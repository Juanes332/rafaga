#!/usr/bin/env bash
# Ráfaga - script de arranque, parada y reinicio para Linux (ADR-05, ADR-17, ADR-25).
# Uso: scripts/rafaga.sh start|stop|reset   (normalmente desde ./start.sh, ./stop.sh, ./reset.sh)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT=rafaga
ENV_FILE="$ROOT/.env"
ENV_EXAMPLE="$ROOT/.env.example"
FILES=(-f compose.yaml)
DEVICE_LABEL="CPU"
TIMEOUT_FIRST=600
TIMEOUT_NEXT=180
DEFAULT_VERSION=1.0.0   # ADR-29: versión fija, nunca "latest"

info() { printf '%s\n' "$*"; }
warn() { printf 'AVISO: %s\n' "$*" >&2; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

compose() { docker compose -p "$PROJECT" "${FILES[@]}" "$@"; }

# ---------- Requisitos ----------
check_docker() {
  command -v docker >/dev/null 2>&1 || die "Docker no está instalado.
  Instala Docker Engine: https://docs.docker.com/engine/install/
  y vuelve a ejecutar ./start.sh"
  local ver
  ver="$(docker compose version --short 2>/dev/null || true)"
  [ -n "$ver" ] || die "Falta el plugin 'docker compose' (versión 2).
  Instálalo: https://docs.docker.com/compose/install/linux/"
  ver="${ver#v}"
  [ "${ver%%.*}" -ge 2 ] 2>/dev/null || die "Se necesita Docker Compose v2 o superior (detectado: $ver).
  Actualiza: https://docs.docker.com/compose/install/linux/"
  local out
  if ! out="$(docker info 2>&1)"; then
    case "$out" in
      *"permission denied"*) die "Tu usuario no tiene permiso para usar Docker.
  Ejecuta: sudo usermod -aG docker \$USER
  cierra la sesión, vuelve a entrar y ejecuta ./start.sh de nuevo." ;;
      *) die "El servicio de Docker no responde.
  Inicia Docker con: sudo systemctl start docker
  y vuelve a ejecutar ./start.sh" ;;
    esac
  fi
}

# ---------- .env ----------
env_get() { # env_get CLAVE
  [ -f "$ENV_FILE" ] || return 0
  grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true
}

env_set() { # env_set CLAVE VALOR  (sin sed: los valores pueden tener caracteres especiales)
  local tmp
  tmp="$(mktemp "$ROOT/.env.XXXXXX")"
  awk -v k="$1" -v v="$2" '
    BEGIN { done = 0 }
    index($0, k "=") == 1 { if (!done) { print k "=" v; done = 1 } ; next }
    { print }
    END { if (!done) print k "=" v }
  ' "$ENV_FILE" >"$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$ENV_FILE"
}

gen_secret() { # gen_secret BYTES -> base64url sin relleno
  local n="$1" s=""
  if command -v openssl >/dev/null 2>&1; then
    s="$(openssl rand -base64 "$n" | tr -d '\n=' | tr '+/' '-_')"
  elif [ -r /dev/urandom ]; then
    s="$(head -c "$n" /dev/urandom | base64 | tr -d '\n=' | tr '+/' '-_')"
  elif command -v python3 >/dev/null 2>&1; then
    s="$(python3 -c "import secrets,sys;print(secrets.token_urlsafe(int(sys.argv[1])),end='')" "$n")"
  fi
  [ -n "$s" ] || die "No se pudo generar un secreto aleatorio (falta openssl, /dev/urandom y python3)."
  printf '%s' "$s"
}

ensure_env() {
  if [ ! -f "$ENV_FILE" ]; then
    [ -f "$ENV_EXAMPLE" ] || die "No se encuentra .env.example en $ROOT."
    ( umask 077; cp "$ENV_EXAMPLE" "$ENV_FILE" )
    info "Archivo .env creado."
  fi
  chmod 600 "$ENV_FILE" 2>/dev/null || true
  [ -n "$(env_get POSTGRES_PASSWORD)" ] || { env_set POSTGRES_PASSWORD "$(gen_secret 32)"; info "Contraseña de base de datos generada (guardada en .env)."; }
  [ -n "$(env_get JWT_SECRET)" ] || { env_set JWT_SECRET "$(gen_secret 64)"; info "Secreto de sesión generado (guardado en .env)."; }
}

# ---------- Imágenes (registro opcional) ----------
registry() { printf '%s' "${RAFAGA_IMAGE_REGISTRY:-$(env_get RAFAGA_IMAGE_REGISTRY)}"; }

# PULLED=1 solo si las imágenes se descargaron; en otro caso se construyen en local.
PULLED=0

# Con RAFAGA_IMAGE_REGISTRY descarga las imágenes ya construidas; si falla, avisa y construye en local.
pull_images() {
  local reg
  PULLED=0
  reg="$(registry)"
  [ -n "$reg" ] || return 0
  local ver="${RAFAGA_VERSION:-$(env_get RAFAGA_VERSION)}"
  ver="${ver:-$DEFAULT_VERSION}"
  info "Descargando imágenes de $reg (versión $ver)..."
  if compose pull api solver web; then
    PULLED=1
  else
    warn "No se pudieron descargar las imágenes de $reg (versión $ver); se construirán en local.
  Comprueba RAFAGA_IMAGE_REGISTRY y RAFAGA_VERSION en .env, tu conexión y tu sesión (docker login)."
  fi
  return 0
}

clear_ports() {
  env_set RAFAGA_WEB_PORT ""
  env_set RAFAGA_API_PORT ""
}

# ---------- GPU (ADR-17) ----------
detect_gpu() {
  if ! command -v nvidia-smi >/dev/null 2>&1 || ! nvidia-smi -L >/dev/null 2>&1; then
    info "GPU NVIDIA no detectada: se usará la CPU."
    return 0
  fi
  info "GPU NVIDIA detectada. Verificando que Docker pueda usarla (puede tardar la primera vez)..."
  local out
  if out="$(docker compose -p "$PROJECT" -f compose.yaml -f compose.gpu.yaml run --rm --no-deps -T solver \
      python -m app.services.device.device_probe 2>&1)"; then
    FILES=(-f compose.yaml -f compose.gpu.yaml)
    local name
    name="$(printf '%s\n' "$out" | grep -o '"gpu_name": *"[^"]*"' | tail -n 1 | sed 's/.*: *"\(.*\)"/\1/' || true)"
    DEVICE_LABEL="GPU: ${name:-NVIDIA}"
    info "$DEVICE_LABEL"
  else
    warn "La GPU NVIDIA no está disponible dentro de Docker; se usará la CPU."
    printf '%s\n' "$out" | tail -n 5 >&2
    warn "Revisa la sección «GPU no detectada» del README (NVIDIA Container Toolkit y driver >= 535)."
  fi
}

# ---------- Arranque ----------
# Devuelve 0 si va bien, 2 si hay un conflicto de puerto, 1 en otro fallo.
up_stack() { # up_stack [--build]
  local log rc=0
  log="$(mktemp)"
  compose up -d "$@" 2>&1 | tee "$log" || rc=$?
  if [ "$rc" -ne 0 ]; then
    if grep -qiE 'port is already allocated|address already in use|ports are not available' "$log"; then
      rm -f "$log"; return 2
    fi
    rm -f "$log"; return 1
  fi
  rm -f "$log"
}

effective_port() { # effective_port SERVICIO PUERTO_INTERNO
  local line
  line="$(compose port "$1" "$2" 2>/dev/null | head -n 1 || true)"
  printf '%s' "${line##*:}"
}

show_failure_help() {
  warn "Algo falló al arrancar. Diagnóstico:"
  compose ps -a >&2 || true
  compose logs --tail 25 >&2 || true
  info "
Qué hacer:
  - Si el error habla de 'build', revisa tu conexión a internet y el espacio en disco.
  - Revisa los registros completos con: docker compose -p rafaga logs
  - Si nada funciona, consulta la sección «Solución de problemas» del README." >&2
}

http_ok() { # http_ok URL
  if command -v curl >/dev/null 2>&1; then
    curl -fsS -o /dev/null --max-time 5 "$1" 2>/dev/null
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O /dev/null -T 5 "$1" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c "import sys,urllib.request;urllib.request.urlopen(sys.argv[1],timeout=5)" "$1" 2>/dev/null
  else
    die "Se necesita curl, wget o python3 para comprobar el estado."
  fi
}

wait_http() { # wait_http URL SEGUNDOS ETIQUETA
  local url="$1" limit="$2" label="$3" start now
  start="$(date +%s)"
  while ! http_ok "$url"; do
    now="$(date +%s)"
    if [ $((now - start)) -ge "$limit" ]; then
      warn "$label no respondió en $limit s ($url)."
      show_failure_help
      exit 1
    fi
    sleep 3
  done
}

open_browser() {
  [ -z "${RAFAGA_NO_BROWSER:-}" ] || return 0
  if command -v xdg-open >/dev/null 2>&1 && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
    nohup xdg-open "$1" >/dev/null 2>&1 &
  else
    info "Abre esta dirección en tu navegador: $1"
  fi
}

cmd_start() {
  check_docker
  local first=0
  [ -f "$ENV_FILE" ] || first=1
  ensure_env
  pull_images
  detect_gpu
  [ -n "$(compose ps -aq 2>/dev/null || true)" ] || first=1

  local flag="--build" attempt=0 rc web api
  if [ "$PULLED" -eq 1 ]; then
    flag=""
    info "Arrancando Ráfaga con las imágenes descargadas..."
  else
    info "Construyendo y arrancando Ráfaga (la primera vez puede tardar varios minutos)..."
  fi
  while :; do
    attempt=$((attempt + 1))
    [ "$attempt" -le 4 ] || { show_failure_help; die "No se pudieron fijar los puertos tras varios intentos. Cierra otros programas y reintenta."; }
    rc=0
    if [ -n "$flag" ]; then up_stack "$flag" || rc=$?; else up_stack || rc=$?; fi
    if [ "$rc" -eq 2 ]; then
      warn "Un puerto guardado está ocupado; se elegirá otro automáticamente."
      clear_ports; continue
    elif [ "$rc" -ne 0 ]; then
      show_failure_help; die "No se pudo arrancar la aplicación."
    fi
    web="$(effective_port web 3000)"; api="$(effective_port api 8000)"
    [ -n "$web" ] && [ -n "$api" ] || { show_failure_help; die "No se pudieron leer los puertos publicados."; }
    if [ "$web" = "$(env_get RAFAGA_WEB_PORT)" ] && [ "$api" = "$(env_get RAFAGA_API_PORT)" ]; then
      break
    fi
    env_set RAFAGA_WEB_PORT "$web"; env_set RAFAGA_API_PORT "$api"
    flag=""   # segunda pasada: recrea api y web con los puertos ya fijados
  done

  local limit="$TIMEOUT_NEXT"; [ "$first" -eq 1 ] && limit="$TIMEOUT_FIRST"
  info "Esperando a que los servicios estén listos..."
  wait_http "http://127.0.0.1:$api/health" "$limit" "La API"
  wait_http "http://127.0.0.1:$web/" "$limit" "La interfaz web"

  local url="http://localhost:$web"
  info ""
  info "Ráfaga está lista en $url"
  info "Dispositivo de cálculo: $DEVICE_LABEL"
  info "Para detenerla: ./stop.sh   |   Para borrar todos los datos: ./reset.sh"
  open_browser "$url"
}

cmd_stop() {
  check_docker
  docker compose -p "$PROJECT" stop
  info "Ráfaga detenida. Tus datos se conservan; ejecuta ./start.sh para volver a usarla."
}

cmd_reset() {
  check_docker
  info "ATENCIÓN: esto borra TODOS los datos de Ráfaga (proyectos, resultados y cuentas)."
  info "Los secretos del archivo .env se conservan."
  printf "Escribe 'borrar' para confirmar: "
  local answer=""
  read -r answer || true
  if [ "$answer" != "borrar" ]; then
    info "Cancelado. No se ha cambiado nada."
    return 0
  fi
  docker compose -p "$PROJECT" down -v --remove-orphans
  if [ -f "$ENV_FILE" ]; then clear_ports; fi
  info "Datos borrados. Ejecuta ./start.sh para empezar de nuevo."
}

# Solo despacha al ejecutarlo; al hacer `source` (pruebas) se cargan las funciones.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    start) cmd_start ;;
    stop) cmd_stop ;;
    reset) cmd_reset ;;
    *) die "Uso: $0 start|stop|reset" ;;
  esac
fi

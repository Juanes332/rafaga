#!/usr/bin/env bash
# Prueba de humo de extremo a extremo contra una pila Ráfaga en marcha (OPS-11).
# Crea cuenta (si hace falta), proyecto con valores SINTÉTICOS, un bloque, un plan2d grueso,
# y comprueba el campo K, k.png y el PDF del informe. Sale con código distinto de 0 si algo falla.
#
# Variables opcionales: RAFAGA_API_PORT (por defecto, el de .env), SMOKE_EMAIL, SMOKE_PASSWORD,
# SMOKE_DX (m, por defecto 2), SMOKE_TIMEOUT (s, por defecto 900), SMOKE_SKIP_PDF=1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { printf 'FALLO: %s\n' "$*" >&2; exit 1; }
ok() { printf '  ok  %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Se necesita '$1' instalado."; }
need curl; need python3

PORT="${RAFAGA_API_PORT:-}"
if [ -z "$PORT" ] && [ -f "$ROOT/.env" ]; then
  PORT="$(grep -E '^RAFAGA_API_PORT=' "$ROOT/.env" | tail -n 1 | cut -d= -f2-)"
fi
[ -n "$PORT" ] || fail "No se conoce el puerto de la API. Ejecuta ./start.sh o define RAFAGA_API_PORT."
BASE="http://127.0.0.1:$PORT"
EMAIL="${SMOKE_EMAIL:-smoke@example.invalid}"
PASSWORD="${SMOKE_PASSWORD:-smoke-test-password-123}"
DX="${SMOKE_DX:-2}"
TIMEOUT="${SMOKE_TIMEOUT:-900}"
TOKEN=""

# api METHOD RUTA [JSON] -> cuerpo en $TMP/body, código HTTP en $CODE
api() {
  local method="$1" path="$2" data="${3:-}" args=()
  args=(-sS -o "$TMP/body" -w '%{http_code}' -X "$method" --max-time 60)
  [ -z "$TOKEN" ] || args+=(-H "Authorization: Bearer $TOKEN")
  [ -z "$data" ] || args+=(-H 'Content-Type: application/json' --data "$data")
  CODE="$(curl "${args[@]}" "$BASE$path")" || fail "No se pudo conectar con $BASE$path"
}
expect() { # expect CODIGO... (el último api debe devolver uno de ellos)
  local c
  for c in "$@"; do [ "$CODE" = "$c" ] && return 0; done
  fail "HTTP $CODE (se esperaba $*): $(head -c 400 "$TMP/body")"
}
jget() { # jget EXPRESIÓN_PYTHON_SOBRE_d  (lee $TMP/body)
  python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print($1)" "$TMP/body"
}

echo "Prueba de humo contra $BASE"

api GET /health; expect 200
[ "$(jget "d.get('status')")" = "ok" ] || fail "/health no está en 'ok': $(cat "$TMP/body")"
ok "API sana"

api GET /api/v1/auth/setup-status; expect 200
if [ "$(jget "str(d['needs_setup']).lower()")" = "true" ]; then
  api POST /api/v1/auth/setup "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"; expect 201
  ok "cuenta inicial creada"
else
  api POST /api/v1/auth/login "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
  [ "$CODE" = 200 ] || fail "Ya existe una cuenta y el login con SMOKE_EMAIL/SMOKE_PASSWORD falló (HTTP $CODE). Define esas variables con una cuenta válida."
  ok "sesión iniciada con la cuenta existente"
fi
TOKEN="$(jget "d['access_token']")"

api POST /api/v1/projects "{\"name\":\"smoke-$(date +%s)\"}"; expect 201
PID="$(jget "d['id']")"
ok "proyecto $PID"

# Ubicación sintética con elevación manual: no hay llamadas a Open-Meteo.
api PUT "/api/v1/projects/$PID/location" '{"lat":10.0,"lon":10.0,"elevation_m":100}'; expect 200
[ "$(jget "d.get('air_density_kg_m3') is not None")" = "True" ] || fail "El proyecto no calculó la densidad del aire."
ok "ubicación sintética con elevación manual"

api PATCH "/api/v1/projects/$PID/wind" '{"source":"manual","manual_direction_deg":270,"manual_u10_ms":5,"terrain_category":"urban"}'; expect 200
ok "viento manual"

api GET "/api/v1/projects/$PID/geometry"; expect 200
VER="$(jget "d['version']")"
BID="$(python3 -c 'import uuid;print(uuid.uuid4())')"
BLOCK="{\"expected_version\":$VER,\"buildings\":[{\"id\":\"$BID\",\"name\":\"Bloque 1\",\"footprint\":[[0,0],[20,0],[20,12],[0,12]],\"holes\":[],\"height_m\":12,\"source\":\"draw\",\"missing_height\":false}]}"
api PUT "/api/v1/projects/$PID/geometry" "$BLOCK"; expect 200
[ "$(jget "len(d['buildings'])")" = "1" ] || fail "La geometría no guardó el bloque."
ok "bloque guardado"

api GET "/api/v1/projects/$PID/alternatives"; expect 200
AID="$(jget "[a['id'] for a in d if a.get('is_base')][0]")"

api POST /api/v1/simulations "{\"alternative_id\":\"$AID\",\"kind\":\"plan2d\",\"directions_deg\":[270],\"dx_m\":$DX,\"device\":\"auto\",\"auto_coarsen\":true}"; expect 202
SID="$(jget "d['id']")"
ok "estudio $SID encolado (dx=$DX m)"

start="$(date +%s)"
status=""
while :; do
  api GET "/api/v1/simulations/$SID"; expect 200
  status="$(jget "d['status']")"
  printf '\r  estado: %-10s progreso: %s   ' "$status" "$(jget "round(d['progress']*100)")%"
  case "$status" in completed) break ;; failed|cancelled|partial) echo; fail "El estudio terminó en '$status': $(jget "[j.get('error') for j in d['jobs']]")" ;; esac
  [ $(( $(date +%s) - start )) -lt "$TIMEOUT" ] || { echo; fail "Tiempo agotado ($TIMEOUT s) esperando el estudio."; }
  sleep 2
done
echo
ok "estudio completado"

RID="$(jget "[j['result_id'] for j in d['jobs'] if j.get('result_id')][0]")"
api GET "/api/v1/results/$RID"; expect 200
[ "$(jget "'K' in d['fields']")" = "True" ] || fail "El resultado no declara el campo K."
[ "$(jget "'k.png' in d['images']")" = "True" ] || fail "El resultado no declara k.png."
ok "metadatos del resultado (K y k.png)"

curl -sS -o "$TMP/K.bin" -D "$TMP/K.hdr" -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/results/$RID/fields/K" >"$TMP/code" || fail "No se pudo descargar K."
[ "$(cat "$TMP/code")" = 200 ] || fail "GET fields/K devolvió HTTP $(cat "$TMP/code")."
[ -s "$TMP/K.bin" ] || fail "El campo K está vacío."
ok "campo K descargado ($(wc -c <"$TMP/K.bin") bytes)"

curl -sS -o "$TMP/k.png" -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/results/$RID/images/k.png" >"$TMP/code" || fail "No se pudo descargar k.png."
[ "$(cat "$TMP/code")" = 200 ] || fail "GET images/k.png devolvió HTTP $(cat "$TMP/code")."
[ "$(head -c 8 "$TMP/k.png" | od -An -tx1 | tr -d ' \n')" = "89504e470d0a1a0a" ] || fail "k.png no es un PNG válido."
ok "k.png válido"

if [ -z "${SMOKE_SKIP_PDF:-}" ]; then
  api POST "/api/v1/projects/$PID/reports" "{\"study_ids\":[\"$SID\"],\"include_comfort\":false}"; expect 202
  REP="$(jget "d['report_id']")"
  start="$(date +%s)"
  while :; do
    api GET "/api/v1/reports/$REP"; expect 200
    rs="$(jget "d['status']")"
    case "$rs" in completed) break ;; failed|cancelled) fail "El informe terminó en '$rs'." ;; esac
    [ $(( $(date +%s) - start )) -lt 300 ] || fail "Tiempo agotado esperando el informe."
    sleep 2
  done
  curl -sS -o "$TMP/r.pdf" -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/reports/$REP/file" >"$TMP/code" || fail "No se pudo descargar el PDF."
  [ "$(cat "$TMP/code")" = 200 ] || fail "GET reports/file devolvió HTTP $(cat "$TMP/code")."
  [ "$(head -c 4 "$TMP/r.pdf")" = "%PDF" ] || fail "El informe no es un PDF válido."
  ok "informe PDF válido"
fi

echo "PRUEBA DE HUMO SUPERADA"

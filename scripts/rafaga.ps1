# Ráfaga - script de arranque, parada y reinicio para Windows PowerShell 5.1+ (ADR-05, ADR-17, ADR-25).
# Uso: scripts\rafaga.ps1 start|stop|reset   (normalmente desde start.bat / stop.bat / reset.bat)
param([Parameter(Position = 0)][string]$Action)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Project = 'rafaga'
$EnvFile = Join-Path $Root '.env'
$EnvExample = Join-Path $Root '.env.example'
$script:Files = @('-f', 'compose.yaml')
$script:DeviceLabel = 'CPU'
$script:LastOut = @()
$TimeoutFirst = 600
$TimeoutNext = 180

function Info($msg) { Write-Host $msg }
function Warn($msg) { Write-Host "AVISO: $msg" -ForegroundColor Yellow }
function Fail($msg) {
    Write-Host "`nERROR: $msg" -ForegroundColor Red
    exit 1
}

# Ejecuta docker sin que los mensajes de stderr se conviertan en errores de PowerShell.
# Guarda la salida en $script:LastOut y devuelve el código de salida. -Live muestra la salida al instante.
function Invoke-Docker([string[]]$DockerArgs, [switch]$Live) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = New-Object System.Collections.ArrayList
        & docker @DockerArgs 2>&1 | ForEach-Object {
            $line = "$_"
            [void]$lines.Add($line)
            if ($Live) { Write-Host $line }
        }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
    $script:LastOut = @($lines)
    return $code
}

function Invoke-Compose([string[]]$ComposeArgs, [switch]$Live, [switch]$NoFiles) {
    $all = @('compose', '-p', $Project)
    if (-not $NoFiles) { $all += $script:Files }
    $all += $ComposeArgs
    return (Invoke-Docker -DockerArgs $all -Live:$Live)
}

# ---------- Requisitos ----------
function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Fail "Docker no está instalado.`n  Instala Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/`n  (activa la opción WSL 2), reinicia el equipo y vuelve a ejecutar start.bat"
    }
    if ((Invoke-Compose @('version', '--short') -NoFiles) -ne 0) {
        Fail "Falta Docker Compose v2.`n  Actualiza Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/"
    }
    $ver = ($script:LastOut -join '').Trim().TrimStart('v')
    $major = 0
    if (-not [int]::TryParse(($ver -split '\.')[0], [ref]$major) -or $major -lt 2) {
        Fail "Se necesita Docker Compose v2 o superior (detectado: $ver). Actualiza Docker Desktop."
    }
    if ((Invoke-Docker @('info')) -ne 0) {
        Fail "Docker no responde.`n  Inicia Docker Desktop, espera a que el icono indique que está en marcha y vuelve a ejecutar start.bat"
    }
}

# ---------- .env ----------
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Read-EnvLines {
    if (Test-Path $EnvFile) { return @([System.IO.File]::ReadAllLines($EnvFile)) }
    return @()
}

function Get-EnvValue([string]$Key) {
    $found = ''
    foreach ($l in (Read-EnvLines)) {
        if ($l.StartsWith("$Key=")) { $found = $l.Substring($Key.Length + 1) }
    }
    return $found
}

function Set-EnvValue([string]$Key, [string]$Value) {
    $out = New-Object System.Collections.ArrayList
    $done = $false
    foreach ($l in (Read-EnvLines)) {
        if ($l.StartsWith("$Key=")) {
            if (-not $done) { [void]$out.Add("$Key=$Value"); $done = $true }
        } else {
            [void]$out.Add($l)
        }
    }
    if (-not $done) { [void]$out.Add("$Key=$Value") }
    [System.IO.File]::WriteAllText($EnvFile, (($out -join "`n") + "`n"), $Utf8NoBom)
}

function New-Secret([int]$Bytes) {
    $buf = New-Object byte[] $Bytes
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($buf) } finally { $rng.Dispose() }
    return ([Convert]::ToBase64String($buf)).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

function Initialize-Env {
    if (-not (Test-Path $EnvFile)) {
        if (-not (Test-Path $EnvExample)) { Fail "No se encuentra .env.example en $Root." }
        Copy-Item $EnvExample $EnvFile
        Info 'Archivo .env creado.'
    }
    if (-not (Get-EnvValue 'POSTGRES_PASSWORD')) {
        Set-EnvValue 'POSTGRES_PASSWORD' (New-Secret 32)
        Info 'Contraseña de base de datos generada (guardada en .env).'
    }
    if (-not (Get-EnvValue 'JWT_SECRET')) {
        Set-EnvValue 'JWT_SECRET' (New-Secret 64)
        Info 'Secreto de sesión generado (guardado en .env).'
    }
}

# ---------- Imágenes (registro opcional) ----------
function Get-Registry {
    if ($env:RAFAGA_IMAGE_REGISTRY) { return $env:RAFAGA_IMAGE_REGISTRY }
    return (Get-EnvValue 'RAFAGA_IMAGE_REGISTRY')
}

# Con RAFAGA_IMAGE_REGISTRY descarga las imágenes ya construidas; si no, se construyen en local.
# Devuelve $true solo si se descargaron las imágenes; si falla, avisa y se construirá en local.
function Get-RemoteImage {
    $reg = Get-Registry
    if (-not $reg) { return $false }
    $ver = $env:RAFAGA_VERSION
    if (-not $ver) { $ver = Get-EnvValue 'RAFAGA_VERSION' }
    if (-not $ver) { $ver = '1.0.0' }  # ADR-29: versión fija, nunca latest
    Info "Descargando imágenes de $reg (versión $ver)..."
    if ((Invoke-Compose @('pull', 'api', 'solver', 'web') -Live) -ne 0) {
        Warn "No se pudieron descargar las imágenes de $reg (versión $ver); se construirán en local.`n  Comprueba RAFAGA_IMAGE_REGISTRY y RAFAGA_VERSION en .env, tu conexión y tu sesión (docker login)."
        return $false
    }
    return $true
}

function Clear-Ports {
    Set-EnvValue 'RAFAGA_WEB_PORT' ''
    Set-EnvValue 'RAFAGA_API_PORT' ''
}

# ---------- GPU (ADR-17) ----------
function Test-DockerWsl2 {
    # Docker Desktop con el motor WSL 2 reporta un kernel "...microsoft-standard-WSL2".
    if ((Invoke-Docker @('info', '--format', '{{.KernelVersion}}')) -ne 0) { return $false }
    return (($script:LastOut -join ' ') -match 'WSL2|microsoft')
}

function Find-Gpu {
    $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    $ok = $false
    if ($smi) {
        $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { & nvidia-smi -L *> $null; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false } finally { $ErrorActionPreference = $prev }
    }
    if (-not $ok) {
        Info 'GPU NVIDIA no detectada: se usará la CPU.'
        return
    }
    if (-not (Test-DockerWsl2)) {
        Warn 'Docker Desktop no usa el motor WSL 2, necesario para la GPU. Activa Settings > General > "Use the WSL 2 based engine". Se usará la CPU.'
        return
    }
    Info 'GPU NVIDIA detectada. Verificando que Docker pueda usarla (puede tardar la primera vez)...'
    $probe = @('compose', '-p', $Project, '-f', 'compose.yaml', '-f', 'compose.gpu.yaml', 'run', '--rm', '--no-deps', '-T', 'solver', 'python', '-m', 'app.services.device.device_probe')
    if ((Invoke-Docker $probe) -eq 0) {
        $script:Files = @('-f', 'compose.yaml', '-f', 'compose.gpu.yaml')
        $name = 'NVIDIA'
        $m = [regex]::Match(($script:LastOut -join "`n"), '"gpu_name":\s*"([^"]*)"')
        if ($m.Success) { $name = $m.Groups[1].Value }
        $script:DeviceLabel = "GPU: $name"
        Info $script:DeviceLabel
    } else {
        Warn 'La GPU NVIDIA no está disponible dentro de Docker; se usará la CPU.'
        $script:LastOut | Select-Object -Last 5 | ForEach-Object { Write-Host $_ }
        Warn 'Revisa la sección «GPU no detectada» del README (driver NVIDIA >= 535, wsl --update y motor WSL 2).'
    }
}

# ---------- Arranque ----------
# Devuelve 0 si va bien, 2 si hay un conflicto de puerto y 1 en otro fallo.
function Start-Stack([string[]]$Extra) {
    $code = Invoke-Compose (@('up', '-d') + $Extra) -Live
    if ($code -eq 0) { return 0 }
    if (($script:LastOut -join "`n") -match '(?i)port is already allocated|address already in use|ports are not available|forbidden by its access permissions') { return 2 }
    return 1
}

function Get-EffectivePort([string]$Service, [string]$InternalPort) {
    if ((Invoke-Compose @('port', $Service, $InternalPort)) -ne 0) { return '' }
    # Stderr is merged into the output: keep only the "host:port" line, not warnings.
    $line = ($script:LastOut | Where-Object { "$_" -match ':\d+\s*$' } | Select-Object -First 1)
    if (-not $line) { return '' }
    return ("$line").Substring(("$line").LastIndexOf(':') + 1).Trim()
}

function Show-FailureHelp {
    Warn 'Algo falló al arrancar. Diagnóstico:'
    [void](Invoke-Compose @('ps', '-a') -Live)
    [void](Invoke-Compose @('logs', '--tail', '25') -Live)
    Info @'

Qué hacer:
  - Si el error habla de 'build', revisa tu conexión a internet y el espacio en disco.
  - Revisa los registros completos con: docker compose -p rafaga logs
  - Si nada funciona, consulta la sección «Solución de problemas» del README.
'@
}

function Test-Http([string]$Url) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return ($r.StatusCode -eq 200)
    } catch { return $false }
}

function Wait-Http([string]$Url, [int]$Seconds, [string]$Label) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while (-not (Test-Http $Url)) {
        if ($sw.Elapsed.TotalSeconds -ge $Seconds) {
            Warn "$Label no respondió en $Seconds s ($Url)."
            Show-FailureHelp
            exit 1
        }
        Start-Sleep -Seconds 3
    }
}

function Invoke-Start {
    Test-Docker
    $first = -not (Test-Path $EnvFile)
    Initialize-Env
    $pulled = Get-RemoteImage
    Find-Gpu
    [void](Invoke-Compose @('ps', '-aq'))
    if (-not (($script:LastOut -join '').Trim())) { $first = $true }

    $extra = @('--build')
    if ($pulled) {
        $extra = @()
        Info 'Arrancando Ráfaga con las imágenes descargadas...'
    } else {
        Info 'Construyendo y arrancando Ráfaga (la primera vez puede tardar varios minutos)...'
    }
    $attempt = 0
    $web = ''; $api = ''
    while ($true) {
        $attempt++
        if ($attempt -gt 4) {
            Show-FailureHelp
            Fail 'No se pudieron fijar los puertos tras varios intentos. Cierra otros programas y reintenta.'
        }
        $rc = Start-Stack $extra
        if ($rc -eq 2) {
            Warn 'Un puerto guardado está ocupado; se elegirá otro automáticamente.'
            Clear-Ports
            continue
        } elseif ($rc -ne 0) {
            Show-FailureHelp
            Fail 'No se pudo arrancar la aplicación.'
        }
        $web = Get-EffectivePort 'web' '3000'
        $api = Get-EffectivePort 'api' '8000'
        if (-not $web -or -not $api) {
            Show-FailureHelp
            Fail 'No se pudieron leer los puertos publicados.'
        }
        if (($web -eq (Get-EnvValue 'RAFAGA_WEB_PORT')) -and ($api -eq (Get-EnvValue 'RAFAGA_API_PORT'))) { break }
        Set-EnvValue 'RAFAGA_WEB_PORT' $web
        Set-EnvValue 'RAFAGA_API_PORT' $api
        $extra = @()   # segunda pasada: recrea api y web con los puertos ya fijados
    }

    $limit = $TimeoutNext
    if ($first) { $limit = $TimeoutFirst }
    Info 'Esperando a que los servicios estén listos...'
    Wait-Http "http://127.0.0.1:$api/health" $limit 'La API'
    Wait-Http "http://127.0.0.1:$web/" $limit 'La interfaz web'

    $url = "http://localhost:$web"
    Info ''
    Info "Ráfaga está lista en $url"
    Info "Dispositivo de cálculo: $($script:DeviceLabel)"
    Info 'Para detenerla: stop.bat   |   Para borrar todos los datos: reset.bat'
    if (-not $env:RAFAGA_NO_BROWSER) { Start-Process $url }
}

function Invoke-Stop {
    Test-Docker
    [void](Invoke-Compose @('stop') -Live -NoFiles)
    Info 'Ráfaga detenida. Tus datos se conservan; ejecuta start.bat para volver a usarla.'
}

function Invoke-Reset {
    Test-Docker
    Info 'ATENCIÓN: esto borra TODOS los datos de Ráfaga (proyectos, resultados y cuentas).'
    Info 'Los secretos del archivo .env se conservan.'
    $answer = Read-Host "Escribe 'borrar' para confirmar"
    if ($answer -cne 'borrar') {
        Info 'Cancelado. No se ha cambiado nada.'
        return
    }
    $code = Invoke-Compose @('down', '-v', '--remove-orphans') -Live -NoFiles
    if ($code -ne 0) { Fail 'No se pudieron borrar los datos.' }
    if (Test-Path $EnvFile) { Clear-Ports }
    Info 'Datos borrados. Ejecuta start.bat para empezar de nuevo.'
}

switch ($Action) {
    'start' { Invoke-Start }
    'stop' { Invoke-Stop }
    'reset' { Invoke-Reset }
    default { Fail 'Uso: rafaga.ps1 start|stop|reset' }
}
exit 0

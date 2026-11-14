# Punto de entrada de Windows: reset
& (Join-Path (Join-Path $PSScriptRoot 'scripts') 'rafaga.ps1') reset
exit $LASTEXITCODE

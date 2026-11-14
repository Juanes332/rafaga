# Punto de entrada de Windows: stop
& (Join-Path (Join-Path $PSScriptRoot 'scripts') 'rafaga.ps1') stop
exit $LASTEXITCODE

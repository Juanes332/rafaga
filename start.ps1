# Punto de entrada de Windows: start
& (Join-Path (Join-Path $PSScriptRoot 'scripts') 'rafaga.ps1') start
exit $LASTEXITCODE

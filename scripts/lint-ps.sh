#!/usr/bin/env bash
# Lint the Windows scripts (BL-04): parse each with the PowerShell parser and run
# PSScriptAnalyzer, failing on Error severity. Runs in a pinned PowerShell image.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${PS_LINT_IMAGE:-mcr.microsoft.com/powershell:7.4-ubuntu-22.04}"

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required." >&2; exit 1; }

docker run --rm -v "$ROOT:/work:ro" -w /work -e HOME=/tmp "$IMAGE" pwsh -NoLogo -NoProfile -Command '
$ErrorActionPreference = "Stop"
$files = @("start.ps1","stop.ps1","reset.ps1","scripts/rafaga.ps1")
$failed = $false
foreach ($f in $files) {
  $tokens = $null; $errs = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $f).Path, [ref]$tokens, [ref]$errs)
  if ($errs.Count -gt 0) { $failed = $true; $errs | ForEach-Object { Write-Host "PARSE ERROR $f : $($_.Message) line $($_.Extent.StartLineNumber)" } }
  else { Write-Host "parse ok  $f" }
}
Set-PSRepository PSGallery -InstallationPolicy Trusted
Install-Module PSScriptAnalyzer -RequiredVersion 1.22.0 -Scope CurrentUser -Force | Out-Null
foreach ($f in $files) {
  $r = Invoke-ScriptAnalyzer -Path $f -Severity Error
  if ($r) { $failed = $true; $r | ForEach-Object { Write-Host "ANALYZER ERROR $f : $($_.RuleName) $($_.Message) line $($_.Line)" } }
  else { Write-Host "analyzer ok (no Error severity)  $f" }
}
if ($failed) { exit 1 }
'

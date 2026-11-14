@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset.ps1"
if errorlevel 1 (
  echo.
  echo Ocurrio un error. Revisa los mensajes anteriores.
  if not defined RAFAGA_NO_PAUSE pause
  exit /b 1
)
if not defined RAFAGA_NO_PAUSE pause

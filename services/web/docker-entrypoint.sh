#!/bin/sh
# Writes the runtime API discovery file (ADR-05) and hands PID 1 to serve.
set -eu

port="${RAFAGA_API_PORT:-0}"
case "$port" in
  ''|*[!0-9]*) port=0 ;;
esac

base="${RAFAGA_API_BASE_URL:-}"
if [ -n "$base" ]; then
  base_json="\"$base\""
else
  base_json="null"
fi

printf '{"apiPort": %s, "apiBaseUrl": %s}\n' "$port" "$base_json" > /app/dist/config.json

exec serve -s /app/dist -l tcp://0.0.0.0:3000

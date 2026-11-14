#!/usr/bin/env bash
# Scripted test (BL-05): an unreachable registry must warn and fall back to a local build.
# Uses a fake `docker` on PATH; no daemon, network or compose stack is touched.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/bin" "$WORK/root/scripts"
cp "$HERE/../rafaga.sh" "$WORK/root/scripts/rafaga.sh"
touch "$WORK/root/.env.example"

cat >"$WORK/bin/docker" <<'SHIM'
#!/usr/bin/env bash
# Fake docker: `compose ... pull` fails like an unreachable registry.
case " $* " in
  *" pull "*) echo "Error: dial tcp: lookup registry.invalid: no such host" >&2; exit 1 ;;
esac
exit 0
SHIM
chmod +x "$WORK/bin/docker"

fails=0
check() { if ! eval "$2"; then printf 'FAIL: %s\n' "$1" >&2; fails=$((fails + 1)); else printf 'ok   %s\n' "$1"; fi; }

run_pull() { # run_pull REGISTRY -> prints "rc PULLED" and stderr to $WORK/err
  (
    export PATH="$WORK/bin:$PATH" RAFAGA_IMAGE_REGISTRY="$1"
    # shellcheck disable=SC1091
    source "$WORK/root/scripts/rafaga.sh"
    rc=0; pull_images 2>"$WORK/err" >/dev/null || rc=$?
    echo "$rc ${PULLED:-unset}"
  )
}

out="$(run_pull registry.invalid/rafaga)"
check "unreachable registry does not abort (rc 0)" '[ "${out%% *}" = 0 ]'
check "unreachable registry marks images as not pulled" '[ "${out##* }" = 0 ]'
check "unreachable registry warns" 'grep -q "AVISO" "$WORK/err"'

out="$(run_pull "")"
check "empty registry means local build (not pulled)" '[ "${out##* }" = 0 ]'

[ "$fails" -eq 0 ] || exit 1
echo "all pull-fallback checks passed"

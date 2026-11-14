# Windows manual checklist (BL-04)

`scripts/lint-ps.sh` only proves the PowerShell scripts parse and have no Error-severity
analyzer findings. The steps below need a real Windows machine and are run by hand before a release.

Record the date, Windows build, Docker Desktop version and GPU for each pass.

## 1. Prerequisites
- [ ] Docker Desktop is installed with the WSL2 backend enabled (Settings > General > "Use the WSL 2 based engine").
- [ ] `docker compose version` reports v2 or newer in PowerShell.
- [ ] Optional GPU: NVIDIA driver >= 535 installed on Windows (not inside WSL).

## 2. GPU probe
- [ ] `nvidia-smi -L` lists the GPU in PowerShell.
- [ ] `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` prints the GPU (skip on CPU-only machines).
- [ ] `start.bat` prints `GPU: <name>` on a GPU machine, or the CPU notice otherwise, and never aborts for lack of a GPU.

## 3. Start
- [ ] Double-click `start.bat` (or run `./start.ps1`) on a clean checkout: `.env` is created, secrets are generated, images build.
- [ ] The browser opens on `http://localhost:<port>` and the port is not hardcoded (a different one is picked if busy).
- [ ] With `RAFAGA_IMAGE_REGISTRY` set to an unreachable host, the script warns and builds locally instead of failing.

## 4. First login
- [ ] The first-use screen asks to create the initial account; after creating it the login works.
- [ ] `compute badge` shows the device (GPU or CPU) and the solver is reported online.

## 5. Stop keeps data
- [ ] Create a project, run `stop.bat`, run `start.bat` again: the account and the project are still there.

## 6. Reset asks "borrar"
- [ ] `reset.bat` prints the warning and waits for input.
- [ ] Typing anything other than `borrar` cancels and changes nothing.
- [ ] Typing `borrar` deletes the volumes; the next `start.bat` shows the first-use screen and keeps the `.env` secrets.

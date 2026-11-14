# scripts

- `a11y.mjs` — axe-core in a real browser on every screen, both themes.
- `measure-particle-fps.mjs` — particle animation frame rate in headed, hardware-accelerated Chromium at 1920x1080; writes `perf/particle-fps.json`.

## measure-particle-fps.mjs

Logs in through the UI, opens a completed 2D result, then samples `requestAnimationFrame`
for `SECONDS` (default 20, after `WARMUP_SECONDS`, default 5) at each CPU throttle rate (`THROTTLE`, default `1`, via CDP
`Emulation.setCPUThrottlingRate`). Prints mean fps, p5 fps (5th-percentile frame rate) and long tasks.
Exits 3 if the particles are not running (static fallback) and 4 on a software renderer (SwiftShader/llvmpipe
does not count). Writes `{mean_fps, p5_fps, gpu_renderer, particles, ...}` to `perf/particle-fps.json` (`OUT`).
Acceptance (BL-08): mean >= 50 fps, p5 >= 30 fps, hardware renderer.

```sh
BASE=http://localhost:<web-port> EMAIL=... PASSWORD=... \
RESULT_PATH=/projects/<projectId>/results/<resultId> node scripts/measure-particle-fps.mjs
```

- `GL_ARGS` selects the GL backend. The default (`--use-gl=angle --use-angle=gl-egl` plus GPU raster) uses the real GPU.
  Software GL (`--use-angle=swiftshader --enable-unsafe-swiftshader`) measures the CPU emulating a GPU:
  a useful stress test, but noisy when the machine is loaded.
- `API_PORT=<port>` lets a local `vite`/`vite preview` server talk to an already running API
  (rewrites `/config.json` and relays API calls with CORS headers added).

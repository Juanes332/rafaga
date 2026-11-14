// Particle animation frame rate in a real, headed Chromium with hardware acceleration at 1080p (BL-08).
// Samples requestAnimationFrame for SECONDS (default 20) after WARMUP_SECONDS (default 5) and writes
// perf/particle-fps.json = {mean_fps, p5_fps, gpu_renderer, particles, ...}. Exits 4 on a software renderer.
// Usage: BASE=http://localhost:<web-port> EMAIL=... PASSWORD=... RESULT_PATH=/projects/<id>/results/<id> \
//   [API_PORT=...] [SECONDS=20] [WARMUP_SECONDS=5] [THROTTLE=1] [OUT=perf/particle-fps.json] \
//   [GL_ARGS="..."] [CHROME_PATH=...] [ALLOW_SOFTWARE=1 (stress runs only: never counts for BL-08)] \
//   node scripts/measure-particle-fps.mjs
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { chromium } from "playwright";

const BASE = process.env.BASE ?? "http://localhost:32779";
const EMAIL = process.env.EMAIL;
const PASSWORD = process.env.PASSWORD;
const RESULT_PATH = process.env.RESULT_PATH;
const SECONDS = Number(process.env.SECONDS ?? 20);
const WARMUP_MS = Number(process.env.WARMUP_SECONDS ?? 5) * 1000;
const RATES = (process.env.THROTTLE ?? "1").split(",").map(Number);
const OUT = resolve(process.env.OUT ?? "perf/particle-fps.json");
const SOFTWARE = /swiftshader|llvmpipe|software/i;
// Hardware acceleration: real GPU through ANGLE/GL, GPU raster and no blocklist (headed, never headless).
const GL_ARGS = (
  process.env.GL_ARGS ?? "--use-gl=angle --use-angle=gl-egl --ignore-gpu-blocklist --enable-gpu-rasterization --enable-zero-copy"
)
  .split(" ")
  .filter(Boolean);
if (!EMAIL || !PASSWORD || !RESULT_PATH) {
  console.error("EMAIL, PASSWORD and RESULT_PATH are required");
  process.exit(2);
}

// Runs in the page: samples rAF deltas and PerformanceObserver long tasks for `ms`.
const sample = (ms) =>
  new Promise((resolve) => {
    const deltas = [];
    const longTasks = [];
    const po = new PerformanceObserver((l) => l.getEntries().forEach((e) => longTasks.push(e.duration)));
    po.observe({ entryTypes: ["longtask"] });
    let last = performance.now();
    const end = last + ms;
    const tick = (t) => {
      deltas.push(t - last);
      last = t;
      if (t < end) requestAnimationFrame(tick);
      else {
        po.disconnect();
        resolve({ deltas, longTasks });
      }
    };
    requestAnimationFrame(tick);
  });

export function summarize({ deltas, longTasks }, seconds) {
  const fps = deltas.slice(1).map((d) => 1000 / d).sort((a, b) => a - b);
  const mean = deltas.length / (deltas.reduce((a, b) => a + b, 0) / 1000);
  const p5 = fps[Math.floor(fps.length * 0.05)] ?? 0;
  return { frames: deltas.length, meanFps: +mean.toFixed(1), p5Fps: +p5.toFixed(1), longTasks: longTasks.length, longTaskMs: +longTasks.reduce((a, b) => a + b, 0).toFixed(0), seconds };
}

const browser = await chromium.launch({ headless: false, executablePath: process.env.CHROME_PATH || undefined, args: GL_ARGS });
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, reducedMotion: "no-preference" });
const page = await ctx.newPage();
// Dev/preview servers ship apiPort 8000 and the API only allows the stack's own web origin in CORS:
// API_PORT repoints /config.json and relays API calls with permissive CORS headers.
if (process.env.API_PORT) {
  const cors = { "access-control-allow-origin": BASE, "access-control-allow-headers": "*", "access-control-allow-methods": "*" };
  await page.route("**/config.json", (r) => r.fulfill({ json: { apiPort: Number(process.env.API_PORT), apiBaseUrl: null } }));
  await page.route(`**:${process.env.API_PORT}/**`, async (r) => {
    if (r.request().method() === "OPTIONS") return r.fulfill({ status: 204, headers: cors });
    const res = await r.fetch();
    await r.fulfill({ response: res, headers: { ...res.headers(), ...cors } });
  });
}
await page.goto(`${BASE}/login`);
await page.getByLabel("Correo").fill(EMAIL);
await page.getByLabel("Contraseña").fill(PASSWORD);
await page.getByRole("button", { name: "Iniciar sesión" }).click();
await page.waitForURL(/\/projects/);
await page.evaluate((to) => {
  window.history.pushState({}, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
}, RESULT_PATH);
// The particle canvas is the aria-hidden canvas inside the flow plan; wait for it to be sized.
await page.waitForFunction(() => [...document.querySelectorAll("canvas[aria-hidden]")].some((c) => c.width > 400), null, { timeout: 60000 });
await page.waitForTimeout(WARMUP_MS);
// Particle mode = one aria-hidden canvas owns a WebGL2 context (static streamlines use SVG).
const running = await page.evaluate(() => [...document.querySelectorAll("canvas[aria-hidden]")].some((c) => c.getContext("webgl2")));
if (!running) {
  console.error("particles are not running (static fallback): WebGL2 unavailable or reduced motion");
  await browser.close();
  process.exit(3);
}
const canvasPx = await page.evaluate(() => [...document.querySelectorAll("canvas[aria-hidden]")].map((c) => `${c.width}x${c.height}`));
console.log(`canvases: ${canvasPx.join(", ")}`);
const gl = await page.evaluate(() => {
  const c = document.createElement("canvas").getContext("webgl2");
  const e = c?.getExtension("WEBGL_debug_renderer_info");
  return e ? c.getParameter(e.UNMASKED_RENDERER_WEBGL) : "unknown";
});
console.log(`renderer: ${gl}`);
const particles = await page.evaluate(() => {
  const c = [...document.querySelectorAll("canvas[aria-hidden]")].find((el) => el.dataset.particles);
  return c ? Number(c.dataset.particles) : null;
});
if (SOFTWARE.test(gl) && !process.env.ALLOW_SOFTWARE) {
  console.error(`software renderer (${gl}) does not count: run on a machine with a real GPU`);
  await browser.close();
  process.exit(4);
}
const cdp = await ctx.newCDPSession(page);
const runs = [];
for (const rate of RATES) {
  await cdp.send("Emulation.setCPUThrottlingRate", { rate });
  await page.waitForTimeout(1500);
  const out = summarize(await page.evaluate(sample, SECONDS * 1000), SECONDS);
  console.log(`cpu x${rate}: ${JSON.stringify(out)}`);
  runs.push({ cpu_throttle: rate, ...out });
}
const first = runs[0];
const finalParticles = await page.evaluate(() => Number([...document.querySelectorAll("canvas[aria-hidden]")].find((el) => el.dataset.particles)?.dataset.particles ?? 0));
const result = {
  mean_fps: first.meanFps,
  p5_fps: first.p5Fps,
  gpu_renderer: gl,
  particles: finalParticles || particles,
  particles_at_start: particles,
  seconds: SECONDS,
  warmup_seconds: WARMUP_MS / 1000,
  viewport: "1920x1080",
  headed: true,
  long_tasks: first.longTasks,
  measured_at: new Date().toISOString(),
  runs,
};
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`);
console.log(`wrote ${OUT}`);
await browser.close();

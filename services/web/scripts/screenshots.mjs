// Visual self-review: captures key screens from `pnpm dev:mock` in light and dark.
// Usage: BASE=http://localhost:5199 node scripts/screenshots.mjs [outDir] [filter]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.env.BASE ?? "http://localhost:5199";
const OUT = process.argv[2] ?? "screenshots";
const FILTER = process.argv[3] ?? "";
const P1 = "00000000-0000-4000-8000-0000000000p1";
const P2 = "00000000-0000-4000-8000-0000000000p2";

const SHOTS = [
  { name: "01-login", path: "/login", auth: false },
  { name: "03-projects", path: "/projects" },
  { name: "05-location-empty", path: `/projects/${P2}/location` },
  { name: "05-location-set", path: `/projects/${P1}/location` },
  { name: "06-geometry", path: `/projects/${P1}/geometry` },
  { name: "10-wind", path: `/projects/${P1}/wind` },
  { name: "11-alternatives", path: `/projects/${P1}/alternatives` },
  { name: "12-simulate", path: `/projects/${P1}/simulate` },
  { name: "14-results", path: `/projects/${P1}/results/00000000-0000-4000-8000-0000000000r1`, wait: 2500 },
  { name: "18-compare", path: `/projects/${P1}/compare?a=00000000-0000-4000-8000-0000000000r1&b=00000000-0000-4000-8000-0000000000r2`, wait: 2000 },
  { name: "20-reports", path: `/projects/${P1}/reports` },
  { name: "21-settings", path: "/settings" },
  { name: "22-users", path: "/users" },
  { name: "23-templates", path: "/templates" },
];

async function login(page) {
  await page.goto(`${BASE}/login`);
  await page.getByLabel("Correo").fill("ana@estudio.co");
  await page.getByLabel("Contraseña").fill("contrasena-segura");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await page.waitForURL(/\/projects$/);
}

async function run(theme, viewport, suffix) {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const context = await browser.newContext({ viewport, colorScheme: theme, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on("pageerror", (e) => console.error(`[${theme}] pageerror:`, e.message));
  await login(page);
  for (const shot of SHOTS.filter((s) => s.name.includes(FILTER))) {
    if (shot.auth === false) {
      const anon = await browser.newContext({ viewport, colorScheme: theme });
      const p = await anon.newPage();
      await p.goto(`${BASE}${shot.path}`);
      await p.waitForTimeout(800);
      await p.screenshot({ path: `${OUT}/${shot.name}-${theme}${suffix}.png` });
      await anon.close();
      continue;
    }
    // Client-side navigation keeps the in-page mock state and the session.
    await page.evaluate((to) => {
      window.history.pushState({}, "", to);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }, shot.path);
    await page.waitForTimeout(shot.wait ?? 1200);
    await page.screenshot({ path: `${OUT}/${shot.name}-${theme}${suffix}.png` });
  }
  await browser.close();
}

mkdirSync(OUT, { recursive: true });
for (const theme of ["light", "dark"]) await run(theme, { width: 1440, height: 900 }, "");
if (!FILTER || FILTER === "mobile") await run("light", { width: 390, height: 844 }, "-mobile");
console.log("screenshots in", OUT);

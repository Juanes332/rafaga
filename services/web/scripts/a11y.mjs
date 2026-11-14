// axe-core in a real browser (colour contrast included) on every screen, both themes.
// Usage: BASE=http://localhost:5199 CHROME_PATH=… node scripts/a11y.mjs
import { chromium } from "playwright";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const AXE = require.resolve("axe-core/axe.min.js");
const BASE = process.env.BASE ?? "http://localhost:5199";
const P1 = "00000000-0000-4000-8000-0000000000p1";
const P2 = "00000000-0000-4000-8000-0000000000p2";
const R = (n) => `00000000-0000-4000-8000-0000000000r${n}`;
const PATHS = [
  "/projects",
  `/projects/${P2}/location`,
  `/projects/${P1}/location`,
  `/projects/${P1}/geometry`,
  `/projects/${P1}/wind`,
  `/projects/${P1}/alternatives`,
  `/projects/${P1}/simulate`,
  `/projects/${P1}/results/${R(1)}`,
  `/projects/${P1}/compare?a=${R(1)}&b=${R(2)}`,
  `/projects/${P1}/reports`,
  "/settings",
  "/users",
  "/templates",
];

async function audit(page, label) {
  await page.addScriptTag({ path: AXE });
  const res = await page.evaluate(async () => {
    // eslint-disable-next-line no-undef
    const r = await axe.run(document, { resultTypes: ["violations"] });
    return r.violations.filter((v) => ["serious", "critical"].includes(v.impact)).map((v) => ({ id: v.id, n: v.nodes.length, t: v.nodes.slice(0, 3).map((x) => x.target.join(" ")) }));
  });
  console.log(res.length ? `FAIL ${label} ${JSON.stringify(res)}` : `ok   ${label}`);
  return res.length;
}

let failures = 0;
for (const theme of ["light", "dark"]) {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await (await browser.newContext({ colorScheme: theme, viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto(`${BASE}/login`);
  await page.waitForTimeout(600);
  failures += await audit(page, `${theme} /login`);
  await page.getByLabel("Correo").fill("ana@estudio.co");
  await page.getByLabel("Contraseña").fill("contrasena-segura");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await page.waitForURL(/\/projects$/);
  for (const p of PATHS) {
    await page.evaluate((to) => {
      window.history.pushState({}, "", to);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }, p);
    await page.waitForTimeout(1500);
    failures += await audit(page, `${theme} ${p}`);
  }
  await browser.close();
}
console.log(failures ? `${failures} screens with serious/critical violations` : "0 serious/critical violations");
process.exit(failures ? 1 : 0);

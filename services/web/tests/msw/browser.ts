import { http, HttpResponse } from "msw";
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

/** Browser worker for `pnpm dev:mock`: the whole API from fixtures, plus /config.json. */
export async function startMockWorker(): Promise<void> {
  const config = http.get("/config.json", () => HttpResponse.json({ apiPort: 8000, apiBaseUrl: "http://localhost:8000" }));
  const worker = setupWorker(config, ...handlers);
  await worker.start({ onUnhandledRequest: "bypass", quiet: true });
}

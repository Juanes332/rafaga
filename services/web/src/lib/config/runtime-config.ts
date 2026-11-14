/** Runtime API discovery (ADR-05): the bundle carries no URL, /config.json does. */
export interface RuntimeConfig {
  apiPort: number | null;
  apiBaseUrl: string | null;
}

interface LocationLike {
  protocol: string;
  hostname: string;
}

type FetchFn = (input: string, init: RequestInit) => Promise<Response>;

function isPort(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0 && value < 65536;
}

/** Validate the raw JSON; null means "service not found". */
export function parseRuntimeConfig(raw: unknown): RuntimeConfig | null {
  if (typeof raw !== "object" || raw === null) return null;
  const { apiPort, apiBaseUrl } = raw as Record<string, unknown>;
  const override = typeof apiBaseUrl === "string" && apiBaseUrl.length > 0 ? apiBaseUrl : null;
  if (override) return { apiPort: isPort(apiPort) ? apiPort : null, apiBaseUrl: override };
  return isPort(apiPort) ? { apiPort, apiBaseUrl: null } : null;
}

/** API base including the /api/v1 prefix. */
export function buildApiBase(config: RuntimeConfig, loc: LocationLike): string {
  if (config.apiBaseUrl) return `${config.apiBaseUrl.replace(/\/+$/, "")}/api/v1`;
  return `${loc.protocol}//${loc.hostname}:${config.apiPort}/api/v1`;
}

/** Fetch and resolve the API base; null when the config is missing or invalid. */
export async function loadRuntimeConfig(fetchFn: FetchFn, loc: LocationLike): Promise<string | null> {
  try {
    const response = await fetchFn("/config.json", { cache: "no-store" });
    if (!response.ok) return null;
    const config = parseRuntimeConfig(await response.json());
    return config ? buildApiBase(config, loc) : null;
  } catch {
    return null;
  }
}

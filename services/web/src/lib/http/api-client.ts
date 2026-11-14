import { ApiError } from "./api-error";

type QueryValue = string | number | boolean | null | undefined;
type Query = Record<string, QueryValue>;

interface ClientConfig {
  baseUrl: string;
  getToken: () => string | null;
  onUnauthorized: () => void;
}

interface RequestOptions {
  query?: Query;
  signal?: AbortSignal;
}

export interface BinaryResponse {
  data: ArrayBuffer;
  headers: Headers;
}

const config: ClientConfig = { baseUrl: "", getToken: () => null, onUnauthorized: () => undefined };

/** Wire base URL (from /config.json) and auth hooks once at bootstrap. */
export function configureApiClient(next: Partial<ClientConfig>): void {
  Object.assign(config, next);
}

export function getApiBase(): string {
  return config.baseUrl;
}

function buildUrl(path: string, query?: Query): string {
  const url = `${config.baseUrl}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== null) params.append(k, String(v));
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

/** Auth header for callers that fetch outside apiClient (MapLibre tiles). */
export function authHeaders(): Record<string, string> {
  const token = config.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function toApiError(response: Response, hadToken: boolean): Promise<ApiError> {
  const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  const retry = Number(response.headers.get("Retry-After"));
  // A 401 on login is bad credentials, not an expired session.
  if (response.status === 401 && hadToken) config.onUnauthorized();
  return new ApiError(
    response.status,
    typeof body.code === "string" ? body.code : `http_${response.status}`,
    typeof body.message === "string" ? body.message : response.statusText,
    (body.details as Record<string, unknown>) ?? {},
    Number.isFinite(retry) && retry > 0 ? retry : null,
  );
}

async function send(method: string, path: string, body?: unknown, opts: RequestOptions = {}): Promise<Response> {
  const isForm = body instanceof FormData;
  const headers: Record<string, string> = { ...authHeaders() };
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  let response: Response;
  try {
    response = await fetch(buildUrl(path, opts.query), {
      method,
      headers,
      signal: opts.signal,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "network_error", "network unreachable");
  }
  if (!response.ok) throw await toApiError(response, "Authorization" in headers);
  return response;
}

async function json<T>(method: string, path: string, body?: unknown, opts?: RequestOptions): Promise<T> {
  const response = await send(method, path, body, opts);
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

/** Typed transport for the api/ layer. Never used by components directly. */
export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) => json<T>("GET", path, undefined, opts),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) => json<T>("POST", path, body ?? {}, opts),
  put: <T>(path: string, body: unknown) => json<T>("PUT", path, body),
  patch: <T>(path: string, body: unknown) => json<T>("PATCH", path, body),
  delete: <T = void>(path: string) => json<T>("DELETE", path),
  upload: <T>(path: string, form: FormData) => json<T>("POST", path, form),
  binary: async (path: string, opts?: RequestOptions): Promise<BinaryResponse> => {
    const response = await send("GET", path, undefined, opts);
    return { data: await response.arrayBuffer(), headers: response.headers };
  },
  blob: async (path: string, opts?: RequestOptions): Promise<Blob> => (await send("GET", path, undefined, opts)).blob(),
};

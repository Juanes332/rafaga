/** Normalised API failure: ErrorBody code plus transport facts. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly retryAfter: number | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/** True when the error carries the given ErrorBody code. */
export function hasCode(error: unknown, code: string): boolean {
  return isApiError(error) && error.code === code;
}

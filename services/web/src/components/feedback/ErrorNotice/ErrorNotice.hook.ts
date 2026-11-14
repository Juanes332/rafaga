import { errorMessage } from "@/lib/http/error-copy";
import type { ErrorNoticeProps } from "./ErrorNotice.types";

/** Resolve the copy once: explicit message wins over the mapped error code. */
export function useErrorNotice({ error, message }: Pick<ErrorNoticeProps, "error" | "message">): string {
  return message ?? errorMessage(error);
}

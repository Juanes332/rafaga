export interface ErrorNoticeProps {
  /** An ApiError (mapped to es-CO copy) or ready-made copy. */
  error?: unknown;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

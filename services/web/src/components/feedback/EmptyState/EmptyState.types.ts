import type { ReactNode } from "react";

export interface EmptyStateProps {
  title: string;
  lead?: string;
  /** One primary action (and at most one secondary). */
  children?: ReactNode;
  className?: string;
}

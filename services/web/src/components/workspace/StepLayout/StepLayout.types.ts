import type { ReactNode } from "react";

export interface StepLayoutProps {
  /** Step title, read by screen readers and shown above the inspector. */
  title: string;
  canvas: ReactNode;
  inspector?: ReactNode;
  /** Optional bar above the canvas (layer toggles, tools). */
  toolbar?: ReactNode;
  /** Optional strip under canvas + inspector (the FR-48 disclaimer on result views). */
  footer?: ReactNode;
}

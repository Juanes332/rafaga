import { cn } from "@/lib/utils";
import type { EmptyStateProps } from "./EmptyState.types";
import styles from "./EmptyState.module.css";

/** An invitation to act: one sentence and an action, no illustration. */
export function EmptyState({ title, lead, children, className }: EmptyStateProps) {
  return (
    <section className={cn(styles.root, className)}>
      <h2 className={styles.title}>{title}</h2>
      {lead ? <p className={styles.lead}>{lead}</p> : null}
      {children ? <div className={styles.actions}>{children}</div> : null}
    </section>
  );
}

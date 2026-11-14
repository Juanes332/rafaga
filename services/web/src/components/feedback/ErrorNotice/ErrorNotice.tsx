import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useErrorNotice } from "./ErrorNotice.hook";
import type { ErrorNoticeProps } from "./ErrorNotice.types";
import styles from "./ErrorNotice.module.css";

/** Cause + fix, with an optional recovery action. */
export function ErrorNotice({ error, message, actionLabel, onAction, className }: ErrorNoticeProps) {
  const text = useErrorNotice({ error, message });
  return (
    <div role="alert" className={cn(styles.root, className)}>
      <p className={styles.text}>{text}</p>
      {actionLabel && onAction ? (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

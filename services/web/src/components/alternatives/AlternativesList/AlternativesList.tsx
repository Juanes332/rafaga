import { MoreHorizontal, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { AlternativeNameDialog } from "@/components/alternatives/AlternativeNameDialog/AlternativeNameDialog";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { DeleteAlternativeDialog } from "./DeleteAlternativeDialog";
import { useAlternativesList } from "./AlternativesList.hook";
import type { AlternativesListProps } from "./AlternativesList.types";
import styles from "./AlternativesList.module.css";

/** Alternatives of the project; the base is marked and cannot be edited or deleted. */
export function AlternativesList(props: AlternativesListProps) {
  const { t } = useTranslation();
  const l = useAlternativesList(props);
  return (
    <section className={styles.root} aria-labelledby="alternatives-title">
      <div className={styles.header}>
        <h2 id="alternatives-title" className={styles.title}>
          {t("alternatives:list.title")}
        </h2>
        {!props.readOnly ? (
          <Button size="sm" variant="secondary" onClick={() => l.openCreate(true)}>
            <Plus aria-hidden />
            {t("alternatives:list.create")}
          </Button>
        ) : null}
      </div>
      <ul className={styles.list}>
        {props.alternatives.map((a) => (
          <li key={a.id} className={cn(styles.row, a.id === props.selectedId && styles.selected)}>
            <button type="button" className={styles.select} aria-pressed={a.id === props.selectedId} onClick={() => props.onSelect(a.id)}>
              <span className={styles.name}>{a.name}</span>
              <span className={styles.meta}>
                {a.is_base ? t("alternatives:list.base") : t("alternatives:list.elements", { count: a.element_count ?? 0 })}
              </span>
            </button>
            {!a.is_base && !props.readOnly ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label={t("alternatives:list.actions", { name: a.name })}>
                    <MoreHorizontal aria-hidden />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={() => l.setRenaming(a)}>{t("alternatives:list.rename")}</DropdownMenuItem>
                  <DropdownMenuItem destructive onSelect={() => l.setDeleting(a)}>
                    {t("alternatives:list.delete")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : null}
          </li>
        ))}
      </ul>
      <AlternativeNameDialog
        open={l.creating}
        mode="create"
        sources={props.alternatives}
        pending={l.create.isPending}
        error={l.create.error}
        onOpenChange={l.openCreate}
        onSubmit={l.onCreate}
      />
      <AlternativeNameDialog
        open={l.renaming !== null}
        mode="rename"
        initialName={l.renaming?.name}
        pending={l.update.isPending}
        error={l.update.error}
        onOpenChange={(o) => !o && l.setRenaming(null)}
        onSubmit={(name) => l.onRename(name)}
      />
      <DeleteAlternativeDialog name={l.deleting?.name ?? null} onCancel={() => l.setDeleting(null)} onConfirm={l.onDelete} />
    </section>
  );
}

import { useTranslation } from "react-i18next";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface BaseChangeDialogProps {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

/** BR-09: changing base buildings while alternatives exist needs an explicit yes. */
export function BaseChangeDialog({ open, onCancel, onConfirm }: BaseChangeDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={open} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("geometry:baseChange.title")}</AlertDialogTitle>
          <AlertDialogDescription>{t("geometry:baseChange.body")}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("common:cancel")}</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>{t("geometry:baseChange.confirm")}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

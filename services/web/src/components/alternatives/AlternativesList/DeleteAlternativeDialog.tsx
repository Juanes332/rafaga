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

interface DeleteAlternativeDialogProps {
  name: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

/** Confirmation naming the alternative. */
export function DeleteAlternativeDialog({ name, onCancel, onConfirm }: DeleteAlternativeDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={name !== null} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("alternatives:deleteDialog.title", { name })}</AlertDialogTitle>
          <AlertDialogDescription>{t("alternatives:deleteDialog.body")}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("common:cancel")}</AlertDialogCancel>
          <AlertDialogAction destructive onClick={onConfirm}>
            {t("alternatives:deleteDialog.submit")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

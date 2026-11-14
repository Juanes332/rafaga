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

interface DeleteProjectDialogProps {
  name: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

/** Confirmation that names the project being deleted. */
export function DeleteProjectDialog({ name, onCancel, onConfirm }: DeleteProjectDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={name !== null} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("projects:deleteDialog.title", { name })}</AlertDialogTitle>
          <AlertDialogDescription>{t("projects:deleteDialog.body")}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("common:cancel")}</AlertDialogCancel>
          <AlertDialogAction destructive onClick={onConfirm}>
            {t("projects:deleteDialog.submit")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

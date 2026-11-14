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

interface DeleteUserDialogProps {
  email: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

/** Confirmation naming the account being deleted. */
export function DeleteUserDialog({ email, onCancel, onConfirm }: DeleteUserDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={email !== null} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("users:delete.title", { email })}</AlertDialogTitle>
          <AlertDialogDescription>{t("users:delete.body")}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("common:cancel")}</AlertDialogCancel>
          <AlertDialogAction destructive onClick={onConfirm}>
            {t("users:delete.submit")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

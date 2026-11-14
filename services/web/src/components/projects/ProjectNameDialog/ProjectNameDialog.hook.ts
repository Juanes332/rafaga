import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import type { ProjectNameDialogProps } from "./ProjectNameDialog.types";

interface UseProjectNameDialog {
  name: string;
  nameError: string | null;
  setName: (v: string) => void;
  onSubmit: (e: FormEvent) => void;
}

/** Name draft reset on open; empty names are explained, not sent. */
export function useProjectNameDialog(p: ProjectNameDialogProps): UseProjectNameDialog {
  const { t } = useTranslation();
  const [name, setName] = useState(p.initialName ?? "");
  const [nameError, setNameError] = useState<string | null>(null);
  useEffect(() => {
    if (p.open) {
      setName(p.initialName ?? "");
      setNameError(null);
    }
  }, [p.open, p.initialName]);
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return setNameError(t("projects:create.nameRequired"));
    p.onSubmit(trimmed);
  };
  return { name, nameError, setName, onSubmit };
}

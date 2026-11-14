import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AlternativeNameDialogProps } from "./AlternativeNameDialog.types";

export const NO_COPY = "none";

/** Name + optional source alternative; resets every time the dialog opens. */
export function useAlternativeNameDialog(p: AlternativeNameDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [from, setFrom] = useState(NO_COPY);
  const [nameError, setNameError] = useState<string | null>(null);
  useEffect(() => {
    if (!p.open) return;
    setName(p.initialName ?? "");
    setFrom(NO_COPY);
    setNameError(null);
  }, [p.open, p.initialName]);
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return setNameError(t("alternatives:createDialog.nameRequired"));
    p.onSubmit(name.trim(), from === NO_COPY ? null : from);
  };
  return { name, setName, from, setFrom, nameError, onSubmit };
}

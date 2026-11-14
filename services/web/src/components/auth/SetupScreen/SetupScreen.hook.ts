import { useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { authKeys, useSetupMutation } from "@/api/auth/auth.queries";
import { hasCode } from "@/lib/http/api-error";
import { useSessionStore } from "@/stores/session/session.store";

export const MIN_PASSWORD = 10;

interface UseSetupScreen {
  email: string;
  password: string;
  passwordError: string | null;
  formError: unknown;
  pending: boolean;
  setEmail: (v: string) => void;
  setPassword: (v: string) => void;
  onSubmit: (e: FormEvent) => void;
}

function useSetupSubmit() {
  const mutation = useSetupMutation();
  const signIn = useSessionStore((s) => s.signIn);
  const qc = useQueryClient();
  const navigate = useNavigate();
  const submit = (email: string, password: string) =>
    mutation.mutate(
      { email, password },
      {
        onSuccess: (token) => {
          signIn(token);
          qc.setQueryData(authKeys.setupStatus, { needs_setup: false });
          void navigate({ to: "/projects" });
        },
        onError: (err) => hasCode(err, "setup_already_done") && void navigate({ to: "/login" }),
      },
    );
  return { mutation, submit };
}

/** First-run account: inline 10-char rule, server 422 mapped to the same place. */
export function useSetupScreen(): UseSetupScreen {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const { mutation, submit } = useSetupSubmit();
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (password.length < MIN_PASSWORD) return setLocalError(t("auth:passwordShort"));
    setLocalError(null);
    submit(email, password);
  };
  const serverShort = hasCode(mutation.error, "password_too_short");
  return {
    email,
    password,
    passwordError: localError ?? (serverShort ? t("auth:passwordShort") : null),
    formError: serverShort ? null : mutation.error,
    pending: mutation.isPending,
    setEmail,
    setPassword,
    onSubmit,
  };
}

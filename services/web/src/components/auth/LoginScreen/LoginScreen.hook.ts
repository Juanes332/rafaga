import { useState, type FormEvent } from "react";
import { useNavigate } from "@tanstack/react-router";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { useLoginMutation } from "@/api/auth/auth.queries";
import { isApiError } from "@/lib/http/api-error";
import { useSessionStore } from "@/stores/session/session.store";

interface UseLoginScreen {
  email: string;
  password: string;
  message: string | null;
  expired: boolean;
  pending: boolean;
  setEmail: (v: string) => void;
  setPassword: (v: string) => void;
  onSubmit: (e: FormEvent) => void;
}

function loginMessage(error: unknown, t: TFunction): string | null {
  if (!error) return null;
  if (isApiError(error) && error.status === 401) return t("errors:invalid_credentials");
  if (isApiError(error) && error.status === 429) {
    return error.retryAfter ? t("auth:login.wait", { seconds: error.retryAfter }) : t("errors:rate_limited_nowait");
  }
  return null;
}

/** SCR-02 logic: 401 → same message for unknown email and wrong password; 429 → wait time. */
export function useLoginScreen(): UseLoginScreen {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const mutation = useLoginMutation();
  const signIn = useSessionStore((s) => s.signIn);
  const expired = useSessionStore((s) => s.expired);
  const navigate = useNavigate();

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate(
      { email, password },
      { onSuccess: (token) => (signIn(token), void navigate({ to: "/projects" })) },
    );
  };
  return {
    email,
    password,
    message: loginMessage(mutation.error, t),
    expired: expired && !mutation.isError,
    pending: mutation.isPending,
    setEmail,
    setPassword,
    onSubmit,
  };
}

import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useCreateUser } from "@/api/users/users.queries";
import { hasCode } from "@/lib/http/api-error";

type Role = "architect" | "reviewer";

/** New account form; the 10-character rule is checked before sending (server too). */
export function useCreateUserForm() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("reviewer");
  const [shortPassword, setShortPassword] = useState(false);
  const create = useCreateUser();

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (password.length < 10) return setShortPassword(true);
    setShortPassword(false);
    create.mutate(
      { email: email.trim(), password, role },
      { onSuccess: () => (setEmail(""), setPassword(""), toast(t("users:create.created"))) },
    );
  };
  const serverShort = hasCode(create.error, "password_too_short");
  return {
    email,
    password,
    role,
    passwordError: shortPassword || serverShort ? t("auth:passwordShort") : null,
    error: serverShort ? null : create.error,
    pending: create.isPending,
    setEmail,
    setPassword,
    setRole: (r: string) => setRole(r as Role),
    onSubmit,
  };
}

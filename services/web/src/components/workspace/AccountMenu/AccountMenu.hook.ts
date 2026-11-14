import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useSessionStore } from "@/stores/session/session.store";

interface UseAccountMenu {
  email: string;
  initial: string;
  isArchitect: boolean;
  onLogout: () => void;
}

/** Account entry: the email, role-gated links and sign out. */
export function useAccountMenu(): UseAccountMenu {
  const user = useSessionStore((s) => s.user);
  const signOut = useSessionStore((s) => s.signOut);
  const qc = useQueryClient();
  const navigate = useNavigate();
  return {
    email: user?.email ?? "",
    initial: (user?.email ?? "?").slice(0, 1).toUpperCase(),
    isArchitect: user?.role === "architect",
    onLogout: () => {
      signOut();
      qc.clear();
      void navigate({ to: "/login" });
    },
  };
}

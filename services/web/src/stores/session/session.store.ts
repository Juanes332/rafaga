import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { Token, User } from "@/types/auth/auth.types";

interface SessionState {
  token: string | null;
  user: User | null;
  expiresAt: number | null;
  expired: boolean;
  signIn: (token: Token, now?: number) => void;
  signOut: () => void;
  expire: () => void;
  isValid: (now?: number) => boolean;
}

/** Bearer session (ADR-06): sessionStorage so it dies with the tab. */
export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      expiresAt: null,
      expired: false,
      signIn: (token, now = Date.now()) =>
        set({ token: token.access_token, user: token.user, expiresAt: now + token.expires_in * 1000, expired: false }),
      signOut: () => set({ token: null, user: null, expiresAt: null, expired: false }),
      expire: () => set({ token: null, user: null, expiresAt: null, expired: true }),
      isValid: (now = Date.now()) => {
        const { token, expiresAt } = get();
        return token !== null && expiresAt !== null && now < expiresAt;
      },
    }),
    {
      name: "rafaga-session",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({ token: s.token, user: s.user, expiresAt: s.expiresAt }),
    },
  ),
);

import { beforeEach, describe, expect, it } from "vitest";
import { useSessionStore } from "@/stores/session/session.store";
import type { Token } from "@/types/auth/auth.types";

const token: Token = {
  access_token: "abc",
  token_type: "bearer",
  expires_in: 3600,
  user: { id: "u1", email: "ana@estudio.co", role: "architect" },
};

describe("session store", () => {
  beforeEach(() => useSessionStore.getState().signOut());

  it("starts signed out", () => {
    expect(useSessionStore.getState().token).toBeNull();
  });

  it("stores token, user and expiry on sign in", () => {
    useSessionStore.getState().signIn(token, 1_000);
    const s = useSessionStore.getState();
    expect(s.token).toBe("abc");
    expect(s.user?.email).toBe("ana@estudio.co");
    expect(s.expiresAt).toBe(1_000 + 3_600_000);
  });

  it("treats an expired token as signed out", () => {
    useSessionStore.getState().signIn(token, 0);
    expect(useSessionStore.getState().isValid(3_600_001)).toBe(false);
    expect(useSessionStore.getState().isValid(10)).toBe(true);
  });

  it("flags the session as expired when signed out by a 401", () => {
    useSessionStore.getState().signIn(token, 0);
    useSessionStore.getState().expire();
    expect(useSessionStore.getState().token).toBeNull();
    expect(useSessionStore.getState().expired).toBe(true);
  });

  it("persists to sessionStorage, never localStorage", () => {
    useSessionStore.getState().signIn(token, 0);
    expect(sessionStorage.getItem("rafaga-session")).toContain("abc");
    expect(localStorage.getItem("rafaga-session")).toBeNull();
  });
});

import { redirect } from "@tanstack/react-router";
import { setupStatusQueryOptions } from "@/api/auth/auth.queries";
import { useSessionStore } from "@/stores/session/session.store";
import { queryClient } from "./query-client";

async function needsSetup(): Promise<boolean> {
  const status = await queryClient.ensureQueryData(setupStatusQueryOptions());
  return status.needs_setup;
}

/** Every app route: account creation first, then a valid session. */
export async function requireSession(): Promise<void> {
  if (await needsSetup()) throw redirect({ to: "/setup" });
  if (!useSessionStore.getState().isValid()) throw redirect({ to: "/login" });
}

export async function guardSetup(): Promise<void> {
  if (!(await needsSetup())) throw redirect({ to: useSessionStore.getState().isValid() ? "/projects" : "/login" });
}

export async function guardLogin(): Promise<void> {
  if (await needsSetup()) throw redirect({ to: "/setup" });
  if (useSessionStore.getState().isValid()) throw redirect({ to: "/projects" });
}

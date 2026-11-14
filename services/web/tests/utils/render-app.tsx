import { createMemoryHistory, createRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { queryClient } from "@/app/query-client";
import { routeTree } from "@/app/router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useSessionStore } from "@/stores/session/session.store";
import { architect, tokenFor } from "../msw/auth/auth.handlers";

/** Sign in as the fixture architect (or a given role) before rendering the app. */
export function signInAs(role: "architect" | "reviewer" = "architect"): void {
  useSessionStore.getState().signIn(tokenFor({ ...architect, role }));
}

/** Render the real route tree at a path, with the app's guards and query client. */
export function renderApp(path: string) {
  queryClient.clear();
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: [path] }) });
  const result = render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <RouterProvider router={router} />
      </TooltipProvider>
    </QueryClientProvider>,
  );
  return Object.assign(result, { router });
}

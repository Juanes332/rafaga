import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";
import { render, type RenderOptions, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";

/** Fresh client per test: retries off and no cache bleed between tests. */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } } });
}

/** Wrapper for renderHook() and any test needing the Query context. */
export function createQueryWrapper(client: QueryClient = createTestQueryClient()) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <TooltipProvider>{children}</TooltipProvider>
    </QueryClientProvider>
  );
}

/** render() with Query + Tooltip providers. */
export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, "wrapper">): RenderResult {
  return render(ui, { wrapper: createQueryWrapper(), ...options });
}

interface RouterRenderOptions {
  path?: string;
  /** Route pattern the UI is mounted on, e.g. /projects/$projectId/wind */
  pattern?: string;
  client?: QueryClient;
}

/** Render a component inside a memory router so <Link> and useParams work. */
export async function renderWithRouter(ui: ReactElement, opts: RouterRenderOptions = {}) {
  const rootRoute = createRootRoute({ component: () => <Outlet /> });
  const pattern = opts.pattern ?? "/";
  const uiRoute = createRoute({ getParentRoute: () => rootRoute, path: pattern, component: () => ui });
  const fallback = createRoute({ getParentRoute: () => rootRoute, path: "$", component: () => <p>destino</p> });
  const router = createRouter({
    routeTree: rootRoute.addChildren([uiRoute, fallback]),
    history: createMemoryHistory({ initialEntries: [opts.path ?? pattern] }),
  });
  const client = opts.client ?? createTestQueryClient();
  const result = render(<RouterProvider router={router} />, { wrapper: createQueryWrapper(client) });
  return Object.assign(result, { router });
}

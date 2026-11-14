import { createRouter } from "@tanstack/react-router";
import { homeRoute, pagesRoute, projectsRoute, settingsRoute, templatesRoute, usersRoute } from "./routes.pages";
import { authedRoute, loginRoute, rootRoute, setupRoute } from "./routes.root";
import {
  alternativesRoute,
  compareRoute,
  geometryRoute,
  locationRoute,
  reportsRoute,
  resultsRoute,
  simulateRoute,
  windRoute,
  workspaceIndexRoute,
  workspaceRoute,
} from "./routes.workspace";

export const routeTree = rootRoute.addChildren([
  setupRoute,
  loginRoute,
  authedRoute.addChildren([
    homeRoute,
    pagesRoute.addChildren([projectsRoute, settingsRoute, usersRoute, templatesRoute]),
    workspaceRoute.addChildren([
      workspaceIndexRoute,
      locationRoute,
      geometryRoute,
      windRoute,
      alternativesRoute,
      simulateRoute,
      resultsRoute,
      reportsRoute,
    ]),
    compareRoute,
  ]),
]);

/** Single typed router. */
export const router = createRouter({ routeTree, defaultPreload: false, scrollRestoration: true });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

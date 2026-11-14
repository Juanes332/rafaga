import { createRoute, redirect } from "@tanstack/react-router";
import { ProjectsScreen } from "@/components/projects/ProjectsScreen/ProjectsScreen";
import { SettingsScreen } from "@/components/settings/SettingsScreen/SettingsScreen";
import { TemplatesScreen } from "@/components/templates/TemplatesScreen/TemplatesScreen";
import { UsersScreen } from "@/components/users/UsersScreen/UsersScreen";
import { AppLayout } from "@/components/workspace/AppLayout/AppLayout";
import { authedRoute } from "./routes.root";

export const homeRoute = createRoute({
  getParentRoute: () => authedRoute,
  path: "/",
  beforeLoad: () => {
    throw redirect({ to: "/projects" });
  },
});

export const pagesRoute = createRoute({ getParentRoute: () => authedRoute, id: "pages", component: AppLayout });
export const projectsRoute = createRoute({ getParentRoute: () => pagesRoute, path: "/projects", component: ProjectsScreen });
export const settingsRoute = createRoute({ getParentRoute: () => pagesRoute, path: "/settings", component: SettingsScreen });
export const usersRoute = createRoute({ getParentRoute: () => pagesRoute, path: "/users", component: UsersScreen });
export const templatesRoute = createRoute({ getParentRoute: () => pagesRoute, path: "/templates", component: TemplatesScreen });

import { createRootRoute, createRoute, Outlet } from "@tanstack/react-router";
import { LoginScreen } from "@/components/auth/LoginScreen/LoginScreen";
import { SetupScreen } from "@/components/auth/SetupScreen/SetupScreen";
import { NotFound } from "@/components/feedback/NotFound/NotFound";
import { guardLogin, guardSetup, requireSession } from "./route-guards";

export const rootRoute = createRootRoute({ component: () => <Outlet />, notFoundComponent: NotFound });

export const setupRoute = createRoute({ getParentRoute: () => rootRoute, path: "/setup", beforeLoad: guardSetup, component: SetupScreen });
export const loginRoute = createRoute({ getParentRoute: () => rootRoute, path: "/login", beforeLoad: guardLogin, component: LoginScreen });

/** Pathless layout: every authenticated route passes the setup + session gate. */
export const authedRoute = createRoute({ getParentRoute: () => rootRoute, id: "authed", beforeLoad: requireSession, component: () => <Outlet /> });

import type { HttpHandler } from "msw";
import { authHandlers } from "./auth/auth.handlers";
import { systemHandlers } from "./system/system.handlers";
import { projectsHandlers } from "./projects/projects.handlers";
import { locationHandlers } from "./location/location.handlers";
import { geoHandlers } from "./geo/geo.handlers";
import { tilesHandlers } from "./tiles/tiles.handlers";
import { windHandlers } from "./wind/wind.handlers";
import { geometryHandlers } from "./geometry/geometry.handlers";
import { backgroundsHandlers } from "./backgrounds/backgrounds.handlers";
import { alternativesHandlers } from "./alternatives/alternatives.handlers";
import { facadesHandlers } from "./facades/facades.handlers";
import { sceneHandlers } from "./scene/scene.handlers";
import { simulationsHandlers } from "./simulations/simulations.handlers";
import { resultsHandlers } from "./results/results.handlers";
import { comparisonsHandlers } from "./comparisons/comparisons.handlers";
import { exportsHandlers } from "./exports/exports.handlers";
import { reportsHandlers } from "./reports/reports.handlers";
import { settingsHandlers } from "./settings/settings.handlers";
import { templatesHandlers } from "./templates/templates.handlers";
import { usersHandlers } from "./users/users.handlers";

/** Every domain handler, shared by the node server (tests) and the browser worker (mock mode). */
export const handlers: HttpHandler[] = [
  ...authHandlers,
  ...systemHandlers,
  ...projectsHandlers,
  ...locationHandlers,
  ...geoHandlers,
  ...tilesHandlers,
  ...windHandlers,
  ...geometryHandlers,
  ...backgroundsHandlers,
  ...alternativesHandlers,
  ...facadesHandlers,
  ...sceneHandlers,
  ...simulationsHandlers,
  ...resultsHandlers,
  ...comparisonsHandlers,
  ...exportsHandlers,
  ...reportsHandlers,
  ...settingsHandlers,
  ...templatesHandlers,
  ...usersHandlers,
];

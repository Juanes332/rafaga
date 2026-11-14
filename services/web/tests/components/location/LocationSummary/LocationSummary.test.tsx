import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LocationSummary } from "@/components/location/LocationSummary/LocationSummary";
import type { Project } from "@/types/projects/project.types";

const project = { lat: 5.536944, lon: -73.360556, elevation_m: 2500, elevation_source: "open_meteo", air_density_kg_m3: 0.9 } as unknown as Project;

describe("LocationSummary", () => {
  it("shows decimal degrees and degrees-minutes-seconds", () => {
    render(<LocationSummary project={project} />);
    expect(screen.getByText("5,53694")).toBeInTheDocument();
    expect(screen.getByText("5°32′13″ N")).toBeInTheDocument();
    expect(screen.getByText("73°21′38″ O")).toBeInTheDocument();
  });
});

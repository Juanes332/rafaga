import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { facadeDefaultsFrom, useApplyTemplate, useCreateTemplate } from "@/api/templates/templates.queries";
import { defaultSettings } from "../../msw/settings/settings.handlers";
import { templatesState } from "../../msw/templates/templates.handlers";
import { createQueryWrapper } from "../../utils/render-with-providers";

describe("templates api", () => {
  it("maps strategy defaults by type", () => {
    const out = facadeDefaultsFrom([
      { type: "screen", label_key: "s", parameters: [{ key: "porosity", unit: "", min: 0.05, max: 0.95, default: 0.4, help_key: "h" }] },
    ]);
    expect(out).toEqual({ screen: { porosity: 0.4 } });
  });
  it("rejects a payload with a location", async () => {
    const { result } = renderHook(() => useCreateTemplate(), { wrapper: createQueryWrapper() });
    const payload = { lat: 1, thresholds: defaultSettings().thresholds } as unknown as Parameters<typeof result.current.mutate>[0]["payload"];
    result.current.mutate({ name: "x", payload });
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "template_contains_location" }));
  });
  it("applies a template to a project", async () => {
    const { result } = renderHook(() => useApplyTemplate(), { wrapper: createQueryWrapper() });
    result.current.mutate({ projectId: "p", templateId: "00000000-0000-4000-8000-0000000000t1" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(templatesState.applied).toEqual(["p:00000000-0000-4000-8000-0000000000t1"]);
  });
});

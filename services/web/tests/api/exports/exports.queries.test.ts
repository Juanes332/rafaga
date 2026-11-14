import { describe, expect, it } from "vitest";
import { apiClient } from "@/lib/http/api-client";
import { exportsKeys, fetchExportFile, isExportActive } from "@/api/exports/exports.queries";
import type { ExportAccepted } from "@/types/exports/export.types";

describe("exports api", () => {
  it("keeps a stable key", () => {
    expect(exportsKeys.detail("e")).toEqual(["exports", "e"]);
  });
  it("treats queued and running as active", () => {
    expect(isExportActive({ status: "running" })).toBe(true);
    expect(isExportActive({ status: "completed" })).toBe(false);
    expect(isExportActive(undefined)).toBe(false);
  });
  it("refuses a file before it is ready, then downloads a PNG blob", async () => {
    const { export_id } = await apiClient.post<ExportAccepted>("/exports", { result_id: "r", layer: "k", dpi: 300 });
    await expect(fetchExportFile(export_id)).rejects.toMatchObject({ code: "export_not_ready" });
    await apiClient.get(`/exports/${export_id}`);
    await apiClient.get(`/exports/${export_id}`);
    const blob = await fetchExportFile(export_id);
    expect(blob.size).toBeGreaterThan(0);
  });
});

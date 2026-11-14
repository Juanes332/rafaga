import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { anyReportActive, reportsKeys, reportsQueryOptions, useCreateReport } from "@/api/reports/reports.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";

const P1 = "00000000-0000-4000-8000-0000000000p1";

describe("reports api", () => {
  it("detects an active version", () => {
    expect(anyReportActive([{ id: "r", version: 1, status: "running" }])).toBe(true);
    expect(anyReportActive([{ id: "r", version: 1, status: "failed" }])).toBe(false);
  });
  it("lists versions newest first", async () => {
    const list = await new QueryClient().fetchQuery(reportsQueryOptions(P1));
    expect(list[0].version).toBe(1);
  });
  it("creates a report and invalidates the list", async () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    const { result } = renderHook(() => useCreateReport(P1), { wrapper: createQueryWrapper(client) });
    result.current.mutate({ study_ids: ["s1"], include_comfort: true });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: reportsKeys.list(P1) });
  });
});

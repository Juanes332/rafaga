import { describe, expect, it } from "vitest";
import { isStudyActive, simulationsKeys } from "@/api/simulations/simulations.queries";

const job = (status: "queued" | "running" | "completed" | "failed" | "cancelled") =>
  ({ id: "j", kind: "plan2d", lane: "heavy", status, progress: 0, resumable: false }) as const;

describe("simulations polling condition", () => {
  it("polls while any job is queued or running", () => {
    expect(isStudyActive({ status: "running", jobs: [job("running")] })).toBe(true);
    expect(isStudyActive({ status: "partial", jobs: [job("completed"), job("queued")] })).toBe(true);
  });
  it("stops when every job is terminal", () => {
    expect(isStudyActive({ status: "completed", jobs: [job("completed"), job("failed")] })).toBe(false);
    expect(isStudyActive(undefined)).toBe(false);
  });
  it("keeps stable keys", () => {
    expect(simulationsKeys.detail("s")).toEqual(["simulations", "study", "s"]);
  });
});

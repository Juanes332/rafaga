import { describe, expect, it } from "vitest";
import { formatDate, formatDuration, formatRelative } from "@/lib/format/format.date";

const now = new Date("2026-11-13T12:00:00Z");

describe("date formatting", () => {
  it("formats absolute dates as '12 nov 2026'", () => {
    expect(formatDate("2026-11-12T10:00:00")).toBe("12 nov 2026");
  });
  it("uses relative time under 48 h", () => {
    expect(formatRelative("2026-11-13T10:00:00Z", now)).toBe("hace 2 h");
    expect(formatRelative("2026-11-13T11:55:00Z", now)).toBe("hace 5 min");
    expect(formatRelative("2026-11-13T11:59:40Z", now)).toBe("hace un momento");
    expect(formatRelative("2026-11-12T08:00:00Z", now)).toBe("ayer");
  });
  it("falls back to the absolute date beyond 48 h", () => {
    expect(formatRelative("2026-11-01T10:00:00", now)).toBe("1 nov 2026");
  });
  it("formats ETA durations", () => {
    expect(formatDuration(42)).toBe("42 s");
    expect(formatDuration(185)).toBe("3 min 5 s");
    expect(formatDuration(3720)).toBe("1 h 2 min");
    expect(formatDuration(null)).toBe("—");
  });
});

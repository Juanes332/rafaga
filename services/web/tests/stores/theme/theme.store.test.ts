import { beforeEach, describe, expect, it } from "vitest";
import { nextTheme, useThemeStore } from "@/stores/theme/theme.store";

describe("theme store", () => {
  beforeEach(() => useThemeStore.getState().setTheme("system"));

  it("follows the system by default and leaves data-theme unset", () => {
    expect(useThemeStore.getState().theme).toBe("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("writes data-theme on explicit choice", () => {
    useThemeStore.getState().setTheme("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("cycles light → dark → system", () => {
    expect(nextTheme("light")).toBe("dark");
    expect(nextTheme("dark")).toBe("system");
    expect(nextTheme("system")).toBe("light");
  });
});

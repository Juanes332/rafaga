import { describe, expect, it } from "vitest";
import { login, setupAccount, setupStatusQueryOptions } from "@/api/auth/auth.queries";
import { createTestQueryClient } from "../../utils/render-with-providers";
import { authState } from "../../msw/auth/auth.handlers";

describe("auth api", () => {
  it("reads setup status", async () => {
    authState.needsSetup = true;
    await expect(createTestQueryClient().fetchQuery(setupStatusQueryOptions())).resolves.toEqual({ needs_setup: true });
  });
  it("creates the first account", async () => {
    authState.needsSetup = true;
    const token = await setupAccount({ email: "a@b.co", password: "0123456789" });
    expect(token.user.role).toBe("architect");
  });
  it("rejects bad credentials with invalid_credentials", async () => {
    await expect(login({ email: "a@b.co", password: "x" })).rejects.toMatchObject({ status: 401, code: "invalid_credentials" });
  });
});

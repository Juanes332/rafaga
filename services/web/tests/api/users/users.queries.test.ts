import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { useCreateUser, useDeleteUser, usersQueryOptions } from "@/api/users/users.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";

describe("users api", () => {
  it("lists users", async () => {
    const list = await new QueryClient().fetchQuery(usersQueryOptions());
    expect(list.map((u) => u.role)).toEqual(["architect", "reviewer"]);
  });
  it("creates a user and reports email_taken", async () => {
    const { result } = renderHook(() => useCreateUser(), { wrapper: createQueryWrapper() });
    result.current.mutate({ email: "rev@estudio.co", password: "0123456789", role: "reviewer" });
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "email_taken" }));
  });
  it("refuses to delete yourself", async () => {
    const { result } = renderHook(() => useDeleteUser(), { wrapper: createQueryWrapper() });
    result.current.mutate("00000000-0000-4000-8000-0000000000a1");
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "cannot_delete_self" }));
  });
});

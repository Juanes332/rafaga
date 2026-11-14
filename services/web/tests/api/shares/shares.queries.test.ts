import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { sharesQueryOptions, useToggleShare } from "@/api/shares/shares.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";

const P2 = "00000000-0000-4000-8000-0000000000p2";

describe("shares api", () => {
  it("grants and revokes access", async () => {
    const client = new QueryClient();
    const { result } = renderHook(() => useToggleShare(), { wrapper: createQueryWrapper(client) });
    result.current.mutate({ projectId: P2, userId: "00000000-0000-4000-8000-0000000000a2", grant: true });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(await client.fetchQuery(sharesQueryOptions(P2))).toHaveLength(1);
    result.current.mutate({ projectId: P2, userId: "00000000-0000-4000-8000-0000000000a2", grant: false });
    await waitFor(() => expect(result.current.variables?.grant).toBe(false));
    await waitFor(async () => expect(await new QueryClient().fetchQuery(sharesQueryOptions(P2))).toHaveLength(0));
  });
});

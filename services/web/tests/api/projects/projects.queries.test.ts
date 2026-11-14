import { QueryClient } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  projectsKeys,
  projectsQueryOptions,
  useCreateProject,
  useDeleteProject,
  useDuplicateProject,
} from "@/api/projects/projects.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const spy = vi.spyOn(client, "invalidateQueries");
  return { client, spy, wrapper: createQueryWrapper(client) };
}

describe("projects queries", () => {
  it("keeps stable keys", () => {
    expect(projectsKeys.all).toEqual(["projects"]);
    expect(projectsKeys.detail("x")).toEqual(["projects", "x"]);
  });

  it("lists project summaries", async () => {
    const { client } = setup();
    const list = await client.fetchQuery(projectsQueryOptions());
    expect(list.map((p) => p.name)).toEqual(["Edificio de la calle 5", "Conjunto norte"]);
    expect(list[0].has_location).toBe(true);
  });

  it("creates a project without a location and invalidates the list", async () => {
    const { spy, wrapper } = setup();
    const { result } = renderHook(() => useCreateProject(), { wrapper });
    result.current.mutate("Torre sur");
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.lat).toBeNull();
    expect(spy).toHaveBeenCalledWith({ queryKey: projectsKeys.all });
  });

  it("duplicates and deletes", async () => {
    const { wrapper } = setup();
    const dup = renderHook(() => useDuplicateProject(), { wrapper });
    dup.result.current.mutate("00000000-0000-4000-8000-0000000000p2");
    await waitFor(() => expect(dup.result.current.data?.name).toBe("Copia de Conjunto norte"));
    const del = renderHook(() => useDeleteProject(), { wrapper });
    del.result.current.mutate("00000000-0000-4000-8000-0000000000p2");
    await waitFor(() => expect(del.result.current.isSuccess).toBe(true));
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import { saveBlob } from "@/hooks/download/save-blob";

describe("saveBlob", () => {
  afterEach(() => vi.restoreAllMocks());

  it("clicks a temporary anchor with the file name and removes it", () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:x");
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    saveBlob(new Blob(["a"]), "rafaga-k.png");
    const anchor = click.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe("rafaga-k.png");
    expect(anchor.href).toBe("blob:x");
    expect(document.querySelector("a[download]")).toBeNull();
  });
});

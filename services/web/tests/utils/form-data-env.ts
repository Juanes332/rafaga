import { File as NodeFile } from "node:buffer";
import { afterAll, beforeAll } from "vitest";

/**
 * jsdom's FormData/File are not understood by Node's fetch (undici), so multipart bodies
 * reach MSW as text. Swap in Node's classes for tests that upload.
 */
export function useNodeFormData(): void {
  const original = { FormData: globalThis.FormData, File: globalThis.File };
  beforeAll(async () => {
    const nodeForm = await new Response("a=1", { headers: { "Content-Type": "application/x-www-form-urlencoded" } }).formData();
    globalThis.FormData = nodeForm.constructor as typeof FormData;
    globalThis.File = NodeFile as unknown as typeof File;
  });
  afterAll(() => {
    globalThis.FormData = original.FormData;
    globalThis.File = original.File;
  });
}

import axe from "axe-core";

/** Serious/critical axe violations in the current document (jsdom cannot judge colour contrast). */
export async function seriousViolations(root: Element = document.body): Promise<string[]> {
  const result = await axe.run(root, { rules: { "color-contrast": { enabled: false }, region: { enabled: false } } });
  return result.violations
    .filter((v) => v.impact === "serious" || v.impact === "critical")
    .map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`);
}

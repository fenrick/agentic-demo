import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DocumentPanel from "../../../frontend/src/components/DocumentPanel";

describe("DocumentPanel", () => {
  it("highlights newly inserted text", async () => {
    const { rerender } = render(
      <DocumentPanel text="hello world" onAcceptDiff={() => {}} />,
    );

    rerender(
      <DocumentPanel text="hello brave world" onAcceptDiff={() => {}} />,
    );

    const el = await screen.findByText("brave");
    await new Promise((r) => setTimeout(r, 60));
    expect(el.classList.contains("highlight")).toBe(true);
  });
});

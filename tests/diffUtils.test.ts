import { computeDiff } from "@/utils/diffUtils";

describe("computeDiff", () => {
  it("computes insert patches", () => {
    const result = computeDiff("hello world", "hello brave world");
    expect(result).toEqual([
      { type: "equal", token: "hello" },
      { type: "equal", token: " " },
      { type: "insert", token: "brave" },
      { type: "insert", token: " " },
      { type: "equal", token: "world" },
    ]);
  });

  it("computes delete patches", () => {
    const result = computeDiff("hello brave world", "hello world");
    expect(result).toEqual([
      { type: "equal", token: "hello" },
      { type: "equal", token: " " },
      { type: "delete", token: "brave" },
      { type: "delete", token: " " },
      { type: "equal", token: "world" },
    ]);
  });
});

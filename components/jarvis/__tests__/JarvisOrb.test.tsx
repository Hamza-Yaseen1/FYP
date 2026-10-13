import { describe, it, expect, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render } from "@testing-library/react";
import JarvisOrb from "../JarvisOrb";

afterEach(cleanup);

describe("JarvisOrb", () => {
  it("renders with idle state by default", () => {
    const { getByRole } = render(<JarvisOrb state="idle" />);
    const orb = getByRole("status");
    expect(orb).toHaveAttribute("data-state", "idle");
    expect(orb).toHaveClass("jarvis-orb--idle");
    expect(orb).toHaveAttribute("aria-label", "JARVIS idle");
  });

  it.each(["listening", "thinking", "speaking"] as const)(
    "applies the %s state class",
    (state) => {
      const { getByRole } = render(<JarvisOrb state={state} />);
      expect(getByRole("status")).toHaveClass(`jarvis-orb--${state}`);
      expect(getByRole("status")).toHaveAttribute("data-state", state);
    }
  );

  it("supports size variants", () => {
    const { getByRole, rerender } = render(<JarvisOrb state="idle" size="sm" />);
    expect(getByRole("status")).toHaveClass("size-8");
    rerender(<JarvisOrb state="idle" size="lg" />);
    expect(getByRole("status")).toHaveClass("size-14");
  });
});
import { describe, it, expect, vi, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import JarvisLauncher from "../JarvisLauncher";

afterEach(cleanup);

describe("JarvisLauncher", () => {
  it("calls onClick when clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<JarvisLauncher state="idle" onClick={onClick} />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is labelled for assistive tech", () => {
    render(<JarvisLauncher state="idle" onClick={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: "Open Kestrel" })
    ).toBeInTheDocument();
  });
});
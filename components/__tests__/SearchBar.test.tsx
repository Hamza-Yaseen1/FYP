import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SearchBar from "../SearchBar";

const asHTMLElement = (el: Element | null): HTMLElement => el as HTMLElement;

describe("SearchBar", () => {
  it("renders search input with placeholder", () => {
    const { container } = render(<SearchBar value="" onChange={vi.fn()} onClear={vi.fn()} />);
    const root = asHTMLElement(container.firstElementChild);
    expect(within(root).getByPlaceholderText("Search messages...")).toBeDefined();
  });

  it("displays custom placeholder", () => {
    const { container } = render(<SearchBar value="" onChange={vi.fn()} onClear={vi.fn()} placeholder="Custom placeholder" />);
    const root = asHTMLElement(container.firstElementChild);
    expect(within(root).getByPlaceholderText("Custom placeholder")).toBeDefined();
  });

  it("displays current value", () => {
    const { container } = render(<SearchBar value="test query" onChange={vi.fn()} onClear={vi.fn()} />);
    const root = asHTMLElement(container.firstElementChild);
    expect(within(root).getByDisplayValue("test query")).toBeDefined();
  });

  it("shows clear button when value is not empty", () => {
    const { container } = render(<SearchBar value="test" onChange={vi.fn()} onClear={vi.fn()} />);
    const root = asHTMLElement(container.firstElementChild);
    expect(within(root).getAllByRole("button").length).toBeGreaterThan(0);
  });

  it("does not show clear button when value is empty", () => {
    const { container } = render(<SearchBar value="" onChange={vi.fn()} onClear={vi.fn()} />);
    const root = asHTMLElement(container.firstElementChild);
    expect(within(root).queryAllByRole("button").length).toBe(0);
  });

  it("calls onClear when clear button is clicked", async () => {
    const user = userEvent.setup();
    const onClear = vi.fn();
    const onChange = vi.fn();
    const { container } = render(<SearchBar value="test" onChange={onChange} onClear={onClear} />);
    const root = asHTMLElement(container.firstElementChild);

    await user.click(within(root).getByRole("button"));
    expect(onClear).toHaveBeenCalled();
  });
});
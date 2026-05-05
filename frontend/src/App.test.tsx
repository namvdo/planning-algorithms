import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("@uiw/react-codemirror", () => ({
  default: ({ value, onChange, "aria-label": ariaLabel }: { value: string; onChange: (value: string) => void; "aria-label": string }) => (
    <textarea aria-label={ariaLabel} value={value} onChange={(event) => onChange(event.currentTarget.value)} />
  ),
}));

const traceResponse = {
  algorithm: "forward",
  status: "found",
  start: { row: 0, col: 0 },
  goal: { row: 0, col: 2 },
  rows: 1,
  cols: 3,
  plan: [{ index: 1, from_state: { row: 0, col: 0 }, to_state: { row: 0, col: 1 }, action: "right" }],
  trace: [
    {
      index: 0,
      phase: "forward",
      message: "Initialize the frontier with the start state.",
      current: null,
      frontier: [{ row: 0, col: 0 }],
      visited: [{ row: 0, col: 0 }],
      backward_frontier: [],
      backward_visited: [],
      forward_tree_edges: [],
      backward_tree_edges: [],
      discovered: [],
      meeting_state: null,
      plan_prefix: [],
    },
    {
      index: 1,
      phase: "complete",
      message: "Goal reached.",
      current: { row: 0, col: 2 },
      frontier: [],
      visited: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 0, col: 2 },
      ],
      backward_frontier: [],
      backward_visited: [],
      forward_tree_edges: [
        { from_state: { row: 0, col: 0 }, to_state: { row: 0, col: 1 }, action: "right" },
        { from_state: { row: 0, col: 1 }, to_state: { row: 0, col: 2 }, action: "right" },
      ],
      backward_tree_edges: [],
      discovered: [],
      meeting_state: null,
      plan_prefix: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 0, col: 2 },
      ],
    },
  ],
  stats: {
    expanded_count: 3,
    visited_count: 3,
    max_frontier_size: 1,
    path_length: 2,
    trace_length: 2,
  },
};

const weightedTraceResponse = {
  algorithm: "dijkstra",
  status: "found",
  start: { row: 0, col: 0 },
  goal: { row: 0, col: 0 },
  rows: 0,
  cols: 0,
  plan: [],
  graph: {
    nodes: [
      { id: "S", label: null, x: 48, y: 170, heuristic: 7 },
      { id: "B", label: null, x: 220, y: 270, heuristic: 6 },
      { id: "G", label: null, x: 560, y: 170, heuristic: 0 },
    ],
    edges: [
      { source: "S", target: "B", cost: 2 },
      { source: "B", target: "G", cost: 3 },
    ],
    start: "S",
    goal: "G",
  },
  graph_path: ["S", "B", "G"],
  trace: [
    {
      index: 0,
      phase: "complete",
      message: "Optimal path S -> B -> G has total cost 5.",
      current: null,
      frontier: [],
      visited: [],
      backward_frontier: [],
      backward_visited: [],
      forward_tree_edges: [],
      backward_tree_edges: [],
      discovered: [],
      meeting_state: null,
      plan_prefix: [],
      current_node: "G",
      frontier_nodes: [],
      visited_nodes: ["S", "B", "G"],
      settled_nodes: ["S", "B", "G"],
      updated_nodes: [],
      node_labels: [
        { node_id: "S", g: 0, h: 7, f: 7, value: null, residual: null },
        { node_id: "B", g: 2, h: 6, f: 8, value: null, residual: null },
        { node_id: "G", g: 5, h: 0, f: 5, value: null, residual: null },
      ],
      active_edge: null,
      parent_edges: [
        { source: "S", target: "B", cost: 2 },
        { source: "B", target: "G", cost: 3 },
      ],
      policy_edges: [],
      relaxation: null,
      priority_queue: [],
    },
  ],
  stats: {
    expanded_count: 3,
    visited_count: 3,
    max_frontier_size: 1,
    path_length: 2,
    trace_length: 1,
    total_cost: 5,
    relaxation_count: 2,
    sweep_count: 0,
  },
};

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/code/default")) {
          return {
            ok: true,
            json: async () => ({ language: "python3", code: "def forward_search(x_init, is_goal, get_actions, transition):\n    return []" }),
          };
        }
        if (url.includes("/code/evaluate")) {
          return {
            ok: true,
            json: async () => ({
              algorithm: "forward",
              passed: true,
              cases: [
                {
                  name: "Current grid",
                  passed: true,
                  message: "Plan is valid and has the expected length.",
                  expected_length: 2,
                  actual_length: 2,
                },
              ],
              stdout: "",
              stderr: "",
              duration_ms: 12,
            }),
          };
        }
        if (url.includes("/code/visualize")) {
          return {
            ok: true,
            json: async () => traceResponse,
          };
        }
        if (url.includes("/search/trace")) {
          return {
            ok: true,
            json: async () => weightedTraceResponse,
          };
        }
        return {
          ok: true,
          json: async () => traceResponse,
        };
      }),
    );
  });

  it("uses the selected algorithm and editor code for visualization", async () => {
    render(<App />);
    expect(screen.getByText("No trace")).toBeInTheDocument();
    vi.mocked(fetch).mockClear();

    fireEvent.click(screen.getByRole("button", { name: /Backward Backward Search/i }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/default/backward"))).toBe(true));
    vi.mocked(fetch).mockClear();
    fireEvent.click(screen.getByRole("button", { name: /^Run$/i }));

    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/visualize"))).toBe(true));
    const traceCall = vi.mocked(fetch).mock.calls.find((call) => String(call[0]).includes("/code/visualize"));
    const request = JSON.parse(String(traceCall?.[1]?.body));
    expect(request.algorithm).toBe("backward");
    expect(request.code).toContain("forward_search");
  });

  it("validates malformed grids before running", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Forward Forward Search/i }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/default/forward"))).toBe(true));

    fireEvent.change(screen.getByLabelText("Grid editor"), { target: { value: "S\nGG" } });

    expect(screen.getByText("Grid must be rectangular.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Run$/i })).toBeDisabled();
  });

  it("steps and resets trace frames", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Forward Forward Search/i }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/default/forward"))).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: /^Run$/i }));
    await screen.findByText("Frame 2 of 2");

    fireEvent.click(screen.getByRole("button", { name: /^Reset$/i }));
    expect(screen.getByText("Frame 1 of 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Current frame metrics")).toHaveTextContent("1 visited nodes");
    expect(screen.getByLabelText("Current frame metrics")).toHaveTextContent("0 path nodes");
    expect(screen.getAllByTestId("visited-marker")).toHaveLength(1);

    fireEvent.click(screen.getByLabelText("Next frame"));
    expect(screen.getByText("Frame 2 of 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Current frame metrics")).toHaveTextContent("3 visited nodes");
    expect(screen.getByLabelText("Current frame metrics")).toHaveTextContent("3 path nodes");
    expect(screen.queryByTestId("visited-marker")).not.toBeInTheDocument();
  });

  it("renders stats and complexity content", async () => {
    render(<App />);

    expect(await screen.findByText("Run Stats")).toBeInTheDocument();
    expect(screen.getByText("Time O((|S| + |E|) log |S|) with a binary heap, space O(|S| + |E|).")).toBeInTheDocument();
    expect(screen.queryByText("Good fit")).not.toBeInTheDocument();
    expect(screen.getByText("Pseudocode")).toBeInTheDocument();
    expect(screen.getByText("No run yet.")).toBeInTheDocument();
  });

  it("evaluates the exact Python3 editor code", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Forward Forward Search/i }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/default/forward"))).toBe(true));
    vi.mocked(fetch).mockClear();

    fireEvent.change(screen.getByLabelText("Python3 live code editor"), {
      target: { value: "def forward_search(x_init, is_goal, get_actions, transition):\n    return None" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Run Code/i }));

    await screen.findByText("All judge cases passed");
    const request = JSON.parse(String(vi.mocked(fetch).mock.calls[0][1]?.body));
    expect(request.code).toContain("return None");
  });

  it("uses dark theme by default and toggles the whole app theme", async () => {
    const { container } = render(<App />);
    await screen.findByText("No trace");

    expect(container.querySelector(".app-shell")).toHaveClass("theme-dark");
    fireEvent.click(screen.getByLabelText("Toggle app theme"));

    expect(container.querySelector(".app-shell")).toHaveClass("theme-light");
    expect(screen.getByLabelText("Toggle app theme")).toHaveTextContent("Dark");
  });

  it("reruns visualization when running code evaluation", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Forward Forward Search/i }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/default/forward"))).toBe(true));
    vi.mocked(fetch).mockClear();

    fireEvent.click(screen.getByRole("button", { name: /Run Code/i }));

    await screen.findByText("All judge cases passed");
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/evaluate"))).toBe(true);
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/code/visualize"))).toBe(true);
  });

  it("runs weighted graph algorithms through the graph trace endpoint", async () => {
    render(<App />);
    await screen.findByText("No trace");
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/search/trace"))).toBe(false);
    expect(screen.getByLabelText("Next frame")).toBeEnabled();
    vi.mocked(fetch).mockClear();

    fireEvent.click(screen.getByLabelText("Next frame"));

    await screen.findAllByText("Weighted Graph");
    await screen.findAllByText("Optimal path S -> B -> G has total cost 5.");
    expect(screen.getByText("Frame 1 of 1")).toBeInTheDocument();
    const traceCall = vi.mocked(fetch).mock.calls.find((call) => String(call[0]).includes("/search/trace"));
    const request = JSON.parse(String(traceCall?.[1]?.body));
    expect(request.algorithm).toBe("dijkstra");
    expect(request.graph.start).toBe("S");
    expect(screen.queryByLabelText("Python3 live code editor")).not.toBeInTheDocument();
  });
});

import type { SearchResponse, State, TraceFrame } from "../lib/types";

interface Props {
  result: SearchResponse | null;
  frame: TraceFrame | null;
  gridText: string;
}

const CELL = 42;

export function GridVisualization({ result, frame, gridText }: Props) {
  const rows = gridText.split("\n").filter((row) => row.length > 0);
  const rowCount = result?.rows ?? rows.length;
  const colCount = result?.cols ?? rows[0]?.length ?? 1;
  const path = new Set((frame?.plan_prefix ?? []).map(keyOf));
  const visited = new Set((frame?.visited ?? []).map(keyOf));
  const backwardVisited = new Set((frame?.backward_visited ?? []).map(keyOf));
  const frontier = new Set((frame?.frontier ?? []).map(keyOf));
  const backwardFrontier = new Set((frame?.backward_frontier ?? []).map(keyOf));
  const discovered = new Set((frame?.discovered ?? []).map(keyOf));
  const current = frame?.current ? keyOf(frame.current) : null;
  const meeting = frame?.meeting_state ? keyOf(frame.meeting_state) : null;

  return (
    <div className="visualization-panel">
      <div className="panel-heading">
        <h2>Visualization</h2>
        <span className="status-pill">{frame ? `Frame ${frame.index + 1} of ${result?.trace.length ?? 1}` : "No trace"}</span>
      </div>
      <svg
        className="grid-svg"
        role="img"
        aria-label="Search grid visualization"
        viewBox={`0 0 ${colCount * CELL} ${rowCount * CELL}`}
        data-testid="grid-visualization"
      >
        {Array.from({ length: rowCount }).flatMap((_, row) =>
          Array.from({ length: colCount }).map((__, col) => {
            const state = { row, col };
            const key = keyOf(state);
            const char = rows[row]?.[col] ?? ".";
            const classes = [
              "cell",
              char === "#" ? "wall" : "",
              visited.has(key) ? "visited" : "",
              backwardVisited.has(key) ? "backward-visited" : "",
              frontier.has(key) || backwardFrontier.has(key) ? "frontier" : "",
              discovered.has(key) ? "discovered" : "",
              path.has(key) ? "path" : "",
              current === key ? "current" : "",
              meeting === key ? "meeting" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <g key={key}>
                <rect className={classes} x={col * CELL + 1} y={row * CELL + 1} width={CELL - 2} height={CELL - 2} rx="4" />
                {char === "S" || char === "G" ? (
                  <text className="cell-label" x={col * CELL + CELL / 2} y={row * CELL + CELL / 2 + 5} textAnchor="middle">
                    {char}
                  </text>
                ) : null}
              </g>
            );
          }),
        )}
      </svg>
      <div className="legend" aria-label="Visualization legend">
        <span><i className="swatch visited" /> Forward visited</span>
        <span><i className="swatch backward" /> Backward visited</span>
        <span><i className="swatch frontier" /> Frontier</span>
        <span><i className="swatch path" /> Plan</span>
      </div>
      <p className="frame-message">{frame?.message ?? "Run an algorithm to create a trace."}</p>
    </div>
  );
}

function keyOf(state: State): string {
  return `${state.row},${state.col}`;
}


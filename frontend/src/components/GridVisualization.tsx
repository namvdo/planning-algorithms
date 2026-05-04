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
  const totalVisited = new Set([...visited, ...backwardVisited]);

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
            const inVisited = totalVisited.has(key);
            const inPath = path.has(key);
            const classes = [
              "cell",
              char === "#" ? "wall" : "",
              inVisited ? "visited" : "",
              inPath ? "path" : "",
            ]
              .filter(Boolean)
              .join(" ");
            const labels = [
              char === "S" ? "Start" : "",
              char === "G" ? "Goal" : "",
              char === "#" ? "Wall" : "",
              inVisited ? "Visited" : "",
              inPath ? "Plan path" : "",
            ]
              .filter(Boolean)
              .join(", ");

            return (
              <g key={key}>
                <rect className={classes} x={col * CELL + 1} y={row * CELL + 1} width={CELL - 2} height={CELL - 2} rx="4" />
                {inVisited && !inPath && char !== "#" ? (
                  <circle
                    className="visited-marker"
                    data-testid="visited-marker"
                    cx={col * CELL + CELL - 10}
                    cy={row * CELL + 10}
                    r="4.5"
                  />
                ) : null}
                <title>{`(${row}, ${col})${labels ? `: ${labels}` : ""}`}</title>
              </g>
            );
          }),
        )}
        {Array.from({ length: rowCount }).flatMap((_, row) =>
          Array.from({ length: colCount }).map((__, col) => {
            const char = rows[row]?.[col] ?? ".";
            if (char !== "S" && char !== "G") {
              return null;
            }
            return (
              <text key={`label-${row}-${col}`} className="cell-label" x={col * CELL + CELL / 2} y={row * CELL + CELL / 2 + 5} textAnchor="middle">
                {char}
              </text>
            );
          }),
        )}
      </svg>
      <div className="legend" aria-label="Visualization legend">
        <span>
          <i className="legend-chip visited-node">
            <i className="legend-visit-dot" />
          </i>
          Visited nodes
        </span>
        <span>
          <i className="legend-chip solution-path" />
          Solution path
        </span>
      </div>
      <div className="frame-metrics" aria-label="Current frame metrics">
        <span><strong>{totalVisited.size}</strong> visited nodes</span>
        <span><strong>{path.size}</strong> path nodes</span>
      </div>
      <p className="frame-message">{frame?.message ?? "Run an algorithm to create a trace."}</p>
    </div>
  );
}

function keyOf(state: State): string {
  return `${state.row},${state.col}`;
}

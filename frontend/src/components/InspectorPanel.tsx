import type { AlgorithmContent } from "../lib/content";
import type { SearchResponse, TraceFrame } from "../lib/types";
import { LatexBlock } from "./LatexBlock";

interface Props {
  algorithm: AlgorithmContent;
  result: SearchResponse | null;
  frame: TraceFrame | null;
}

export function InspectorPanel({ algorithm, result, frame }: Props) {
  return (
    <aside className="inspector">
      <section className="panel">
        <h2>{algorithm.title}</h2>
        <p>{algorithm.summary}</p>
        <dl className="stats">
          <div>
            <dt>Complexity</dt>
            <dd>{algorithm.complexity}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{algorithm.citation}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <h2>Pseudocode</h2>
        <LatexBlock value={algorithm.pseudocodeLatex} />
      </section>

      <section className="panel">
        <h2>Run Stats</h2>
        {result ? (
          <dl className="metric-grid">
            <div>
              <dt>Status</dt>
              <dd>{result.status === "found" ? "Found" : "No path"}</dd>
            </div>
            <div>
              <dt>Path</dt>
              <dd>{result.stats.path_length ?? "n/a"}</dd>
            </div>
            <div>
              <dt>Expanded</dt>
              <dd>{result.stats.expanded_count}</dd>
            </div>
            <div>
              <dt>Visited</dt>
              <dd>{result.stats.visited_count}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted">No run yet.</p>
        )}
      </section>

      <section className="panel">
        <h2>Trace</h2>
        <p className="trace-line">{frame?.message ?? "No trace selected."}</p>
      </section>
    </aside>
  );
}

import CodeMirror from "@uiw/react-codemirror";

interface Props {
  value: string;
  error: string | null;
  onChange: (value: string) => void;
}

export function GraphEditor({ value, error, onChange }: Props) {
  return (
    <div className="grid-editor">
      <div className="panel-heading">
        <h2>Weighted Graph</h2>
        <span className={error ? "status-pill warning" : "status-pill"}>{error ? "Invalid" : "Ready"}</span>
      </div>
      <CodeMirror
        aria-label="Weighted graph editor"
        value={value}
        basicSetup={{
          lineNumbers: false,
          foldGutter: false,
          highlightActiveLine: false,
          highlightActiveLineGutter: false,
        }}
        height="260px"
        onChange={onChange}
        theme="light"
      />
      {error ? (
        <p className="input-error">{error}</p>
      ) : (
        <p className="hint">Use directed edges with positive costs. A* reads each node&apos;s heuristic field.</p>
      )}
    </div>
  );
}

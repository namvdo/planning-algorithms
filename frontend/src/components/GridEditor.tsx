import CodeMirror from "@uiw/react-codemirror";

interface Props {
  value: string;
  error: string | null;
  onChange: (value: string) => void;
}

export function GridEditor({ value, error, onChange }: Props) {
  return (
    <div className="grid-editor">
      <div className="panel-heading">
        <h2>Problem</h2>
        <span className={error ? "status-pill warning" : "status-pill"}>{error ? "Invalid" : "Ready"}</span>
      </div>
      <CodeMirror
        aria-label="Grid editor"
        value={value}
        basicSetup={{
          lineNumbers: false,
          foldGutter: false,
          highlightActiveLine: false,
          highlightActiveLineGutter: false,
        }}
        height="160px"
        onChange={onChange}
        theme="light"
      />
      {error ? <p className="input-error">{error}</p> : <p className="hint">Use S for start, G for goal, # for walls, and . for free cells.</p>}
    </div>
  );
}


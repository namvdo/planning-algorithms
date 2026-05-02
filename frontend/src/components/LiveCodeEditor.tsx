import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { CheckCircle2, Play, RefreshCcw, XCircle } from "lucide-react";
import type { CodeEvaluationResponse } from "../lib/types";

interface Props {
  code: string;
  theme: "light" | "dark";
  loading: boolean;
  evaluation: CodeEvaluationResponse | null;
  onChange: (code: string) => void;
  onEvaluate: () => void;
  onReset: () => void;
}

export function LiveCodeEditor({
  code,
  theme,
  loading,
  evaluation,
  onChange,
  onEvaluate,
  onReset,
}: Props) {
  return (
    <section className="live-code-panel">
      <div className="panel-heading">
        <div>
          <h2>Live Python3 Editor</h2>
          <p className="subtle">Edit the selected algorithm. The visualization run uses this exact code.</p>
        </div>
        <div className="editor-actions">
          <button type="button" onClick={onReset}>
            <RefreshCcw size={16} />
            Reset code
          </button>
          <button type="button" onClick={onEvaluate} disabled={loading}>
            <Play size={16} />
            {loading ? "Evaluating" : "Run Code"}
          </button>
        </div>
      </div>
      <CodeMirror
        aria-label="Python3 live code editor"
        value={code}
        extensions={[python()]}
        basicSetup={{
          foldGutter: true,
          lineNumbers: true,
          highlightActiveLine: true,
          highlightActiveLineGutter: true,
        }}
        height="520px"
        theme={theme === "dark" ? oneDark : "light"}
        onChange={onChange}
      />
      {evaluation ? (
        <div className={evaluation.passed ? "judge-result passed" : "judge-result failed"}>
          <div className="judge-summary">
            {evaluation.passed ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
            <strong>{evaluation.passed ? "All judge cases passed" : "Some judge cases failed"}</strong>
            <span>{evaluation.duration_ms} ms</span>
          </div>
          <div className="judge-cases">
            {evaluation.cases.map((testCase) => (
              <div key={testCase.name} className="judge-case">
                <strong>{testCase.name}</strong>
                <span>{testCase.passed ? "pass" : "fail"}</span>
                <p>{testCase.message}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="hint">
          Expected return value: a list of action strings such as <code>["right", "down"]</code>, or <code>None</code> when no plan exists.
        </p>
      )}
    </section>
  );
}

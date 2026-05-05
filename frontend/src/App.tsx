import { useEffect, useMemo, useState } from "react";
import { AlgorithmSelector } from "./components/AlgorithmSelector";
import { GraphEditor } from "./components/GraphEditor";
import { GridEditor } from "./components/GridEditor";
import { GridVisualization } from "./components/GridVisualization";
import { InspectorPanel } from "./components/InspectorPanel";
import { LiveCodeEditor } from "./components/LiveCodeEditor";
import { TraceControls } from "./components/TraceControls";
import { WeightedGraphVisualization } from "./components/WeightedGraphVisualization";
import { algorithms, defaultGrid, defaultWeightedGraph, plannedTopics } from "./lib/content";
import { evaluateCode, fetchDefaultCode, fetchWeightedGraphTrace, visualizeCode } from "./lib/api";
import { parseGraphText } from "./lib/graphValidation";
import { validateGridText } from "./lib/gridValidation";
import type { CodeEvaluationResponse, SearchAlgorithm, SearchResponse } from "./lib/types";

export function App() {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<SearchAlgorithm>("dijkstra");
  const [gridText, setGridText] = useState(defaultGrid);
  const [graphText, setGraphText] = useState(defaultWeightedGraph);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [codeLoading, setCodeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [codeError, setCodeError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [code, setCode] = useState("");
  const [appTheme, setAppTheme] = useState<"light" | "dark">("dark");
  const [evaluation, setEvaluation] = useState<CodeEvaluationResponse | null>(null);

  const gridError = validateGridText(gridText);
  const graphParse = useMemo(() => parseGraphText(graphText), [graphText]);
  const graphError = graphParse.error;
  const selectedContent = useMemo(
    () => algorithms.find((algorithm) => algorithm.id === selectedAlgorithm) ?? algorithms[0],
    [selectedAlgorithm],
  );
  const usesWeightedGraph = selectedContent.problemKind === "weighted_graph";
  const canRun = usesWeightedGraph ? !graphError : !gridError && Boolean(code.trim());
  const frameCount = result?.trace.length ?? 0;
  const frame = result?.trace[Math.min(frameIndex, Math.max(frameCount - 1, 0))] ?? null;

  useEffect(() => {
    if (!playing || frameCount <= 1) {
      return;
    }

    const timer = window.setInterval(() => {
      setFrameIndex((current) => {
        if (current >= frameCount - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 650);

    return () => window.clearInterval(timer);
  }, [playing, frameCount]);

  async function runSearch(codeOverride?: string, algorithmOverride = selectedAlgorithm): Promise<SearchResponse | null> {
    const algorithmContent = algorithms.find((algorithm) => algorithm.id === algorithmOverride) ?? selectedContent;
    if (algorithmContent.problemKind === "weighted_graph") {
      if (graphError || !graphParse.graph) {
        return null;
      }

      setLoading(true);
      setError(null);
      setCodeError(null);
      setPlaying(false);
      try {
        const nextResult = await fetchWeightedGraphTrace(algorithmOverride, graphParse.graph);
        setResult(nextResult);
        setFrameIndex(0);
        return nextResult;
      } catch (nextError) {
        const message = nextError instanceof Error ? nextError.message : "Unable to run weighted graph algorithm.";
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    }

    const codeToRun = codeOverride ?? code;
    if (gridError || !codeToRun.trim()) {
      return null;
    }

    setLoading(true);
    setError(null);
    setCodeError(null);
    setPlaying(false);
    try {
      const nextResult = await visualizeCode(algorithmOverride, gridText, codeToRun);
      setResult(nextResult);
      setFrameIndex(0);
      return nextResult;
    } catch (nextError) {
      const message = nextError instanceof Error ? nextError.message : "Unable to run submitted code.";
      setError(`${message} Reset code to restore the default implementation.`);
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function loadDefaultCode(algorithm: SearchAlgorithm): Promise<string | null> {
    setCodeError(null);
    try {
      const nextCode = await fetchDefaultCode(algorithm);
      setCode(nextCode);
      setEvaluation(null);
      setError(null);
      return nextCode;
    } catch (nextError) {
      setCodeError(nextError instanceof Error ? nextError.message : "Unable to load default code.");
      return null;
    }
  }

  async function resetDefaultCodeAndRun() {
    const nextCode = await loadDefaultCode(selectedAlgorithm);
    if (nextCode) {
      await runSearch(nextCode);
    }
  }

  async function runCodeEvaluation() {
    if (gridError) {
      return;
    }

    setCodeLoading(true);
    setCodeError(null);
    setError(null);
    setPlaying(false);
    try {
      const nextEvaluation = await evaluateCode(selectedAlgorithm, gridText, code);
      setEvaluation(nextEvaluation);
      const nextResult = await visualizeCode(selectedAlgorithm, gridText, code);
      setResult(nextResult);
      setFrameIndex(Math.max(nextResult.trace.length - 1, 0));
    } catch (nextError) {
      setCodeError(nextError instanceof Error ? nextError.message : "Unable to evaluate code.");
    } finally {
      setCodeLoading(false);
    }
  }

  function selectAlgorithm(algorithm: SearchAlgorithm) {
    const nextContent = algorithms.find((item) => item.id === algorithm) ?? algorithms[0];
    setSelectedAlgorithm(algorithm);
    setResult(null);
    setFrameIndex(0);
    setPlaying(false);
    setEvaluation(null);
    setError(null);
    if (nextContent.liveCode) {
      void loadDefaultCode(algorithm);
    } else {
      setCode("");
    }
  }

  async function stepFromStart() {
    const nextResult = await runSearch();
    if (nextResult) {
      setFrameIndex(Math.min(1, Math.max(nextResult.trace.length - 1, 0)));
    }
  }

  return (
    <main className={`app-shell ${appTheme === "dark" ? "theme-dark" : "theme-light"}`}>
      <header className="topbar">
        <div>
          <p className="eyebrow">Planning Algorithms Explorer</p>
          <h1>Chapter 2: Discrete Planning</h1>
        </div>
        <div className="topbar-actions">
          <nav className="chapter-tabs" aria-label="Chapter tabs">
            <button className="tab active" type="button">Chapter 2</button>
            <button className="tab" type="button" disabled>Chapter 3 planned</button>
            <button className="tab" type="button" disabled>Chapter 4 planned</button>
          </nav>
          <button
            className="theme-toggle"
            type="button"
            aria-label="Toggle app theme"
            onClick={() => setAppTheme((theme) => (theme === "light" ? "dark" : "light"))}
          >
            {appTheme === "light" ? "Dark" : "Light"}
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="left-panel">
          <div className="panel">
            <div className="panel-heading">
              <h2>Algorithms</h2>
              <span className="status-pill">MVP</span>
            </div>
            <AlgorithmSelector algorithms={algorithms} selected={selectedAlgorithm} onSelect={selectAlgorithm} />
            <div className="planned-list" aria-label="Planned topics">
              {plannedTopics.map((topic) => (
                <span key={topic}>{topic}</span>
              ))}
            </div>
          </div>

          {usesWeightedGraph ? (
            <GraphEditor value={graphText} error={graphError} onChange={setGraphText} />
          ) : (
            <GridEditor value={gridText} error={gridError} onChange={setGridText} />
          )}
          <TraceControls
            canRun={canRun}
            loading={loading}
            playing={playing}
            frameIndex={frameIndex}
            frameCount={frameCount}
            onRun={() => void runSearch()}
            onReset={() => {
              setPlaying(false);
              setFrameIndex(0);
            }}
            onPrevious={() => {
              setPlaying(false);
              setFrameIndex((current) => Math.max(0, current - 1));
            }}
            onNext={() => {
              if (frameCount === 0) {
                void stepFromStart();
                return;
              }
              setPlaying(false);
              setFrameIndex((current) => Math.min(frameCount - 1, current + 1));
            }}
            onTogglePlay={() => setPlaying((current) => !current)}
          />
          {error ? <p className="request-error" role="alert">{error}</p> : null}
        </aside>

        <section className="main-column">
          {usesWeightedGraph ? (
            <WeightedGraphVisualization result={result} frame={frame} initialGraph={graphParse.graph} />
          ) : (
            <GridVisualization result={result} frame={frame} gridText={gridText} />
          )}
          {selectedContent.liveCode ? (
            <>
              <LiveCodeEditor
                code={code}
                theme={appTheme}
                loading={codeLoading}
                evaluation={evaluation}
                onChange={(nextCode) => {
                  setCode(nextCode);
                  setEvaluation(null);
                  setError(null);
                }}
                onEvaluate={runCodeEvaluation}
                onReset={() => void resetDefaultCodeAndRun()}
              />
              {codeError ? <p className="request-error" role="alert">{codeError}</p> : null}
            </>
          ) : null}
        </section>
        <InspectorPanel algorithm={selectedContent} result={result} frame={frame} />
      </section>
    </main>
  );
}

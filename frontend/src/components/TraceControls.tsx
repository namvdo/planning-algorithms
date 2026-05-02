import { Pause, Play, RotateCcw, StepBack, StepForward } from "lucide-react";

interface Props {
  canRun: boolean;
  loading: boolean;
  playing: boolean;
  frameIndex: number;
  frameCount: number;
  onRun: () => void;
  onReset: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onTogglePlay: () => void;
}

export function TraceControls({
  canRun,
  loading,
  playing,
  frameIndex,
  frameCount,
  onRun,
  onReset,
  onPrevious,
  onNext,
  onTogglePlay,
}: Props) {
  return (
    <div className="controls" aria-label="Trace controls">
      <button type="button" onClick={onRun} disabled={!canRun || loading}>
        <Play size={16} />
        {loading ? "Running" : "Run"}
      </button>
      <button type="button" onClick={onReset} disabled={frameCount === 0}>
        <RotateCcw size={16} />
        Reset
      </button>
      <button type="button" aria-label="Previous frame" onClick={onPrevious} disabled={frameIndex <= 0}>
        <StepBack size={16} />
      </button>
      <button type="button" aria-label="Next frame" onClick={onNext} disabled={frameIndex >= frameCount - 1}>
        <StepForward size={16} />
      </button>
      <button type="button" onClick={onTogglePlay} disabled={frameCount <= 1}>
        {playing ? <Pause size={16} /> : <Play size={16} />}
        {playing ? "Pause" : "Play"}
      </button>
    </div>
  );
}


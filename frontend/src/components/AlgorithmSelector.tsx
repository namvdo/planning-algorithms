import type { AlgorithmContent } from "../lib/content";
import type { SearchAlgorithm } from "../lib/types";

interface Props {
  algorithms: AlgorithmContent[];
  selected: SearchAlgorithm;
  onSelect: (algorithm: SearchAlgorithm) => void;
}

export function AlgorithmSelector({ algorithms, selected, onSelect }: Props) {
  return (
    <div className="algorithm-list" aria-label="Algorithm selector">
      {algorithms.map((algorithm) => (
        <button
          key={algorithm.id}
          className={algorithm.id === selected ? "algorithm-button active" : "algorithm-button"}
          onClick={() => onSelect(algorithm.id)}
          type="button"
        >
          <span>{algorithm.shortName}</span>
          <small>{algorithm.title}</small>
        </button>
      ))}
    </div>
  );
}


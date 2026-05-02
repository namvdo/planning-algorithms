import katex from "katex";
import { useMemo } from "react";
import "katex/dist/katex.min.css";

interface Props {
  value: string;
}

export function LatexBlock({ value }: Props) {
  const html = useMemo(
    () =>
      katex.renderToString(value, {
        displayMode: true,
        throwOnError: false,
        strict: "ignore",
      }),
    [value],
  );

  return <div className="latex-block" dangerouslySetInnerHTML={{ __html: html }} />;
}


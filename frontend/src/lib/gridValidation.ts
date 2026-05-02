export function validateGridText(gridText: string): string | null {
  const rows = gridText.split("\n").filter((row) => row.length > 0);
  if (rows.length === 0) {
    return "Grid must contain at least one row.";
  }

  const width = rows[0].length;
  if (width === 0) {
    return "Grid rows must not be empty.";
  }

  if (rows.some((row) => row.length !== width)) {
    return "Grid must be rectangular.";
  }

  const text = rows.join("");
  const invalid = text.match(/[^SG.# ]/);
  if (invalid) {
    return `Unsupported character: ${invalid[0]}`;
  }

  if ((text.match(/S/g) ?? []).length !== 1) {
    return "Grid must contain exactly one S start marker.";
  }

  if ((text.match(/G/g) ?? []).length !== 1) {
    return "Grid must contain exactly one G goal marker.";
  }

  return null;
}


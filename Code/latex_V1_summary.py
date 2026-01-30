"""Utilities to convert experiment summaries into LaTeX tables."""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional

SUMMARY_COLUMNS: List[str] = [
    "dataFileName",
    "Problem version",
    "Number of zones",
    "solutionValue",
    "isFeasible",
    "solutionStatus",
    "dualBound",
    "cpuTime",
]

LATEX_HEADERS = (
    ("{Instance}", "l"),
    ("{Solution value}", "S[table-format=7.2]"),
    ("{CPU time (s)}", "S[table-format=7.3]"),
)

NUMERIC_COLUMN_DECIMALS = {
    "solutionValue": 2,
    "cpuTime": 3,
}


def export_csv_summary_to_latex(
    csv_relative_path: str,
    tex_relative_path: Optional[str] = None,
    *,
    caption_text: str = "Summary of experiment runs",
    label_tab: str = "tab:experiment-summary",
) -> Path:
    """Convert the summary CSV (semicolon-separated) into a LaTeX table.

    Parameters
    ----------
    csv_relative_path:
        Path to the CSV file, relative to the repository root.
    tex_relative_path:
        Optional path (relative to the repository root) for the output .tex file.
        Defaults to the CSV path with a .tex extension in the same folder.
    caption_text / label_tab:
        Metadata used in the generated table.

    Returns
    -------
    Path: The absolute path to the generated LaTeX file.
    """

    repo_root = Path(__file__).resolve().parents[1]
    csv_path = _resolve_within_repo(repo_root, csv_relative_path)
    output_path = (
        csv_path.with_suffix(".tex")
        if tex_relative_path is None
        else _resolve_within_repo(repo_root, tex_relative_path)
    )

    rows = _load_summary_rows(csv_path)
    if not rows:
        raise ValueError(f"No data rows found in {csv_relative_path}.")

    table_rows = _prepare_table_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_latex_table(output_path, table_rows, caption_text, label_tab)
    print(f"LaTeX table created at: {output_path}")
    return output_path


def _resolve_within_repo(repo_root: Path, provided_path: str) -> Path:
    candidate = Path(provided_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as err:
        raise ValueError(
            f"Path {provided_path} is outside of the repository root {repo_root}."
        ) from err
    return resolved


def _load_summary_rows(csv_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter=";")
        for line_number, raw_row in enumerate(reader, start=1):
            if not raw_row or not any(cell.strip() for cell in raw_row):
                continue
            stripped = [cell.strip() for cell in raw_row]
            if len(stripped) == len(SUMMARY_COLUMNS):
                mapping = dict(zip(SUMMARY_COLUMNS, stripped))
            elif len(stripped) == len(SUMMARY_COLUMNS) + 1:
                mapping = dict(zip(["logFileName", *SUMMARY_COLUMNS], stripped))
                mapping = {key: mapping[key] for key in SUMMARY_COLUMNS}
            else:
                raise ValueError(
                    f"Unexpected column count ({len(stripped)}) on line {line_number} in {csv_path}."
                )
            rows.append(mapping)
    return rows


def _prepare_table_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, object]]:
    table_rows: List[Dict[str, object]] = []
    for row in rows:
        table_rows.append(
            {
                "dataFileName": _escape_latex(row["dataFileName"]),
                "solutionValue": _coerce_float(row["solutionValue"]),
                "cpuTime": _coerce_float(row["cpuTime"]),
            }
        )
    return table_rows


def _write_latex_table(
    output_path: Path,
    table_rows: List[Dict[str, object]],
    caption_text: str,
    label_tab: str,
) -> None:
    column_spec = " ".join(spec for _, spec in LATEX_HEADERS)
    with output_path.open("w", encoding="utf-8") as texfile:
        texfile.write("\\begin{table}[H] \n")
        texfile.write("\\centering \n")
        texfile.write(f"\\begin{{tabular}}{{{column_spec}}}\n")
        texfile.write("\\toprule \n")
        header_line = " & ".join(header for header, _ in LATEX_HEADERS)
        texfile.write(f"{header_line} \\\\ \n")
        texfile.write("\\midrule \n")

        stats = {key: [] for key in NUMERIC_COLUMN_DECIMALS}
        for row in table_rows:
            stats = _update_stats(stats, row)
            texfile.write(
                f"{row['dataFileName']} & "
                f"{_format_numeric(row['solutionValue'], 'solutionValue')} & "
                f"{_format_numeric(row['cpuTime'], 'cpuTime')} \\\\ \n"
            )

        texfile.write("\\midrule \n")
        texfile.write(
            "Average & "
            f"{_format_numeric(_mean_or_none(stats['solutionValue']), 'solutionValue')} & "
            f"{_format_numeric(_mean_or_none(stats['cpuTime']), 'cpuTime')} \\\\ \n"
        )
        texfile.write("\\bottomrule\n")
        texfile.write("\\end{tabular}\n")
        texfile.write(f"\\caption{{{caption_text}}}\n")
        texfile.write(f"\\label{{{label_tab}}}\n")
        texfile.write("\\end{table}\n\n")


def _update_stats(
    stats: Dict[str, List[float]], row: Dict[str, object]
) -> Dict[str, List[float]]:
    for key in stats:
        value = row[key]
        if value is not None:
            stats[key].append(value)
    return stats


def _coerce_float(value: str) -> Optional[float]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() == "missing":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _escape_latex(text: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "_": "\\_",
        "&": "\\&",
        "%": "\\%",
        "#": "\\#",
        "$": "\\$",
        "{": "\\{",
        "}": "\\}",
    }
    escaped = text
    for old, new in replacements.items():
        escaped = escaped.replace(old, new)
    return escaped


def _format_numeric(value: Optional[float], column_key: str) -> str:
    if value is None:
        return "\\multicolumn{1}{c}{--}"
    decimals = NUMERIC_COLUMN_DECIMALS[column_key]
    return f"{value:.{decimals}f}"


def _mean_or_none(values: Iterable[float]) -> Optional[float]:
    values_list = list(values)
    if not values_list:
        return None
    return mean(values_list)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export CSV summaries to LaTeX tables.")
    parser.add_argument("csv_path", help="Relative path to the summary CSV file.")
    parser.add_argument(
        "--tex-path",
        dest="tex_path",
        help="Optional relative path for the output LaTeX file.",
    )
    parser.add_argument(
        "--caption",
        default="Summary of experiment runs",
        help="Caption text for the LaTeX table.",
    )
    parser.add_argument(
        "--label",
        default="tab:experiment-summary",
        help="Label for referencing the LaTeX table.",
    )

    args = parser.parse_args()
    export_csv_summary_to_latex(
        args.csv_path,
        tex_relative_path=args.tex_path,
        caption_text=args.caption,
        label_tab=args.label,
    )

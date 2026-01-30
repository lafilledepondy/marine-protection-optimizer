"""Generate longtable summaries comparing solutions for multiple zone configurations."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from latex_summary import (
    _coerce_float,
    _escape_latex,
    _load_summary_rows,
    _resolve_within_repo,
)

TABLE_SPEC = "l S[table-format=2.0] S[table-format=1.3] S[table-format=2.0] S[table-format=1.3] S[table-format=2.0] S[table-format=1.3]"
NUMERIC_DECIMALS = {"solution": 2, "cpu": 3}


def export_multi_zone_longtable(
    csv_z3: str,
    csv_z7: str,
    csv_z10: str,
    tex_relative_path: Optional[str] = None,
    *,
    caption_text: str = "Résultats détaillés pour un exemple dummy",
    label_tab: str = "tab:mode2-detailed",
) -> Path:
    """Produce a longtable comparing Z=3, Z=7, and Z=10 results by instance."""

    repo_root = Path(__file__).resolve().parents[1]
    csv_paths = {
        3: _resolve_within_repo(repo_root, csv_z3),
        7: _resolve_within_repo(repo_root, csv_z7),
        10: _resolve_within_repo(repo_root, csv_z10),
    }
    output_path = (
        csv_paths[3].with_name("mode2_longtable.tex")
        if tex_relative_path is None
        else _resolve_within_repo(repo_root, tex_relative_path)
    )

    zone_rows = {
        zone: _load_summary_rows(path)
        for zone, path in csv_paths.items()
    }
    combined = _combine_instances(zone_rows)
    if not combined:
        raise ValueError("Aucune instance exploitable n'a été trouvée dans les CSV fournis.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_longtable(output_path, combined, caption_text, label_tab)
    print(f"Longtable créé dans : {output_path}")
    return output_path


def _combine_instances(
    zone_rows: Dict[int, List[Dict[str, str]]]
) -> Dict[str, Dict[int, Dict[str, Optional[float]]]]:
    combined: Dict[str, Dict[int, Dict[str, Optional[float]]]] = {}
    for zone, rows in zone_rows.items():
        for row in rows:
            zone_value = _coerce_float(row.get("Number of zones"))
            if zone_value is None or int(round(zone_value)) != zone:
                continue
            instance = row["dataFileName"]
            combined.setdefault(instance, {})[zone] = {
                "solution": _coerce_float(row.get("solutionValue")),
                "cpu": _coerce_float(row.get("cpuTime")),
            }
    return combined


def _write_longtable(
    output_path: Path,
    combined: Dict[str, Dict[int, Dict[str, Optional[float]]]],
    caption_text: str,
    label_tab: str,
) -> None:
    instances = sorted(combined.keys())
    with output_path.open("w", encoding="utf-8") as texfile:
        texfile.write(f"\\begin{{longtable}}{{{TABLE_SPEC}}}\n")
        texfile.write(f"\\caption{{{caption_text}}} \\\\ \n")
        texfile.write(f"\\label{{{label_tab}}}\n")
        texfile.write("\\toprule\n")
        texfile.write("{Instance} & \\multicolumn{2}{c}{Z = 3} & \\multicolumn{2}{c}{Z = 7} & \\multicolumn{2}{c}{Z = 10} \\\\ \n")
        texfile.write("\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-7}\n")
        texfile.write(" & {Solution} & {CPU (s)} & {Solution} & {CPU (s)} & {Solution} & {CPU (s)} \\\\ \n")
        texfile.write("\\midrule\n")
        texfile.write("\\endfirsthead\n")
        texfile.write("\\multicolumn{7}{c}{\\bfseries \\tablename\\ \\thetable{} -- suite de la page précédente} \\\\ \n")
        texfile.write("\\toprule\n")
        texfile.write("{Instance} & \\multicolumn{2}{c}{Z = 3} & \\multicolumn{2}{c}{Z = 7} & \\multicolumn{2}{c}{Z = 10} \\\\ \n")
        texfile.write("\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-7}\n")
        texfile.write(" & {Solution} & {CPU (s)} & {Solution} & {CPU (s)} & {Solution} & {CPU (s)} \\\\ \n")
        texfile.write("\\midrule\n")
        texfile.write("\\endhead\n")
        texfile.write("\\midrule \\multicolumn{7}{r}{{Suite page suivante}} \\\\ \n")
        texfile.write("\\endfoot\n")
        texfile.write("\\bottomrule\n")
        texfile.write("\\endlastfoot\n")

        for instance in instances:
            escaped_instance = _escape_latex(instance)
            row_values = combined[instance]
            texfile.write(
                f"{escaped_instance} & "
                f"{_format_entry(row_values, 3, 'solution')} & "
                f"{_format_entry(row_values, 3, 'cpu')} & "
                f"{_format_entry(row_values, 7, 'solution')} & "
                f"{_format_entry(row_values, 7, 'cpu')} & "
                f"{_format_entry(row_values, 10, 'solution')} & "
                f"{_format_entry(row_values, 10, 'cpu')} \\\\ \n"
            )

        texfile.write("\\end{longtable}\n")


def _format_entry(
    row_values: Dict[int, Dict[str, Optional[float]]],
    zone: int,
    metric: str,
) -> str:
    zone_data = row_values.get(zone)
    if not zone_data:
        return "\\multicolumn{1}{c}{--}"
    value = zone_data.get(metric)
    if value is None:
        return "\\multicolumn{1}{c}{--}"
    decimals = NUMERIC_DECIMALS[metric]
    return f"{value:.{decimals}f}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Créer une table longue pour le modèle version 2 (Z = 3, 7, 10)."
    )
    parser.add_argument("csv_z3", help="Chemin (relatif) vers le CSV pour Z = 3.")
    parser.add_argument("csv_z7", help="Chemin (relatif) vers le CSV pour Z = 7.")
    parser.add_argument("csv_z10", help="Chemin (relatif) vers le CSV pour Z = 10.")
    parser.add_argument(
        "--tex-path",
        dest="tex_path",
        help="Chemin (relatif) où sauvegarder le fichier .tex.",
    )
    parser.add_argument(
        "--caption",
        default="Résultats détaillés pour un exemple dummy",
        help="Texte de la légende LaTeX.",
    )
    parser.add_argument(
        "--label",
        default="tab:mode2-detailed",
        help="Label LaTeX pour les références croisées.",
    )

    cli_args = parser.parse_args()
    export_multi_zone_longtable(
        cli_args.csv_z3,
        cli_args.csv_z7,
        cli_args.csv_z10,
        tex_relative_path=cli_args.tex_path,
        caption_text=cli_args.caption,
        label_tab=cli_args.label,
    )

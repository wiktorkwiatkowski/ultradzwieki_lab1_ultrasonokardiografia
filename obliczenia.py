#!/usr/bin/env python3
"""Reads the results computed in obliczenia.xlsx and writes LaTeX tables and
pgfplots data to tabele/. All calculations live in the spreadsheet; this script
only exports them. Requires LibreOffice (soffice) to evaluate the formulas."""

import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
XLSX = HERE / "obliczenia.xlsx"
OUT = HERE / "tabele"

CASES = {
    "prawidlowa": "Prawidłowa praca zastawki",
    "male_zwezenie": "Małe zwężenie zastawki dwudzielnej",
    "ciasne_zwezenie": "Ciasne zwężenie zastawki dwudzielnej",
    "niedomykalnosc": "Niedomykalność zastawki dwudzielnej",
    "wypadanie": "Wypadanie zastawki dwudzielnej",
    "wypadanie_mezotel": "Wypadanie zastawki typu mezotelesystolicznego",
}

MATERIALS = {"metal": "Metal", "plastik": "Plastik", "siatka": "Siatka", "guma": "Guma"}

# Case sheet layout: rows 1-3 are the title and headers, then one row per point
# (Lp., t, real dy, real y, then dy and y for each material), then the RMSE row.
HEADER_ROWS = 3
FIRST_MATERIAL_COL = 4


def find_soffice():
    for cand in [
        shutil.which("soffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]:
        if cand and Path(cand).exists():
            return cand
    raise SystemExit("LibreOffice (soffice) not found, install it from libreoffice.org")


def read_sheets():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Separate profile so the export also works while LibreOffice is open.
        # Filter options: comma, quote, UTF-8, en-US numbers, raw values, all sheets.
        subprocess.run(
            [
                find_soffice(),
                f"-env:UserInstallation={(tmp / 'profile').as_uri()}",
                "--headless",
                "--convert-to",
                "csv:Text - txt - csv (StarCalc):44,34,76,1,,1033,false,false,false,false,false,-1",
                "--outdir",
                str(tmp),
                str(XLSX),
            ],
            check=True,
            capture_output=True,
        )
        return {
            p.stem.removeprefix(f"{XLSX.stem}-"): list(csv.reader(p.open(encoding="utf-8")))
            for p in tmp.glob("*.csv")
        }


def fmt(x):
    return f"{x:.2f}".replace(".", ",")


def case_data(rows):
    points = rows[HEADER_ROWS:-1]
    rmse = {m: float(rows[-1][FIRST_MATERIAL_COL + 2 * g]) for g, m in enumerate(MATERIALS)}
    return points, rmse


def case_table(points, rmse):
    groups = ["Rzeczywiste"] + list(MATERIALS.values())
    head = " & ".join(f"\\multicolumn{{2}}{{c}}{{{g}}}" for g in groups)
    sub = " & ".join(["$\\Delta y$ & $y$"] * len(groups))
    lines = [
        f"\\begin{{tabular}}{{cc{' cc' * len(groups)}}}",
        "\\toprule",
        f"Lp. & $t$ [ms] & {head} \\\\",
        f" &  & {sub} \\\\",
        "\\midrule",
    ]
    for p in points:
        lines.append(" & ".join(p) + " \\\\")
    lines.append("\\midrule")
    errs = " & ".join(f"\\multicolumn{{2}}{{c}}{{{fmt(rmse[m])}}}" for m in MATERIALS)
    lines.append(f"\\multicolumn{{4}}{{c}}{{RMSE [mm]}} & {errs} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def bold_min(values):
    best = min(values)
    return [f"\\textbf{{{fmt(v)}}}" if v == best else fmt(v) for v in values]


def summary(rows):
    lines = [
        f"\\begin{{tabular}}{{l{'c' * len(MATERIALS)}}}",
        "\\toprule",
        "Przypadek & " + " & ".join(MATERIALS.values()) + " \\\\",
        "\\midrule",
    ]
    body = rows[2:-1]
    assert [r[0] for r in body] == list(CASES.values()), "unexpected rows in Podsumowanie"
    for r in body:
        lines.append(f"{r[0]} & " + " & ".join(bold_min([float(v) for v in r[1:]])) + " \\\\")
    lines.append("\\midrule")
    lines.append("Średni RMSE & " + " & ".join(bold_min([float(v) for v in rows[-1][1:]])) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def plot_data(points):
    lines = ["t " + " ".join(["rzecz"] + list(MATERIALS))]
    for p in points:
        lines.append(" ".join([p[1], p[3]] + p[FIRST_MATERIAL_COL + 1 :: 2]))
    return "\n".join(lines) + "\n"


def main():
    sheets = read_sheets()
    OUT.mkdir(exist_ok=True)
    for c in CASES:
        points, rmse = case_data(sheets[c])
        (OUT / f"{c}.tex").write_text(case_table(points, rmse))
        (OUT / f"{c}.dat").write_text(plot_data(points))
    (OUT / "rmse.tex").write_text(summary(sheets["Podsumowanie"]))


if __name__ == "__main__":
    main()

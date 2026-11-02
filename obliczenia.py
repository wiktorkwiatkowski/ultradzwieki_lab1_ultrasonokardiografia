#!/usr/bin/env python3
"""Reads the results computed in obliczenia.xlsx and writes LaTeX tables and chart
images to tabele/. All calculations and charts live in the spreadsheet; this script
only exports them. Requires LibreOffice (soffice) to read the workbook and poppler
(pdftoppm) to render the charts."""

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
# (Lp., t, real dy, real y, dy and y for each material, deviation of y from the
# real y for each material), then the RMSE row.
HEADER_ROWS = 3
FIRST_MATERIAL_COL = 4
# Columns further right are helpers for the chart, not part of the table.
TABLE_COLS = 16
# Chart position on a case sheet's printed page, in points: x, y, width, height.
CHART_BOX = (53, 247, 526.89, 241.3)
CHART_DPI = 300


def find_soffice():
    for cand in [
        shutil.which("soffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]:
        if cand and Path(cand).exists():
            return cand
    raise SystemExit("LibreOffice (soffice) not found, install it from libreoffice.org")


def convert(target, outdir):
    # Separate profile so the export also works while LibreOffice is open.
    subprocess.run(
        [
            find_soffice(),
            f"-env:UserInstallation={(outdir / 'profile').as_uri()}",
            "--headless",
            "--convert-to",
            target,
            "--outdir",
            str(outdir),
            str(XLSX),
        ],
        check=True,
        capture_output=True,
    )


def read_sheets():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Filter options: comma, quote, UTF-8, en-US numbers, raw values, all sheets.
        convert("csv:Text - txt - csv (StarCalc):44,34,76,1,,1033,false,false,false,false,false,-1", tmp)
        return {
            p.stem.removeprefix(f"{XLSX.stem}-"): list(csv.reader(p.open(encoding="utf-8")))
            for p in tmp.glob("*.csv")
        }


def export_charts():
    # Rendered to images because a cropped PDF page keeps the sheet's table as
    # invisible, selectable text in the report.
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise SystemExit("pdftoppm not found, install poppler (poppler-utils)")
    x, y, w, h = (round(v * CHART_DPI / 72) for v in CHART_BOX)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        convert("pdf", tmp)
        # One page per sheet: Podsumowanie first, then the cases in CASES order.
        for page, c in enumerate(CASES, start=2):
            subprocess.run(
                [pdftoppm, "-png", "-singlefile", "-r", str(CHART_DPI), "-f", str(page), "-l", str(page),
                 "-x", str(x), "-y", str(y), "-W", str(w), "-H", str(h),
                 str(tmp / f"{XLSX.stem}.pdf"), str(OUT / f"wykres_{c}")],
                check=True,
            )


def fmt(x):
    return f"{x:.2f}".replace(".", ",")


def case_data(rows):
    points = [r[:TABLE_COLS] for r in rows[HEADER_ROWS:-1]]
    rmse = {m: float(rows[-1][FIRST_MATERIAL_COL + 2 * g]) for g, m in enumerate(MATERIALS)}
    return points, rmse


def case_table(points, rmse):
    materials = " & ".join(MATERIALS.values())
    lines = [
        "\\begin{tabular}{cc c cccc}",
        "\\toprule",
        "Lp. & Czas [ms] & \\multicolumn{5}{c}{$y$ [mm]} \\\\",
        "\\cmidrule(lr){3-7}",
        f" &  & Rzeczywiste & {materials} \\\\",
        "\\midrule",
    ]
    for p in points:
        # Lp. and t, then y (every other column, skipping dy).
        lines.append(" & ".join(p[:2] + p[3:12:2]) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "", "\\bigskip", ""]
    lines += [
        "\\begin{tabular}{cc cccc}",
        "\\toprule",
        "Lp. & Czas [ms] & \\multicolumn{4}{c}{Odchylenie [mm]} \\\\",
        "\\cmidrule(lr){3-6}",
        f" &  & {materials} \\\\",
        "\\midrule",
    ]
    for p in points:
        lines.append(" & ".join(p[:2] + p[12:]) + " \\\\")
    lines.append("\\midrule")
    errs = " & ".join(bold_min([rmse[m] for m in MATERIALS]))
    lines.append(f"\\multicolumn{{2}}{{c}}{{RMSE [mm]}} & {errs} \\\\")
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


def main():
    sheets = read_sheets()
    OUT.mkdir(exist_ok=True)
    for c in CASES:
        points, rmse = case_data(sheets[c])
        (OUT / f"{c}.tex").write_text(case_table(points, rmse))
    (OUT / "rmse.tex").write_text(summary(sheets["Podsumowanie"]))
    export_charts()


if __name__ == "__main__":
    main()

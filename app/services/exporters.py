"""
Epic 9 - Unified multi-format export engine.
Every function takes a DataFrame and an output path, and writes the file.
"""
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def export_csv(df: pd.DataFrame, path: str, sep: str = ",") -> str:
    df.to_csv(path, sep=sep, index=False)
    return path


def export_txt(df: pd.DataFrame, path: str, sep: str = "\t") -> str:
    df.to_csv(path, sep=sep, index=False)
    return path


def export_excel(df: pd.DataFrame, path: str) -> str:
    df.to_excel(path, index=False, engine="openpyxl")
    return path


def export_pdf(df: pd.DataFrame, path: str, max_rows: int = 500) -> str:
    """
    Renders the DataFrame as a simple table in a PDF.
    Truncates to max_rows to keep the PDF generation fast/reasonable;
    for very large exports prefer csv/excel.
    """
    truncated = df.head(max_rows)
    data = [list(truncated.columns)] + truncated.astype(str).values.tolist()

    doc = SimpleDocTemplate(path, pagesize=landscape(A4))
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ]))
    doc.build([table])
    return path


EXPORTERS = {
    "csv": export_csv,
    "txt": export_txt,
    "xlsx": export_excel,
    "pdf": export_pdf,
}


def export(df: pd.DataFrame, path: str, fmt: str, sep: str = None) -> str:
    if fmt not in EXPORTERS:
        raise ValueError(f"Unsupported export format: {fmt}")
    if fmt in {"csv", "txt"} and sep is not None:
        return EXPORTERS[fmt](df, path, sep=sep)
    return EXPORTERS[fmt](df, path)

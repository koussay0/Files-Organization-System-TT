"""
Unified loader: turns an uploaded csv/txt/xls/xlsx file into a pandas DataFrame.

Epic 1 - File Ingestion & Basic Stats.
"""
import csv
import io
import pandas as pd
import pdfplumber

SUPPORTED_EXTENSIONS = {"csv", "txt", "xls", "xlsx", "pdf"}


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def sniff_delimiter(sample: str) -> str:
    """Best-effort delimiter detection for csv/txt files."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","


def load_dataframe(file_storage) -> pd.DataFrame:
    """
    Load a Werkzeug FileStorage object into a DataFrame regardless of
    whether it's csv, txt, xls, or xlsx.
    """
    filename = file_storage.filename
    ext = get_extension(filename)

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}")

    if ext in ("xls", "xlsx"):
        return pd.read_excel(file_storage)

    if ext == "pdf":
        return load_pdf(file_storage)

    # csv / txt: sniff delimiter first
    raw_bytes = file_storage.read()
    file_storage.seek(0)
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    sample = text[:4096]
    delimiter = sniff_delimiter(sample)

    return pd.read_csv(io.StringIO(text), sep=delimiter, engine="python")


def load_pdf(file_storage):
    file_storage.seek(0)
    with pdfplumber.open(file_storage.stream) as pdf:
        if not pdf.pages:
            return pd.DataFrame()
        first_page = pdf.pages[0]
        tables = first_page.extract_tables()
        if tables:
            table = tables[0]
            if len(table) > 1:
                headers = [str(cell or f"col{i}") for i, cell in enumerate(table[0])]
                rows = [[cell or "" for cell in row] for row in table[1:]]
                return pd.DataFrame(rows, columns=headers)

        text = first_page.extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return pd.DataFrame()

        if any(delimiter in lines[0] for delimiter in [",", "\t", ";", "|"]):
            delimiter = sniff_delimiter(lines[0])
            data = [line.split(delimiter) for line in lines]
            if len(data) > 1:
                headers = [str(cell or f"col{i}") for i, cell in enumerate(data[0])]
                return pd.DataFrame([row for row in data[1:]], columns=headers)

        return pd.DataFrame({"text": lines})


def basic_stats(df: pd.DataFrame) -> dict:
    """Epic 1: row/column counts."""
    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns.astype(str)),
    }

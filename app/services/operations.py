"""
Core data-manipulation operations, one function per backlog Epic.
Every function takes a DataFrame in and returns a DataFrame (or dict) out,
so they can be unit-tested independently of Flask.
"""
import pandas as pd


# ---------------------------------------------------------------------------
# Epic 2 - Sorting
# ---------------------------------------------------------------------------
def sort_by_column(df: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
    return df.sort_values(by=column, ascending=ascending).reset_index(drop=True)


def sort_by_full_row(df: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
    return df.sort_values(by=list(df.columns), ascending=ascending).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Epic 3 - Duplicate detection & removal
# ---------------------------------------------------------------------------
def find_duplicates(df: pd.DataFrame, subset=None) -> pd.DataFrame:
    """
    Returns a summary DataFrame: each distinct value/row that appears more
    than once, plus its repetition count. subset=None means "full row".
    """
    grouped = df.groupby(subset if subset else list(df.columns)).size()
    grouped = grouped[grouped > 1].reset_index(name="repetition_count")
    return grouped.sort_values("repetition_count", ascending=False).reset_index(drop=True)


def remove_duplicates(df: pd.DataFrame, subset=None) -> pd.DataFrame:
    return df.drop_duplicates(subset=subset).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Epic 4 - Sequence detection (numeric incrementing series, row- or column-wise)
# ---------------------------------------------------------------------------
def detect_sequences(values, min_length: int = 3):
    """
    Given an ordered list of values, find runs of consecutive integers
    (e.g. 100,101,102,103) of at least `min_length`.
    Returns a list of dicts: {"start": v0, "end": vn, "length": n}.
    """
    sequences = []
    run = []

    def flush():
        if len(run) >= min_length:
            sequences.append({"start": run[0], "end": run[-1], "length": len(run)})

    prev = None
    for v in values:
        try:
            v_num = int(v)
        except (ValueError, TypeError):
            flush()
            run.clear()
            prev = None
            continue

        if prev is not None and v_num == prev + 1:
            run.append(v_num)
        else:
            flush()
            run = [v_num]
        prev = v_num

    flush()
    return sequences


# ---------------------------------------------------------------------------
# Epic 5 - File splitting
# ---------------------------------------------------------------------------
def split_by_num_files(df: pd.DataFrame, n_files: int):
    return [chunk.reset_index(drop=True) for chunk in _split_even(df, n_files)]


def _split_even(df, n_files):
    n_rows = len(df)
    base = n_rows // n_files
    remainder = n_rows % n_files
    start = 0
    for i in range(n_files):
        size = base + (1 if i < remainder else 0)
        yield df.iloc[start:start + size]
        start += size


def split_by_rows_per_file(df: pd.DataFrame, rows_per_file: int):
    return [
        df.iloc[i:i + rows_per_file].reset_index(drop=True)
        for i in range(0, len(df), rows_per_file)
    ]


# ---------------------------------------------------------------------------
# Epic 6 - Template-based reformatting
# ---------------------------------------------------------------------------
def apply_template(df: pd.DataFrame, source_column: str, template_fields: list, separator: str = "|") -> pd.DataFrame:
    """
    template_fields: ordered list where each item is either:
      - a literal string (e.g. "Param1"), or
      - the special marker "__SOURCE__" meaning "insert the source column value here"
    Example: ["Param1", "Param2", "__SOURCE__", "Param3"]
    """
    def build_row(value):
        return separator.join(
            str(value) if field == "__SOURCE__" else field
            for field in template_fields
        )

    result = df[[source_column]].copy()
    result["formatted"] = df[source_column].apply(build_row)
    return result[["formatted"]]


# ---------------------------------------------------------------------------
# Epic 7 - Column-level operations (string injection/removal, math)
# ---------------------------------------------------------------------------
def inject_string(df: pd.DataFrame, column: str, text: str, position: str = "append") -> pd.DataFrame:
    df = df.copy()
    if position == "append":
        df[column] = df[column].astype(str) + text
    else:  # prepend
        df[column] = text + df[column].astype(str)
    return df


def remove_string(df: pd.DataFrame, column: str, text: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].astype(str).str.replace(text, "", regex=False)
    return df


def apply_math(df: pd.DataFrame, column: str, operator: str, operand: float) -> pd.DataFrame:
    df = df.copy()
    col = pd.to_numeric(df[column], errors="coerce")

    if operator == "+":
        df[column] = col + operand
    elif operator == "-":
        df[column] = col - operand
    elif operator == "*":
        df[column] = col * operand
    elif operator == "/":
        if operand == 0:
            raise ValueError("Division by zero is not allowed.")
        df[column] = col / operand
    else:
        raise ValueError(f"Unsupported operator: {operator}")
    return df


# ---------------------------------------------------------------------------
# Epic 8 - Column reorder / add / remove / extract
# ---------------------------------------------------------------------------
def reorder_columns(df: pd.DataFrame, new_order: list) -> pd.DataFrame:
    return df[new_order]


def add_column(df: pd.DataFrame, name: str, value, position: int) -> pd.DataFrame:
    df = df.copy()
    df.insert(loc=position, column=name, value=value)
    return df


def remove_column(df: pd.DataFrame, position: int) -> pd.DataFrame:
    df = df.copy()
    col_name = df.columns[position]
    return df.drop(columns=[col_name])


def extract_columns(df: pd.DataFrame, positions: list) -> pd.DataFrame:
    cols = [df.columns[p] for p in positions]
    return df[cols]


def _normalize_column_list(columns, fallback_columns, *, allow_empty=False, field_name="column"):
    """Trim whitespace and discard empty entries while keeping a safe fallback."""
    if columns is None:
        return list(fallback_columns)

    normalized = []
    for col in columns:
        if col is None:
            continue
        text = str(col).strip()
        if text:
            normalized.append(text)

    if not normalized:
        if allow_empty:
            return list(fallback_columns)
        raise ValueError(f"At least one valid {field_name} name is required.")

    missing = [col for col in normalized if col not in fallback_columns]
    if missing:
        raise ValueError(f"Unknown {field_name}(s): {', '.join(missing)}")

    return normalized


# ---------------------------------------------------------------------------
# Epic 10 - Two-file comparison
# ---------------------------------------------------------------------------
def compare_files(df1: pd.DataFrame, df2: pd.DataFrame, subset=None):
    """
    Returns a dict with three DataFrames:
      - in_both:      rows present in both files
      - only_in_f1:   rows only in file 1
      - only_in_f2:   rows only in file 2
    subset=None means "compare on full row".
    """
    if subset is None:
        cols = list(df1.columns)
    else:
        cols = _normalize_column_list(subset, list(df1.columns), field_name="comparison column")

    merged = df1[cols].merge(df2[cols], how="outer", indicator=True, on=cols)

    in_both = merged[merged["_merge"] == "both"].drop(columns="_merge").reset_index(drop=True)
    only_in_f1 = merged[merged["_merge"] == "left_only"].drop(columns="_merge").reset_index(drop=True)
    only_in_f2 = merged[merged["_merge"] == "right_only"].drop(columns="_merge").reset_index(drop=True)

    return {"in_both": in_both, "only_in_f1": only_in_f1, "only_in_f2": only_in_f2}


# ---------------------------------------------------------------------------
# Epic 11 - File merging
# ---------------------------------------------------------------------------
def merge_files(df1: pd.DataFrame, df2: pd.DataFrame, columns_f1: list, columns_f2: list) -> pd.DataFrame:
    """Simple side-by-side column merge (not a SQL-style join on keys)."""
    part1_cols = _normalize_column_list(columns_f1, list(df1.columns), allow_empty=True, field_name="column")
    part2_cols = _normalize_column_list(columns_f2, list(df2.columns), allow_empty=True, field_name="column")

    part1 = df1[part1_cols].reset_index(drop=True)
    part2 = df2[part2_cols].reset_index(drop=True)
    return pd.concat([part1, part2], axis=1)

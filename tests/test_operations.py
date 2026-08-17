"""
Comprehensive unit tests for TT File Processor.
Tests cover: operations, file loading, exporters, and edge cases.
Run with: pytest tests/test_operations.py -v
"""
import pandas as pd
import sys
import os
import io
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import operations as ops
from app.services import file_loader as fl
from app.services import exporters as exp


# ============================================================================
# EPIC 2: SORTING TESTS
# ============================================================================

def test_sort_by_column_ascending():
    """Test sorting a single column in ascending order."""
    df = pd.DataFrame({"a": [3, 1, 2], "b": ["x", "y", "z"]})
    result = ops.sort_by_column(df, "a", ascending=True)
    assert result["a"].tolist() == [1, 2, 3]
    assert result["b"].tolist() == ["y", "z", "x"]


def test_sort_by_column_descending():
    """Test sorting a single column in descending order."""
    df = pd.DataFrame({"a": [3, 1, 2]})
    result = ops.sort_by_column(df, "a", ascending=False)
    assert result["a"].tolist() == [3, 2, 1]


def test_sort_by_column_with_strings():
    """Test sorting string column alphabetically."""
    df = pd.DataFrame({"name": ["charlie", "alice", "bob"]})
    result = ops.sort_by_column(df, "name", ascending=True)
    assert result["name"].tolist() == ["alice", "bob", "charlie"]


def test_sort_by_full_row():
    """Test sorting by multiple columns (full row)."""
    df = pd.DataFrame({"a": [2, 1, 1], "b": [2, 1, 2]})
    result = ops.sort_by_full_row(df, ascending=True)
    assert result["a"].tolist() == [1, 1, 2]


def test_sort_preserves_dataframe_shape():
    """Test that sorting preserves DataFrame dimensions."""
    df = pd.DataFrame({"a": [3, 1, 2], "b": [6, 4, 5], "c": [9, 7, 8]})
    result = ops.sort_by_column(df, "a")
    assert result.shape == df.shape


# ============================================================================
# EPIC 3: DUPLICATE DETECTION & REMOVAL
# ============================================================================

def test_find_duplicates_full_row():
    """Test finding duplicate rows (full row match)."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    summary = ops.find_duplicates(df)
    assert len(summary) == 1
    assert summary.iloc[0]["repetition_count"] == 2


def test_find_duplicates_by_column():
    """Test finding duplicates based on specific column."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "y", "z"]})
    summary = ops.find_duplicates(df, subset=["a"])
    assert len(summary) == 1
    assert summary.iloc[0]["repetition_count"] == 2


def test_find_duplicates_multiple_groups():
    """Test finding multiple duplicate groups."""
    df = pd.DataFrame({"a": [1, 1, 2, 2, 3]})
    summary = ops.find_duplicates(df, subset=["a"])
    assert len(summary) == 2
    assert summary.iloc[0]["repetition_count"] == 2  # sorted descending


def test_find_duplicates_no_duplicates():
    """Test when there are no duplicates."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    summary = ops.find_duplicates(df)
    assert len(summary) == 0


def test_remove_duplicates_full_row():
    """Test removing duplicate rows (full row)."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    result = ops.remove_duplicates(df)
    assert len(result) == 2


def test_remove_duplicates_by_column():
    """Test removing duplicates based on column."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "y", "z"]})
    result = ops.remove_duplicates(df, subset=["a"])
    assert len(result) == 2
    assert result["a"].tolist() == [1, 2]


def test_remove_duplicates_preserves_first():
    """Test that first occurrence is kept."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["first", "second", "third"]})
    result = ops.remove_duplicates(df, subset=["a"])
    assert result[result["a"] == 1]["b"].iloc[0] == "first"


# ============================================================================
# EPIC 4: SEQUENCE DETECTION
# ============================================================================

def test_detect_sequences_simple():
    """Test detecting a simple numeric sequence."""
    values = [1, 2, 3, 7, 8, 20]
    sequences = ops.detect_sequences(values, min_length=3)
    assert len(sequences) == 1
    assert sequences[0] == {"start": 1, "end": 3, "length": 3}


def test_detect_sequences_multiple():
    """Test detecting multiple sequences."""
    values = [1, 2, 3, 5, 6, 7, 8]
    sequences = ops.detect_sequences(values, min_length=3)
    assert len(sequences) == 2


def test_detect_sequences_below_min_length():
    """Test that short sequences are ignored."""
    values = [1, 2, 5, 6, 7, 8, 9]
    sequences = ops.detect_sequences(values, min_length=5)
    assert len(sequences) == 1
    assert sequences[0]["length"] == 5


def test_detect_sequences_with_strings():
    """Test sequence detection with string numbers."""
    values = ["1", "2", "3"]
    sequences = ops.detect_sequences(values, min_length=3)
    assert len(sequences) == 1


def test_detect_sequences_no_sequences():
    """Test when there are no sequences."""
    values = [1, 3, 5, 7, 9]
    sequences = ops.detect_sequences(values, min_length=3)
    assert len(sequences) == 0


# ============================================================================
# EPIC 5: FILE SPLITTING
# ============================================================================

def test_split_by_num_files():
    """Test splitting DataFrame into N equal chunks."""
    df = pd.DataFrame({"a": range(10)})
    chunks = ops.split_by_num_files(df, 3)
    assert len(chunks) == 3
    assert len(chunks[0]) == 4
    assert len(chunks[1]) == 3
    assert len(chunks[2]) == 3


def test_split_by_num_files_preserves_data():
    """Test that splitting preserves all data."""
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    chunks = ops.split_by_num_files(df, 2)
    reconstructed = pd.concat(chunks, ignore_index=True)
    assert len(reconstructed) == len(df)
    assert reconstructed["a"].tolist() == df["a"].tolist()


def test_split_by_rows_per_file():
    """Test splitting DataFrame by rows per file."""
    df = pd.DataFrame({"a": range(10)})
    chunks = ops.split_by_rows_per_file(df, 3)
    assert len(chunks) == 4
    assert len(chunks[0]) == 3
    assert len(chunks[-1]) == 1


def test_split_single_file():
    """Test splitting into 1 file."""
    df = pd.DataFrame({"a": range(5)})
    chunks = ops.split_by_num_files(df, 1)
    assert len(chunks) == 1
    assert len(chunks[0]) == 5


# ============================================================================
# EPIC 6: TEMPLATE-BASED REFORMATTING
# ============================================================================

def test_apply_template_with_source():
    """Test applying a template with source value insertion."""
    df = pd.DataFrame({"id": ["A", "B", "C"]})
    template = ["Prefix", "__SOURCE__", "Suffix"]
    result = ops.apply_template(df, "id", template, separator=":")
    assert result.iloc[0, 0] == "Prefix:A:Suffix"
    assert result.iloc[1, 0] == "Prefix:B:Suffix"


def test_apply_template_custom_separator():
    """Test template with custom separator."""
    df = pd.DataFrame({"id": ["X"]})
    template = ["A", "B", "__SOURCE__"]
    result = ops.apply_template(df, "id", template, separator="|")
    assert result.iloc[0, 0] == "A|B|X"


def test_apply_template_no_source():
    """Test template without source value."""
    df = pd.DataFrame({"id": ["A", "B"]})
    template = ["Header1", "Header2", "Header3"]
    result = ops.apply_template(df, "id", template, separator=",")
    assert result.iloc[0, 0] == "Header1,Header2,Header3"


# ============================================================================
# EPIC 7: COLUMN-LEVEL OPERATIONS
# ============================================================================

def test_inject_string_append():
    """Test appending string to column values."""
    df = pd.DataFrame({"a": ["hello", "world"]})
    result = ops.inject_string(df, "a", "_suffix", position="append")
    assert result["a"].tolist() == ["hello_suffix", "world_suffix"]


def test_inject_string_prepend():
    """Test prepending string to column values."""
    df = pd.DataFrame({"a": ["hello", "world"]})
    result = ops.inject_string(df, "a", "prefix_", position="prepend")
    assert result["a"].tolist() == ["prefix_hello", "prefix_world"]


def test_remove_string():
    """Test removing string from column values."""
    df = pd.DataFrame({"a": ["hello-world", "foo-bar"]})
    result = ops.remove_string(df, "a", "-")
    assert result["a"].tolist() == ["helloworld", "foobar"]


def test_apply_math_addition():
    """Test addition operation on column."""
    df = pd.DataFrame({"a": [10, 20, 30]})
    result = ops.apply_math(df, "a", "+", 5)
    assert result["a"].tolist() == [15, 25, 35]


def test_apply_math_subtraction():
    """Test subtraction operation on column."""
    df = pd.DataFrame({"a": [10, 20, 30]})
    result = ops.apply_math(df, "a", "-", 5)
    assert result["a"].tolist() == [5, 15, 25]


def test_apply_math_multiplication():
    """Test multiplication operation on column."""
    df = pd.DataFrame({"a": [2, 3, 4]})
    result = ops.apply_math(df, "a", "*", 2)
    assert result["a"].tolist() == [4, 6, 8]


def test_apply_math_division():
    """Test division operation on column."""
    df = pd.DataFrame({"a": [10, 20, 30]})
    result = ops.apply_math(df, "a", "/", 2)
    assert result["a"].tolist() == [5.0, 10.0, 15.0]


def test_apply_math_division_by_zero():
    """Test that division by zero raises error."""
    df = pd.DataFrame({"a": [10, 20]})
    try:
        ops.apply_math(df, "a", "/", 0)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Division by zero" in str(e)


def test_apply_math_invalid_operator():
    """Test that invalid operator raises error."""
    df = pd.DataFrame({"a": [10, 20]})
    try:
        ops.apply_math(df, "a", "^", 2)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Unsupported operator" in str(e)


# ============================================================================
# EPIC 8: COLUMN OPERATIONS
# ============================================================================

def test_reorder_columns():
    """Test reordering columns."""
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    result = ops.reorder_columns(df, ["c", "a", "b"])
    assert list(result.columns) == ["c", "a", "b"]


def test_add_column():
    """Test adding a new column."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = ops.add_column(df, "c", [5, 6], position=1)
    assert list(result.columns) == ["a", "c", "b"]
    assert result["c"].tolist() == [5, 6]


def test_add_column_at_start():
    """Test adding column at the start."""
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = ops.add_column(df, "x", [9], position=0)
    assert list(result.columns) == ["x", "a", "b"]


def test_add_column_at_end():
    """Test adding column at the end."""
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = ops.add_column(df, "c", [3], position=2)
    assert list(result.columns) == ["a", "b", "c"]


def test_remove_column():
    """Test removing a column by position."""
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    result = ops.remove_column(df, 1)
    assert list(result.columns) == ["a", "c"]


def test_extract_columns():
    """Test extracting specific columns."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    result = ops.extract_columns(df, [0, 2])
    assert list(result.columns) == ["a", "c"]
    assert len(result) == 2


# ============================================================================
# EPIC 10: TWO-FILE COMPARISON
# ============================================================================

def test_compare_files_basic():
    """Test comparing two files for common and unique rows."""
    df1 = pd.DataFrame({"id": [1, 2, 3]})
    df2 = pd.DataFrame({"id": [2, 3, 4]})
    result = ops.compare_files(df1, df2)
    assert result["in_both"]["id"].tolist() == [2, 3]
    assert result["only_in_f1"]["id"].tolist() == [1]
    assert result["only_in_f2"]["id"].tolist() == [4]


def test_compare_files_by_column():
    """Test comparing files by specific column."""
    df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    df2 = pd.DataFrame({"id": [2, 3, 4], "name": ["x", "y", "z"]})
    result = ops.compare_files(df1, df2, subset=["id"])
    assert len(result["in_both"]) == 2


def test_compare_files_no_matches():
    """Test comparing files with no common rows."""
    df1 = pd.DataFrame({"id": [1, 2, 3]})
    df2 = pd.DataFrame({"id": [4, 5, 6]})
    result = ops.compare_files(df1, df2)
    assert len(result["in_both"]) == 0
    assert len(result["only_in_f1"]) == 3
    assert len(result["only_in_f2"]) == 3


def test_compare_files_all_match():
    """Test comparing identical files."""
    df1 = pd.DataFrame({"id": [1, 2, 3]})
    df2 = pd.DataFrame({"id": [1, 2, 3]})
    result = ops.compare_files(df1, df2)
    assert len(result["in_both"]) == 3
    assert len(result["only_in_f1"]) == 0
    assert len(result["only_in_f2"]) == 0


# ============================================================================
# EPIC 11: FILE MERGING
# ============================================================================

def test_merge_files_basic():
    """Test merging two files side by side."""
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"b": [3, 4]})
    result = ops.merge_files(df1, df2, ["a"], ["b"])
    assert list(result.columns) == ["a", "b"]
    assert result["b"].tolist() == [3, 4]


def test_merge_files_multiple_columns():
    """Test merging with multiple columns from each file."""
    df1 = pd.DataFrame({"a": [1, 2], "b": [5, 6]})
    df2 = pd.DataFrame({"c": [3, 4], "d": [7, 8]})
    result = ops.merge_files(df1, df2, ["a", "b"], ["c", "d"])
    assert list(result.columns) == ["a", "b", "c", "d"]


def test_merge_files_preserves_data():
    """Test that merging preserves all data."""
    df1 = pd.DataFrame({"x": [10, 20, 30]})
    df2 = pd.DataFrame({"y": [40, 50, 60]})
    result = ops.merge_files(df1, df2, ["x"], ["y"])
    assert len(result) == 3
    assert result["x"].tolist() == [10, 20, 30]


# ============================================================================
# FILE LOADER TESTS (EPIC 1)
# ============================================================================

def test_get_extension():
    """Test extracting file extension."""
    assert fl.get_extension("data.csv") == "csv"
    assert fl.get_extension("file.XLSX") == "xlsx"
    assert fl.get_extension("doc.txt") == "txt"


def test_sniff_delimiter_comma():
    """Test detecting comma delimiter."""
    sample = "a,b,c\n1,2,3"
    delimiter = fl.sniff_delimiter(sample)
    assert delimiter == ","


def test_sniff_delimiter_tab():
    """Test detecting tab delimiter."""
    sample = "a\tb\tc\n1\t2\t3"
    delimiter = fl.sniff_delimiter(sample)
    assert delimiter == "\t"


def test_sniff_delimiter_semicolon():
    """Test detecting semicolon delimiter."""
    sample = "a;b;c\n1;2;3"
    delimiter = fl.sniff_delimiter(sample)
    assert delimiter == ";"


def test_basic_stats():
    """Test basic statistics on DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    stats = fl.basic_stats(df)
    assert stats["n_rows"] == 3
    assert stats["n_columns"] == 2
    assert stats["columns"] == ["a", "b"]


def test_basic_stats_empty():
    """Test basic statistics on empty DataFrame."""
    df = pd.DataFrame()
    stats = fl.basic_stats(df)
    assert stats["n_rows"] == 0
    assert stats["n_columns"] == 0


# ============================================================================
# EXPORTER TESTS (EPIC 9)
# ============================================================================

def test_export_csv():
    """Test exporting to CSV format."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        exp.export_csv(df, path)
        assert os.path.exists(path)
        loaded = pd.read_csv(path)
        assert loaded["a"].tolist() == [1, 2]


def test_export_csv_custom_sep():
    """Test exporting CSV with custom separator."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        exp.export_csv(df, path, sep=";")
        assert os.path.exists(path)
        # Verify the separator is used
        with open(path) as f:
            content = f.read()
            assert ";" in content


def test_export_txt():
    """Test exporting to TXT format."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        exp.export_txt(df, path)
        assert os.path.exists(path)


def test_export_excel():
    """Test exporting to Excel format."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.xlsx")
        exp.export_excel(df, path)
        assert os.path.exists(path)
        loaded = pd.read_excel(path)
        assert loaded["a"].tolist() == [1, 2]


def test_export_pdf():
    """Test exporting to PDF format."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.pdf")
        exp.export_pdf(df, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_export_pdf_truncation():
    """Test that PDF export truncates large datasets."""
    # Create a large DataFrame
    df = pd.DataFrame({"a": range(1000), "b": range(1000, 2000)})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.pdf")
        exp.export_pdf(df, path, max_rows=100)
        assert os.path.exists(path)


def test_export_unsupported_format():
    """Test that unsupported format raises error."""
    df = pd.DataFrame({"a": [1, 2]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.xyz")
        try:
            exp.export(df, path, "xyz")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "Unsupported export format" in str(e)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow_upload_sort_export():
    """Test complete workflow: simulate upload -> sort -> export."""
    # Create test data
    df = pd.DataFrame({"id": [3, 1, 2], "name": ["c", "a", "b"]})
    
    # Sort by id
    sorted_df = ops.sort_by_column(df, "id", ascending=True)
    assert sorted_df["id"].tolist() == [1, 2, 3]
    
    # Export
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "result.csv")
        exp.export_csv(sorted_df, path)
        assert os.path.exists(path)


def test_full_workflow_remove_duplicates_export():
    """Test workflow: upload -> remove duplicates -> export."""
    df = pd.DataFrame({"a": [1, 1, 2, 3, 3], "b": ["x", "x", "y", "z", "z"]})
    
    # Remove duplicates
    cleaned = ops.remove_duplicates(df, subset=["a"])
    assert len(cleaned) == 3
    
    # Export
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "cleaned.xlsx")
        exp.export_excel(cleaned, path)
        assert os.path.exists(path)


def test_full_workflow_compare_and_merge():
    """Test workflow: compare two files -> merge results."""
    df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    df2 = pd.DataFrame({"id": [2, 3, 4], "dept": ["sales", "it", "hr"]})
    
    # Compare
    comparison = ops.compare_files(df1, df2, subset=["id"])
    common_ids = comparison["in_both"]["id"].tolist()
    assert common_ids == [2, 3]
    
    # Merge: note that merge_files concatenates columns side-by-side,
    # it doesn't do a SQL-style join, so result has as many rows as input DataFrames
    merged = ops.merge_files(df1, df2, ["id", "name"], ["id", "dept"])
    assert len(merged) == 3  # Both df1 and df2 have 3 rows


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

def test_empty_dataframe():
    """Test operations on empty DataFrame."""
    df = pd.DataFrame()
    stats = fl.basic_stats(df)
    assert stats["n_rows"] == 0


def test_single_row_dataframe():
    """Test operations on single-row DataFrame."""
    df = pd.DataFrame({"a": [1], "b": [2]})
    sorted_df = ops.sort_by_column(df, "a")
    assert len(sorted_df) == 1


def test_single_column_dataframe():
    """Test operations on single-column DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    sorted_df = ops.sort_by_column(df, "a")
    assert len(sorted_df.columns) == 1


def test_dataframe_with_null_values():
    """Test operations on DataFrame with null values."""
    df = pd.DataFrame({"a": [1, None, 3]})
    sorted_df = ops.sort_by_column(df, "a")
    assert len(sorted_df) == 3


def test_special_characters_in_data():
    """Test handling special characters."""
    df = pd.DataFrame({"text": ["hello@world", "foo#bar", "test$value"]})
    result = ops.remove_string(df, "text", "@")
    assert result["text"].tolist()[0] == "helloworld"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])

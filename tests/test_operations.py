"""
Sample unit tests for app/services/operations.py (Epic 12 - Testing).
Run with: pytest
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import operations as ops


def test_sort_by_column():
    df = pd.DataFrame({"a": [3, 1, 2]})
    result = ops.sort_by_column(df, "a")
    assert result["a"].tolist() == [1, 2, 3]


def test_find_duplicates_full_row():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    summary = ops.find_duplicates(df)
    assert len(summary) == 1
    assert summary.iloc[0]["repetition_count"] == 2


def test_remove_duplicates_by_column():
    df = pd.DataFrame({"a": [1, 1, 2]})
    cleaned = ops.remove_duplicates(df, subset=["a"])
    assert len(cleaned) == 2


def test_detect_sequences():
    values = [1, 2, 3, 7, 8, 20]
    sequences = ops.detect_sequences(values, min_length=3)
    assert sequences == [{"start": 1, "end": 3, "length": 3}]


def test_apply_math_division_by_zero():
    df = pd.DataFrame({"a": [10, 20]})
    try:
        ops.apply_math(df, "a", "/", 0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_compare_files():
    df1 = pd.DataFrame({"id": [1, 2, 3]})
    df2 = pd.DataFrame({"id": [2, 3, 4]})
    result = ops.compare_files(df1, df2)
    assert result["in_both"]["id"].tolist() == [2, 3]
    assert result["only_in_f1"]["id"].tolist() == [1]
    assert result["only_in_f2"]["id"].tolist() == [4]


def test_merge_files():
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"b": [3, 4]})
    merged = ops.merge_files(df1, df2, ["a"], ["b"])
    assert list(merged.columns) == ["a", "b"]
    assert merged["b"].tolist() == [3, 4]

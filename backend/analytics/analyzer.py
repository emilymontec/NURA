# analytics/analyzer.py
"""Utilities to analyze business datasets using pandas."""
from typing import Dict, Any

import pandas as pd

from .utils import detect_file_type


def load_csv(file_obj) -> pd.DataFrame:
    """Load a CSV or Excel file into a pandas DataFrame."""
    file_type = detect_file_type(file_obj)
    readers = {
        ".csv": pd.read_csv,
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
    }
    reader = readers.get(file_type)
    if not reader:
        raise ValueError("Tipo de archivo no soportado. Sube un archivo CSV o Excel.")
    return reader(file_obj)

def column_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Return column-level information.
    Includes dtype, number of missing values, and number of unique values.
    """
    info = {}
    for col in df.columns:
        info[col] = {
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "unique": int(df[col].nunique()),
        }
    return info

def dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """High‑level summary of the dataset.
    Returns row count, column count, total missing cells and duplicate rows.
    """
    rows, cols = df.shape
    total_missing = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    return {
        "rows": rows,
        "columns": cols,
        "total_missing": total_missing,
        "duplicate_rows": duplicate_rows,
    }

def analyze_csv(file_path: str) -> Dict[str, Any]:
    """Convenient wrapper that loads a CSV and returns a full analysis.
    """
    df = load_csv(file_path)
    return {
        "summary": dataset_summary(df),
        "columns": column_info(df),
    }

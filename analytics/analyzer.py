# analytics/analyzer.py
"""Utilities to analyze business datasets using pandas."""
from typing import Dict, Any, List

import pandas as pd

from .utils import detect_file_type
import numpy as np


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

def _infer_semantic_type(col_name: str, dtype_str: str) -> str:
    """Infer the business semantic type of a column based on its name and dtype."""
    col_lower = col_name.lower()
    
    # Financial / Monetary
    if any(word in col_lower for word in ["precio", "price", "costo", "cost", "ventas", "sales", "ingreso", "revenue", "monto", "amount", "total", "descuento", "discount", "margen", "margin"]):
        return "Financiero/Monetario"
    
    # Temporal
    if any(word in col_lower for word in ["fecha", "date", "tiempo", "time", "año", "year", "mes", "month", "dia", "day", "hora", "hour"]):
        return "Temporal"
    
    # Identifiers
    if any(word in col_lower for word in ["id", "codigo", "code", "sku", "uuid"]):
        return "Identificador"
        
    # Categorical/Business Dimensions
    if any(word in col_lower for word in ["categoria", "category", "tipo", "type", "estado", "status", "cliente", "client", "customer", "producto", "product", "region", "pais", "country", "ciudad", "city", "canal", "channel"]):
        return "Dimension Categórica"
        
    # Quantities / Metrics
    if any(word in col_lower for word in ["cantidad", "quantity", "qty", "volumen", "volume", "peso", "weight", "stock", "inventario"]):
        return "Metrica/Cantidad"
        
    if "object" in dtype_str or "str" in dtype_str:
        return "Texto/Categoria"
    elif "int" in dtype_str or "float" in dtype_str:
        return "Numerico Generico"
    return "Desconocido"

def column_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Return column-level information including business semantic type."""
    info = {}
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        info[col] = {
            "dtype": dtype_str,
            "semantic_type": _infer_semantic_type(col, dtype_str),
            "missing": int(df[col].isna().sum()),
            "unique": int(df[col].nunique()),
        }
    return info

def compute_correlations(df: pd.DataFrame, threshold: float = 0.65) -> List[Dict[str, Any]]:
    """
    Calculate Pearson correlation for numeric columns.
    Returns a list of significant correlations (absolute value >= threshold).
    """
    correlations = []
    numeric_df = df.select_dtypes(include=[np.number])
    
    if len(numeric_df.columns) < 2:
        return correlations
        
    corr_matrix = numeric_df.corr()
    
    # Get upper triangle to avoid duplicates
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr_value = corr_matrix.iloc[i, j]
            
            if pd.notna(corr_value) and abs(corr_value) >= threshold:
                correlations.append({
                    "col1": col1,
                    "col2": col2,
                    "correlation": round(float(corr_value), 2),
                    "strength": "Fuerte" if abs(corr_value) >= 0.8 else "Moderada",
                    "direction": "Positiva" if corr_value > 0 else "Negativa"
                })
                
    # Sort by absolute correlation (strongest first)
    correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return correlations

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

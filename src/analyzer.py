import pandas as pd


def analyze_data(df):

    numeric_columns = df.select_dtypes(include="number")

    results = {}

    for column in numeric_columns.columns:

        results[column] = {
            "sum": float(df[column].sum()),
            "mean": float(df[column].mean()),
            "max": float(df[column].max()),
            "min": float(df[column].min())
        }

    return results
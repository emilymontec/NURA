import pandas as pd


def detect_anomalies(series):

    mean = series.mean()
    std = series.std()

    upper_limit = mean + (2 * std)
    lower_limit = mean - (2 * std)

    anomalies = series[
        (series > upper_limit) |
        (series < lower_limit)
    ]

    return anomalies.tolist()


def analyze_data(df):

    numeric_columns = df.select_dtypes(include="number")

    results = {}

    for column in numeric_columns.columns:

        anomalies = detect_anomalies(df[column])

        results[column] = {
            "sum": float(df[column].sum()),
            "mean": float(df[column].mean()),
            "max": float(df[column].max()),
            "min": float(df[column].min()),
            "anomalies": anomalies
        }

    return results
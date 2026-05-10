import streamlit as st
import pandas as pd

from analyzer import analyze_data
from insights import generate_insights

st.title("AI Analyst MVP")

uploaded_file = st.file_uploader(
    "Sube un archivo CSV",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("Vista previa")
    st.dataframe(df.head())

    results = analyze_data(df)

    insights = generate_insights(results)

    st.subheader("Métricas")
    st.json(results)

    st.subheader("Insights")

    for insight in insights:
        st.write(f"- {insight}")
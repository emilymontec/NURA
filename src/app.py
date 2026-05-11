import streamlit as st
import pandas as pd

from analyzer import analyze_data
from insights import generate_insights

import matplotlib.pyplot as plt

from llm import generate_ai_report

st.title("DALOT: Analyst MVP")

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

    st.subheader("Reporte IA")
    
    with st.spinner("Generando análisis IA..."):
        
        ai_report = generate_ai_report(results)
    
    st.write(ai_report)
    
    st.subheader("Gráficos")
    
    numeric_columns = df.select_dtypes(include="number")
    
    for column in numeric_columns.columns:
        
        fig, ax = plt.subplots()
        
        ax.plot(df[column])
        
        ax.set_title(column)
        
        st.pyplot(fig)
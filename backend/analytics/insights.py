# analytics/insights.py
from typing import Dict, Any, List

def generate_insights(summary: Dict[str, Any], trends: Dict[str, Any], health: Dict[str, Any]) -> List[str]:
    """Generate automated insights based on data summary, trends, and health score."""
    insights = []
    
    # Check health
    score = health.get("health_score", 0)
    if score < 50:
        insights.append(f"Salud critica de datos: el dataset tiene una puntuacion baja ({score}). Revisa faltantes y duplicados.")
    elif score >= 80:
        insights.append("Salud excelente de datos: el dataset se ve limpio y bien estructurado.")
        
    # Check summary
    missing = summary.get("total_missing", 0)
    if missing > 0:
        insights.append(f"Datos faltantes: se detectaron {missing} valores ausentes en el dataset.")
        
    dupes = summary.get("duplicate_rows", 0)
    if dupes > 0:
        insights.append(f"Registros duplicados: se encontraron {dupes} filas duplicadas que pueden afectar el analisis.")
        
    # Check trends
    for col, trend_data in trends.items():
        trend_val = trend_data.get("trend", 0)
        if trend_val > 0:
            insights.append(f"Tendencia positiva en {col}: los datos muestran una trayectoria ascendente (pendiente: {trend_val:.2f}).")
        elif trend_val < 0:
            insights.append(f"Tendencia negativa en {col}: los datos muestran una trayectoria descendente (pendiente: {trend_val:.2f}).")
            
    if not insights:
        insights.append("No se detectaron insights inmediatos relevantes. Los datos parecen estables.")
        
    return insights

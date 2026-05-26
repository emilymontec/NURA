# analytics/insights.py
from typing import Dict, Any, List

def generate_insights(summary: Dict[str, Any], trends: Dict[str, Any], health: Dict[str, Any], correlations: List[Dict[str, Any]] = None) -> List[str]:
    """Generate automated insights based on data summary, trends, and health score."""
    insights = []
    
    # Check health
    score = health.get("health_score", 0)
    if score < 50:
        insights.append(f"Atención con los datos: La calidad de la información es baja. Revisa si hay celdas vacías o filas repetidas.")
    elif score >= 80:
        insights.append("¡Excelente!: Tu información se ve limpia y completa.")
        
    # Check summary
    missing = summary.get("total_missing", 0)
    if missing > 0:
        insights.append(f"Información incompleta: Hay {missing} celdas vacías en tu archivo.")
        
    dupes = summary.get("duplicate_rows", 0)
    if dupes > 0:
        insights.append(f"Datos repetidos: Hay {dupes} filas exactamente iguales que podrían distorsionar tus totales.")
        
    # Check trends
    for col, trend_data in trends.items():
        trend_val = trend_data.get("trend", 0)
        if trend_val > 0:
            insights.append(f"Crecimiento en '{col}': Los datos muestran que esta métrica tiende a subir.")
        elif trend_val < 0:
            insights.append(f"Caída en '{col}': Los datos muestran que esta métrica tiende a bajar.")
            
    # Check correlations / Relationships
    if correlations:
        for corr in correlations:
            col1 = corr["col1"]
            col2 = corr["col2"]
            direction = corr["direction"]
            strength = corr["strength"]
            val = corr["correlation"]
            
            if direction == "Positiva":
                insights.append(f"Relación directa detectada: Cuando '{col1}' sube, '{col2}' también tiende a subir. Esto podría ser útil para impulsar el crecimiento.")
            else:
                insights.append(f"Relación inversa detectada: Cuando '{col1}' sube, '{col2}' tiende a bajar. Presta atención a esto para evitar problemas o compensaciones indeseadas.")
            
    if not insights:
        insights.append("A simple vista, no encontramos patrones ni relaciones fuertes. La información parece estable.")
        
    return insights


def generate_insights(results):

    insights = []

    for column, metrics in results.items():

        if metrics["mean"] < 100:
            insights.append(
                f"La media de {column} es baja."
            )

        insights.append(
            f"El valor máximo de {column} es {metrics['max']}."
        )

    return insights
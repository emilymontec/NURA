from groq import Groq
from dotenv import load_dotenv

import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_ai_report(results):

    prompt = f"""
    Eres un analista senior de negocios.

    Analiza estas métricas:

    {results}

    Genera:

    - fortalezas
    - problemas
    - riesgos
    - oportunidades
    - recomendaciones

    Sé profesional y claro.
    """

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.4
    )

    return response.choices[0].message.content
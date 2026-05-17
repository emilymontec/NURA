# ai/llm.py
import os
from groq import Groq
from dotenv import load_dotenv
from .prompts import EXECUTIVE_REPORT_PROMPT, CHAT_ANALYST_PROMPT

load_dotenv()

# Initialize Groq client
# Fallback to an empty string to avoid errors if API key is not set immediately
api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None
MODEL_NAME = "llama-3.3-70b-versatile"

def generate_ai_report(context_data: dict) -> str:
    """Generate an executive report using Groq."""
    if not client:
        return "Error: GROQ_API_KEY no esta configurada."
        
    prompt = EXECUTIVE_REPORT_PROMPT.format(
        summary=context_data.get('summary', {}),
        health=context_data.get('health', {}),
        trends=context_data.get('trends', {}),
        insights=context_data.get('insights', [])
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres una analista senior de datos y respondes siempre en espanol."},
                {"role": "user", "content": prompt}
            ],
            model=MODEL_NAME,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar el reporte: {str(e)}"

def chat_with_data(question: str, context: dict, history: str) -> str:
    """Answer user questions based on data context."""
    if not client:
        return "Error: GROQ_API_KEY no esta configurada."
        
    prompt = CHAT_ANALYST_PROMPT.format(
        context=context,
        history=history,
        question=question
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres NURA, una asistente de analitica de datos empresariales. "
                        "Respondes siempre en espanol, con claridad, precision y tono profesional."
                    ),
                },
                {"role": "user", "content": prompt}
            ],
            model=MODEL_NAME,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en el chat: {str(e)}"

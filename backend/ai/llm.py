# ai/llm.py
import os
from groq import Groq
from dotenv import load_dotenv
from .agents import run_agent_system
from .prompts import EXECUTIVE_REPORT_PROMPT, CHAT_ANALYST_PROMPT, AGENT_SYNTHESIS_PROMPT

load_dotenv()

# Initialize Groq client
# Fallback to an empty string to avoid errors if API key is not set immediately
api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None
MODEL_NAME = "llama-3.3-70b-versatile"


def _run_completion(system_message: str, prompt: str, temperature: float = 0.4) -> str:
    """Shared helper for all LLM calls."""
    if not client:
        return "Error: GROQ_API_KEY no esta configurada."

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        model=MODEL_NAME,
        temperature=temperature,
    )
    return response.choices[0].message.content

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
        return _run_completion(
            system_message="Eres una analista senior de datos y respondes siempre en espanol.",
            prompt=prompt,
            temperature=0.3,
        )
    except Exception as e:
        return f"Error al generar el reporte: {str(e)}"

def chat_with_data(question: str, context: dict, history: str) -> str:
    """Answer user questions using a specialized multi-agent system."""
    if not client:
        return "Error: GROQ_API_KEY no esta configurada."

    try:
        agent_results = run_agent_system(
            question=question,
            context=context,
            history=history,
            llm_callback=_run_completion,
        )
        agent_outputs = "\n\n".join(
            f"{item['name']}:\n{item['output']}" for item in agent_results
        )

        synthesis_prompt = AGENT_SYNTHESIS_PROMPT.format(
            context=context,
            history=history,
            question=question,
            agent_names=", ".join(item["name"] for item in agent_results),
            agent_outputs=agent_outputs,
        )

        return _run_completion(
            system_message=(
                "Eres NURA, una asistente de analitica de datos empresariales que opera como sistema multiagente. "
                "Respondes siempre en espanol, con claridad, precision y criterio estrategico."
            ),
            prompt=synthesis_prompt,
            temperature=0.45,
        )
    except Exception as e:
        try:
            # Fallback conservador al modo anterior si algun agente falla.
            prompt = CHAT_ANALYST_PROMPT.format(
                context=context,
                history=history,
                question=question,
            )
            return _run_completion(
                system_message=(
                    "Eres NURA, una asistente de analitica de datos empresariales. "
                    "Respondes siempre en espanol, con claridad, precision y tono profesional."
                ),
                prompt=prompt,
                temperature=0.4,
            )
        except Exception:
            return f"Error en el chat: {str(e)}"

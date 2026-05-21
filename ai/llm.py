# ai/llm.py
import os
from groq import Groq
from dotenv import load_dotenv
from .agents import run_agent_system, get_agent_options, AGENT_REGISTRY, run_specialist_agent
from .prompts import EXECUTIVE_REPORT_PROMPT, CHAT_ANALYST_PROMPT, AGENT_ROUTER_PROMPT

load_dotenv()

# Initialize Groq client
# Fallback to an empty string to avoid errors if API key is not set immediately
api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None
MODEL_NAME = "llama-3.1-8b-instant"
ROUTER_MODEL_NAME = "llama-3.1-8b-instant"


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

def _summarize_context(context: dict) -> str:
    """Summarize context to drastically reduce tokens sent to the LLM."""
    if not context or not context.get("file_name"):
        return "Sin dataset activo."
        
    summary = context.get("summary", {})
    insights = context.get("insights", [])
    
    lines = [
        f"Archivo: {context.get('file_name')} ({summary.get('rows', 0)} filas, {summary.get('columns', 0)} cols)",
        f"Salud: {context.get('health', {}).get('health_score', 0)}/100"
    ]
    if insights:
        lines.append("Insights principales:")
        for ins in insights[:4]: # Send only top 4 insights
            lines.append(f"- {ins}")
            
    return "\n".join(lines)

def route_intent(question: str, context: dict, history: str) -> str:
    """Uses a fast LLM call to decide which agent should handle the intent."""
    if not client:
        return "chat"
        
    prompt = AGENT_ROUTER_PROMPT.format(
        question=question,
        history=history,
        agent_options=get_agent_options()
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres el enrutador de intenciones de NURA. Responde ÚNICAMENTE con el key del agente seleccionado."},
                {"role": "user", "content": prompt},
            ],
            model=ROUTER_MODEL_NAME,
            temperature=0.1,
            max_tokens=15
        )
        selected_key = response.choices[0].message.content.strip().lower()
        # Clean up possible punctuation
        for char in [".", "'", '"', "`", "\n"]:
            selected_key = selected_key.replace(char, "")
        return selected_key.strip()
    except Exception:
        return "chat"

def chat_with_data(question: str, context: dict, history: str) -> str:
    """Answer user questions using the intelligent intent router."""
    if not client:
        return "Error: GROQ_API_KEY no esta configurada."

    try:
        # 1. Summarize context to save tokens
        short_context = _summarize_context(context)
        has_dataset = bool(context and context.get("file_name"))

        # 2. Skip intent router if it's clearly a generic chat or no dataset
        # "NO uses multi_agent_analysis SIEMPRE"
        if not has_dataset or len(question.split()) < 3:
            selected_key = "chat"
        else:
            selected_key = route_intent(question, short_context, history)
        
        # 3. Execute selected specialist if applicable
        if selected_key in AGENT_REGISTRY:
            agent = AGENT_REGISTRY[selected_key]
            if not (agent.requires_dataset and not has_dataset):
                # Run the single specialist agent
                return run_specialist_agent(agent, question, short_context, history, _run_completion)
                
        # 4. Fallback to normal chat
        prompt = CHAT_ANALYST_PROMPT.format(
            context=short_context,
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

    except Exception as e:
        return f"Error en el chat: {str(e)}"

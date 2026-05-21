import os
import json
import requests
from dotenv import load_dotenv
from .agents import run_agent_system, get_agent_options, AGENT_REGISTRY, run_specialist_agent
from .prompts import EXECUTIVE_REPORT_PROMPT, CHAT_ANALYST_PROMPT, AGENT_ROUTER_PROMPT

load_dotenv()

class LLMRouter:
    """Intelligent router that handles redundancy and cost optimization across multiple LLM providers."""
    def __init__(self):
        self.keys = {
            "groq": os.getenv("GROQ_API_KEY", ""),
            "cerebras": os.getenv("CEREBRAS_API_KEY", ""),
            "openrouter": os.getenv("OPENROUTER_API_KEY", "")
        }
        
        self.endpoints = {
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "cerebras": "https://api.cerebras.ai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions"
        }
        
        # Define model tiers to optimize cost and performance
        # Each tier defines a fallback sequence: (provider, model)
        self.tiers = {
            "fast": [
                ("groq", "llama-3.1-8b-instant"),
                ("cerebras", "llama3.1-8b"),
                ("openrouter", "google/gemini-2.5-flash")
            ],
            "standard": [
                ("groq", "llama-3.3-70b-versatile"),
                ("cerebras", "llama3.1-70b"),
                ("openrouter", "meta-llama/llama-3.3-70b-instruct")
            ],
            "premium": [
                ("openrouter", "anthropic/claude-3.5-sonnet"),
                ("openrouter", "openai/gpt-4o"),
                ("groq", "llama-3.3-70b-versatile")
            ]
        }
        
    def generate(self, messages: list, tier: str = "standard", temperature: float = 0.4, max_tokens: int = None) -> str:
        sequence = self.tiers.get(tier, self.tiers["standard"])
        
        for provider, model in sequence:
            api_key = self.keys.get(provider)
            if not api_key:
                continue
                
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            if provider == "openrouter":
                headers["HTTP-Referer"] = "https://nura.ai"
                headers["X-Title"] = "NURA"
                
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
                
            try:
                response = requests.post(self.endpoints[provider], headers=headers, json=payload, timeout=25)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    print(f"[NURA Router] Fallback activado: {provider} ({model}) fallo con estado {response.status_code}.")
            except Exception as e:
                print(f"[NURA Router] Fallback activado: Excepcion con {provider} ({model}) - {str(e)}")
                
        raise Exception("Todos los proveedores LLM configurados (Groq, Cerebras, OpenRouter) han fallado o no estan configurados.")

router = LLMRouter()

def _run_completion(system_message: str, prompt: str, temperature: float = 0.4, tier: str = "standard") -> str:
    """Shared helper for all LLM calls with tier routing."""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    return router.generate(messages, tier=tier, temperature=temperature)

def generate_ai_report(context_data: dict) -> str:
    """Generate an executive report using a Premium model."""
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
            tier="premium"
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
        for ins in insights[:4]:
            lines.append(f"- {ins}")
            
    return "\n".join(lines)

def route_intent(question: str, context: dict, history: str) -> str:
    """Uses a fast LLM call to decide which agent should handle the intent."""
    prompt = AGENT_ROUTER_PROMPT.format(
        question=question,
        history=history,
        agent_options=get_agent_options()
    )
    
    try:
        response_text = router.generate(
            messages=[
                {"role": "system", "content": "Eres el enrutador de intenciones de NURA. Responde ÚNICAMENTE con el key del agente seleccionado."},
                {"role": "user", "content": prompt},
            ],
            tier="fast",
            temperature=0.1,
            max_tokens=15
        )
        selected_key = response_text.strip().lower()
        for char in [".", "'", '"', "`", "\n"]:
            selected_key = selected_key.replace(char, "")
        return selected_key.strip()
    except Exception as e:
        print(f"[NURA Router] Error en route_intent: {e}")
        return "chat"

def chat_with_data(question: str, context: dict, history: str) -> str:
    """Answer user questions using the intelligent intent router."""
    try:
        short_context = _summarize_context(context)
        has_dataset = bool(context and context.get("file_name"))

        if not has_dataset or len(question.split()) < 3:
            selected_key = "chat"
        else:
            selected_key = route_intent(question, short_context, history)
        
        if selected_key in AGENT_REGISTRY:
            agent = AGENT_REGISTRY[selected_key]
            if not (agent.requires_dataset and not has_dataset):
                # Usar un lambda/wrapper para pasar el tier="standard" a los agentes especialistas si fuese necesario
                def run_specialist_callback(system_message, prompt, temperature=0.25):
                    return _run_completion(system_message, prompt, temperature, tier="standard")
                    
                return run_specialist_agent(agent, question, short_context, history, run_specialist_callback)
                
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
            tier="standard"
        )

    except Exception as e:
        return f"Error en el sistema de chat (Router falló): {str(e)}"

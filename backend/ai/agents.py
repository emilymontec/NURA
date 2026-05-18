# ai/agents.py
"""Multi-agent orchestration for NURA."""

from dataclasses import dataclass
from typing import Dict, List

from .prompts import AGENT_SPECIALIST_PROMPT


@dataclass(frozen=True)
class AgentProfile:
    key: str
    name: str
    focus: str
    goal: str
    triggers: tuple[str, ...]
    requires_dataset: bool = False
    priority: int = 50


AGENT_REGISTRY = {
    "context": AgentProfile(
        key="context",
        name="Context Agent",
        focus="memoria conversacional, referencias anteriores, decisiones previas y continuidad",
        goal="asegurar que la respuesta recuerde lo dicho antes y entienda referencias implicitas",
        triggers=("antes", "anterior", "dijiste", "hablamos", "recuerda", "contexto", "referias"),
        requires_dataset=False,
        priority=100,
    ),
    "risk": AgentProfile(
        key="risk",
        name="Risk Agent",
        focus="riesgos, anomalías, inconsistencias, faltantes, duplicados y señales de alerta",
        goal="detectar problemas potenciales, riesgos operativos o de calidad de datos",
        triggers=("riesgo", "anomalia", "anomal", "error", "inconsistencia", "alerta", "problema"),
        requires_dataset=False,
        priority=92,
    ),
    "insight": AgentProfile(
        key="insight",
        name="Insight Agent",
        focus="patrones, comportamiento, oportunidades, relaciones y hallazgos relevantes",
        goal="identificar lo mas interesante del contexto y del dataset",
        triggers=("patron", "insight", "hallazgo", "oportunidad", "comportamiento", "tendencia"),
        requires_dataset=False,
        priority=90,
    ),
    "recommendation": AgentProfile(
        key="recommendation",
        name="Recommendation Agent",
        focus="acciones, optimizacion, soluciones concretas y siguientes pasos",
        goal="convertir el analisis en decisiones accionables y recomendaciones claras",
        triggers=("recomienda", "accion", "mejora", "optimiza", "solucion", "que hago", "siguiente paso"),
        requires_dataset=False,
        priority=88,
    ),
    "strategy": AgentProfile(
        key="strategy",
        name="Strategy Agent",
        focus="impacto ejecutivo, priorizacion, criterio de negocio y lectura estrategica",
        goal="traducir datos y contexto en implicaciones de negocio y prioridades",
        triggers=("estrategia", "negocio", "prioriza", "direccion", "impacto", "ejecutivo"),
        requires_dataset=False,
        priority=84,
    ),
    "operations": AgentProfile(
        key="operations",
        name="Operations Agent",
        focus="eficiencia operativa, cuellos de botella, procesos y continuidad operacional",
        goal="detectar mejoras operativas y riesgos de ejecucion",
        triggers=("operacion", "proceso", "eficiencia", "flujo", "cuello", "productividad"),
        requires_dataset=False,
        priority=78,
    ),
    "forecast": AgentProfile(
        key="forecast",
        name="Forecast Agent",
        focus="trayectorias, escenarios, proyecciones prudentes y lectura de tendencias",
        goal="inferir hacia donde apuntan los datos sin sobredimensionar predicciones",
        triggers=("proyeccion", "forecast", "escenario", "futuro", "crec", "caer", "tendencia"),
        requires_dataset=True,
        priority=76,
    ),
}


def _has_dataset(context: Dict) -> bool:
    return bool(context and context.get("file_name"))


def _dataset_signal_count(context: Dict) -> int:
    count = 0
    if context.get("summary"):
        count += 1
    if context.get("health"):
        count += 1
    if context.get("trends"):
        count += 1
    if context.get("insights"):
        count += 1
    return count


def select_agents(question: str, context: Dict, history: str) -> List[AgentProfile]:
    """Select a compact but meaningful set of specialist agents."""
    lowered_question = (question or "").lower()
    lowered_history = (history or "").lower()
    has_dataset = _has_dataset(context)
    selected: List[AgentProfile] = []

    for agent in AGENT_REGISTRY.values():
        if agent.requires_dataset and not has_dataset:
            continue

        if agent.key == "context":
            if any(trigger in lowered_question for trigger in agent.triggers) or any(
                trigger in lowered_history for trigger in agent.triggers
            ):
                selected.append(agent)
            continue

        if any(trigger in lowered_question for trigger in agent.triggers):
            selected.append(agent)

    if has_dataset:
        defaults = ["insight", "risk", "recommendation"]
        if _dataset_signal_count(context) >= 3:
            defaults.append("strategy")
    else:
        defaults = ["strategy", "recommendation"]

    for key in defaults:
        agent = AGENT_REGISTRY[key]
        if agent not in selected:
            selected.append(agent)

    if "context" not in [agent.key for agent in selected]:
        if any(term in lowered_question for term in ("antes", "anterior", "mencionaste", "dijiste", "eso", "esa", "ese")):
            selected.insert(0, AGENT_REGISTRY["context"])

    unique_agents = []
    seen = set()
    for agent in sorted(selected, key=lambda item: item.priority, reverse=True):
        if agent.key not in seen:
            unique_agents.append(agent)
            seen.add(agent.key)

    return unique_agents[:4]


def run_specialist_agent(agent: AgentProfile, question: str, context: Dict, history: str, llm_callback) -> str:
    """Run a specialist agent through the shared LLM callback."""
    prompt = AGENT_SPECIALIST_PROMPT.format(
        agent_name=agent.name,
        agent_focus=agent.focus,
        agent_goal=agent.goal,
        context=context,
        history=history,
        question=question,
    )
    return llm_callback(prompt=prompt, system_message=f"Eres {agent.name} dentro del sistema multiagente de NURA.", temperature=0.25)


def run_agent_system(question: str, context: Dict, history: str, llm_callback) -> List[Dict[str, str]]:
    """Execute selected agents and return their outputs."""
    selected_agents = select_agents(question, context, history)
    results = []
    for agent in selected_agents:
        output = run_specialist_agent(agent, question, context, history, llm_callback)
        results.append(
            {
                "key": agent.key,
                "name": agent.name,
                "focus": agent.focus,
                "output": output,
            }
        )
    return results

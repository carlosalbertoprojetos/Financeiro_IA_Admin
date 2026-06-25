from typing import Any, TypedDict


class OpenAIModelOption(TypedDict):
    id: str
    label: str
    description: str
    tier: str
    recommended: bool


RECOMMENDED_OPENAI_MODELS: list[OpenAIModelOption] = [
    {
        "id": "gpt-5.5",
        "label": "GPT-5.5",
        "description": "Máxima qualidade para diagnósticos operacionais complexos.",
        "tier": "flagship",
        "recommended": False,
    },
    {
        "id": "gpt-5.4",
        "label": "GPT-5.4",
        "description": "Alto desempenho com bom equilíbrio entre qualidade e custo.",
        "tier": "balanced",
        "recommended": False,
    },
    {
        "id": "gpt-5.4-mini",
        "label": "GPT-5.4 Mini",
        "description": "Rápido e econômico para análises recorrentes.",
        "tier": "fast",
        "recommended": True,
    },
    {
        "id": "gpt-4.1",
        "label": "GPT-4.1",
        "description": "Modelo estável para relatórios executivos detalhados.",
        "tier": "balanced",
        "recommended": False,
    },
    {
        "id": "gpt-4.1-mini",
        "label": "GPT-4.1 Mini",
        "description": "Compacto e confiável para uso diário.",
        "tier": "fast",
        "recommended": False,
    },
    {
        "id": "gpt-4o",
        "label": "GPT-4o",
        "description": "Multimodal legado com boa qualidade geral.",
        "tier": "balanced",
        "recommended": False,
    },
    {
        "id": "gpt-4o-mini",
        "label": "GPT-4o Mini",
        "description": "Opção econômica da família GPT-4o.",
        "tier": "fast",
        "recommended": False,
    },
]

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
ALLOWED_OPENAI_MODEL_IDS = {model["id"] for model in RECOMMENDED_OPENAI_MODELS}


def is_allowed_openai_model(model: str) -> bool:
    return model in ALLOWED_OPENAI_MODEL_IDS


def normalize_openai_model(model: str | None) -> str:
    cleaned = (model or "").strip()
    if not cleaned:
        return DEFAULT_OPENAI_MODEL
    if not is_allowed_openai_model(cleaned):
        raise ValueError(f"Unsupported OpenAI model: {cleaned}")
    return cleaned


def get_model_option(model_id: str) -> OpenAIModelOption | None:
    for option in RECOMMENDED_OPENAI_MODELS:
        if option["id"] == model_id:
            return option
    return None


def openai_models_payload() -> list[dict[str, Any]]:
    return [dict(option) for option in RECOMMENDED_OPENAI_MODELS]

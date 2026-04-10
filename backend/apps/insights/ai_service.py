"""
Lumiq AI Service — Capa de abstracción para proveedores de IA.

Soporta:
  - Ollama (local, gratuito) → desarrollo
  - Anthropic Claude        → producción

Para cambiar de proveedor: modificar AI_PROVIDER en .env
"""
import json
from decouple import config

AI_PROVIDER = config('AI_PROVIDER', default='ollama')
OLLAMA_BASE_URL = config('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3.2')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')


def get_ai_response(prompt: str, max_tokens: int = 600, model_override: str | None = None) -> str:
    """
    Genera una respuesta completa (sin streaming).
    Usa el proveedor configurado en .env
    """
    if AI_PROVIDER == 'anthropic':
        return _anthropic_response(prompt, max_tokens, model_override)
    return _ollama_response(prompt, max_tokens, model_override)


def get_ai_stream(prompt: str, max_tokens: int = 600, model_override: str | None = None):
    """
    Generador que hace yield de tokens uno a uno.
    Compatible con StreamingHttpResponse de Django.
    """
    if AI_PROVIDER == 'anthropic':
        yield from _anthropic_stream(prompt, max_tokens, model_override)
    else:
        yield from _ollama_stream(prompt, max_tokens, model_override)


# ─── Ollama ───────────────────────────────────────────────────────────────────

def _ollama_response(prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    import ollama
    response = ollama.chat(
        model=model_override or OLLAMA_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        options={'num_predict': max_tokens},
    )
    return response['message']['content']


def _ollama_stream(prompt: str, max_tokens: int, model_override: str | None = None):
    import ollama
    stream = ollama.chat(
        model=model_override or OLLAMA_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        options={'num_predict': max_tokens},
        stream=True,
    )
    for chunk in stream:
        token = chunk['message']['content']
        if token:
            yield token


# ─── Anthropic ────────────────────────────────────────────────────────────────

def _anthropic_response(prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=model_override or 'claude-opus-4-6',
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return message.content[0].text


def _anthropic_stream(prompt: str, max_tokens: int, model_override: str | None = None):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    with client.messages.stream(
        model=model_override or 'claude-opus-4-6',
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text

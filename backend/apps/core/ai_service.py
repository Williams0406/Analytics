"""
Lumiq AI Service - Abstracción de proveedor de IA.
Soporta Groq, Anthropic y Ollama según AI_PROVIDER.
"""
from django.conf import settings


def get_ai_response(prompt: str, system: str = "") -> str:
    provider = getattr(settings, 'AI_PROVIDER', 'groq')

    if provider == 'groq':
        return _groq_response(prompt, system)
    elif provider == 'anthropic':
        return _anthropic_response(prompt, system)
    elif provider == 'ollama':
        return _ollama_response(prompt, system)
    else:
        raise ValueError(f"AI_PROVIDER no soportado: {provider}")


def _groq_response(prompt: str, system: str) -> str:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _anthropic_response(prompt: str, system: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    kwargs = {"model": "claude-opus-4-6", "max_tokens": 1024,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def _ollama_response(prompt: str, system: str) -> str:
    import ollama
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = ollama.chat(model=settings.OLLAMA_MODEL, messages=messages)
    return response['message']['content']
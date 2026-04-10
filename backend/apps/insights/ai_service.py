"""
Lumiq AI Service - Capa de abstraccion para proveedores de IA.

Soporta:
  - Groq
  - Ollama
  - Anthropic Claude

La configuracion se lee desde Django settings para mantener un
comportamiento consistente entre modulos y entornos.
"""
from django.conf import settings


def get_ai_provider_and_model(model_override: str | None = None) -> tuple[str, str]:
    provider = getattr(settings, 'AI_PROVIDER', 'groq')

    if provider == 'groq':
        model = model_override or getattr(settings, 'GROQ_MODEL', 'llama3-8b-8192')
    elif provider == 'anthropic':
        model = model_override or 'claude-opus-4-6'
    elif provider == 'ollama':
        model = model_override or getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
    else:
        raise ValueError(f'AI_PROVIDER no soportado: {provider}')

    return provider, model


def get_ai_response(prompt: str, max_tokens: int = 600, model_override: str | None = None) -> str:
    """
    Genera una respuesta completa (sin streaming).
    Usa el proveedor configurado en Django settings.
    """
    provider, _ = get_ai_provider_and_model(model_override)

    if provider == 'groq':
        return _groq_response(prompt, max_tokens, model_override)
    if provider == 'anthropic':
        return _anthropic_response(prompt, max_tokens, model_override)
    if provider == 'ollama':
        return _ollama_response(prompt, max_tokens, model_override)
    raise ValueError(f'AI_PROVIDER no soportado: {provider}')


def get_ai_stream(prompt: str, max_tokens: int = 600, model_override: str | None = None):
    """
    Generador que hace yield de tokens uno a uno.
    Compatible con StreamingHttpResponse de Django.
    """
    provider, _ = get_ai_provider_and_model(model_override)

    if provider == 'groq':
        yield from _groq_stream(prompt, max_tokens, model_override)
    elif provider == 'anthropic':
        yield from _anthropic_stream(prompt, max_tokens, model_override)
    elif provider == 'ollama':
        yield from _ollama_stream(prompt, max_tokens, model_override)
    else:
        raise ValueError(f'AI_PROVIDER no soportado: {provider}')


def _groq_response(prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    from groq import Groq

    _, model = get_ai_provider_and_model(model_override)
    client = Groq(api_key=getattr(settings, 'GROQ_API_KEY', ''))
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        max_completion_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _groq_stream(prompt: str, max_tokens: int, model_override: str | None = None):
    from groq import Groq

    _, model = get_ai_provider_and_model(model_override)
    client = Groq(api_key=getattr(settings, 'GROQ_API_KEY', ''))
    stream = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        max_completion_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


def _ollama_response(prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    import ollama

    _, model = get_ai_provider_and_model(model_override)
    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        options={'num_predict': max_tokens},
    )
    return response['message']['content']


def _ollama_stream(prompt: str, max_tokens: int, model_override: str | None = None):
    import ollama

    _, model = get_ai_provider_and_model(model_override)
    stream = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        options={'num_predict': max_tokens},
        stream=True,
    )
    for chunk in stream:
        token = chunk['message']['content']
        if token:
            yield token


def _anthropic_response(prompt: str, max_tokens: int, model_override: str | None = None) -> str:
    import anthropic

    _, model = get_ai_provider_and_model(model_override)
    client = anthropic.Anthropic(api_key=getattr(settings, 'ANTHROPIC_API_KEY', ''))
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return message.content[0].text


def _anthropic_stream(prompt: str, max_tokens: int, model_override: str | None = None):
    import anthropic

    _, model = get_ai_provider_and_model(model_override)
    client = anthropic.Anthropic(api_key=getattr(settings, 'ANTHROPIC_API_KEY', ''))
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text

"""Cliente minimo para llamar a la API de DeepSeek (compatible con OpenAI SDK)."""
from openai import OpenAI
from . import config

_client = None


def get_client():
    global _client
    if _client is None:
        if not config.DEEPSEEK_API_KEY:
            raise RuntimeError("Falta DEEPSEEK_API_KEY en el .env")
        _client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )
    return _client


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.8, max_tokens: int = 6000) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

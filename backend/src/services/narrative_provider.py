import os

_provider = os.getenv("NARRATIVE_PROVIDER", "gemini").lower()


def get_provider() -> str:
    return _provider


def set_provider(provider: str) -> str:
    global _provider
    provider = provider.lower()
    if provider not in ("gemini", "claude"):
        raise ValueError("provider must be 'gemini' or 'claude'")
    _provider = provider
    return _provider

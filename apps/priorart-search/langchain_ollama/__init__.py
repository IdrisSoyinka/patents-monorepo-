"""Fallback stub for langchain_ollama when the package is unavailable."""


class ChatOllama:  # pragma: no cover - simple stub
    """Minimal stub matching the real ChatOllama interface."""

    _ERROR_MESSAGE = (
        "Ollama API client is not available. Install langchain-ollama and "
        "ensure the Ollama API key is configured."
    )

    def __init__(self, *_, **__):
        pass

    def with_structured_output(self, *_args, **_kwargs):
        """Mimic the real client failing due to missing API integration."""

        raise RuntimeError(self._ERROR_MESSAGE)

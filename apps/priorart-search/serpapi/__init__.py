"""Fallback stub for the serpapi package used in tests."""


class GoogleSearch:  # pragma: no cover - simple stub
    """Minimal stub that mimics SerpAPI GoogleSearch behaviour."""

    def __init__(self, *_args, **_kwargs):
        pass

    def get_dict(self, *_args, **_kwargs):
        raise RuntimeError(
            "SerpAPI client not configured. Set the SERPAPI_API_KEY environment variable."
        )

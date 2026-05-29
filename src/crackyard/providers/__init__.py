from crackyard.config import Config
from crackyard.providers.base import Provider
from crackyard.providers.vastai import VastAIProvider

PROVIDER_NAMES = ["vastai"]


def get_provider(name: str, config: Config) -> Provider:
    if name == "vastai":
        return VastAIProvider(api_key=config.require_vast_api_key())
    raise SystemExit(
        f"Unknown provider: {name!r}. Available: {', '.join(PROVIDER_NAMES)}"
    )

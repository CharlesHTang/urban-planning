from importlib import import_module

from ..config import SiteConfig
from .base import SiteAdapter
from .capture_only import CaptureOnlyAdapter

BUILT_IN_ADAPTERS: dict[str, type[SiteAdapter]] = {
    "capture_only": CaptureOnlyAdapter,
}


def load_adapter(config: SiteConfig) -> SiteAdapter:
    """Construct a built-in adapter or a class referenced as module:ClassName."""
    adapter_class = BUILT_IN_ADAPTERS.get(config.adapter)
    if adapter_class is None:
        adapter_class = _import_adapter(config.adapter)
    return adapter_class(config)


def _import_adapter(reference: str) -> type[SiteAdapter]:
    if ":" not in reference:
        raise ValueError(
            f"Unknown adapter {reference!r}; custom adapters use module:ClassName"
        )
    module_name, class_name = reference.rsplit(":", 1)
    candidate = getattr(import_module(module_name), class_name)
    if not isinstance(candidate, type) or not issubclass(candidate, SiteAdapter):
        raise TypeError(f"{reference!r} is not a SiteAdapter subclass")
    return candidate


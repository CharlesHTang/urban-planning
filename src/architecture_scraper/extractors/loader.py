from importlib import import_module

from ..config import SiteConfig
from .base import ProjectExtractor


def load_extractor(config: SiteConfig) -> ProjectExtractor:
    """Construct the site extractor referenced as module:ClassName."""
    if config.extractor is None:
        raise ValueError(f"No extractor configured for site {config.name!r}")

    extractor_class = _import_extractor(config.extractor)
    return extractor_class(config)


def _import_extractor(reference: str) -> type[ProjectExtractor]:
    if ":" not in reference:
        raise ValueError(
            f"Invalid extractor {reference!r}; use module:ClassName"
        )
    module_name, class_name = reference.rsplit(":", 1)
    candidate = getattr(import_module(module_name), class_name)
    if not isinstance(candidate, type) or not issubclass(
        candidate,
        ProjectExtractor,
    ):
        raise TypeError(f"{reference!r} is not a ProjectExtractor subclass")
    return candidate

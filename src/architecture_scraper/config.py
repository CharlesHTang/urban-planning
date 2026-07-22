from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

import yaml

RenderMode: TypeAlias = Literal["never", "auto", "always"]


@dataclass(frozen=True, slots=True)
class SiteConfig:
    name: str
    projects_url: str
    adapter: str = "capture_only"
    listing_render: RenderMode = "never"
    detail_render: RenderMode = "never"
    concurrency: int = 5
    request_delay: float = 0.5
    timeout: float = 30.0
    impersonate: str = "chrome"


def load_sites(path: str | Path) -> list[SiteConfig]:
    """Load and validate site definitions without any parsing selectors."""
    with Path(path).open(encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict) or not isinstance(raw.get("sites"), list):
        raise ValueError("Configuration must contain a 'sites' list")

    sites = [_parse_site(item, index) for index, item in enumerate(raw["sites"])]
    names = [site.name for site in sites]
    if len(names) != len(set(names)):
        raise ValueError("Site names must be unique")
    return sites


def _parse_site(raw: Any, index: int) -> SiteConfig:
    context = f"sites[{index}]"
    item = _mapping(raw, context)
    return SiteConfig(
        name=_string(item, "name", context),
        projects_url=_string(item, "projects_url", context),
        adapter=_optional_string(item, "adapter", "capture_only", context),
        listing_render=_render_mode(item.get("listing_render", "never"), context),
        detail_render=_render_mode(item.get("detail_render", "never"), context),
        concurrency=_positive_int(item.get("concurrency", 5), f"{context}.concurrency"),
        request_delay=_non_negative_number(
            item.get("request_delay", 0.5), f"{context}.request_delay"
        ),
        timeout=_positive_number(item.get("timeout", 30), f"{context}.timeout"),
        impersonate=_optional_string(item, "impersonate", "chrome", context),
    )


def _render_mode(raw: Any, context: str) -> RenderMode:
    if raw not in {"never", "auto", "always"}:
        raise ValueError(
            f"{context} render modes must be never, auto, or always"
        )
    return cast(RenderMode, raw)


def _mapping(raw: Any, context: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{context} must be a mapping")
    return raw


def _string(raw: dict[str, Any], key: str, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _optional_string(
    raw: dict[str, Any], key: str, default: str, context: str
) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _positive_int(raw: Any, context: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
        raise ValueError(f"{context} must be a positive integer")
    return raw


def _positive_number(raw: Any, context: str) -> float:
    if not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw <= 0:
        raise ValueError(f"{context} must be a positive number")
    return float(raw)


def _non_negative_number(raw: Any, context: str) -> float:
    if not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw < 0:
        raise ValueError(f"{context} must be a non-negative number")
    return float(raw)


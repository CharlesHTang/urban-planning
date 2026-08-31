import json
import re
from collections.abc import Iterable
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .base import ProjectExtractor, clean_text
from .models import ExtractedProject, FactValue


class HtmlProjectExtractor(ProjectExtractor):
    """Small declarative base for the downloaded project HTML pages."""

    NAME_SELECTORS: tuple[str, ...] = ("h1",)
    HEADLINE_SELECTORS: tuple[str, ...] = ()
    DESCRIPTION_SELECTORS: tuple[str, ...] = ()
    LOCATION_SELECTORS: tuple[str, ...] = ()
    CLIENT_SELECTORS: tuple[str, ...] = ()
    STATUS_SELECTORS: tuple[str, ...] = ()
    SIZE_SELECTORS: tuple[str, ...] = ()
    SERVICES_SELECTORS: tuple[str, ...] = ()
    MARKETS_SELECTORS: tuple[str, ...] = ()
    TITLE_SUFFIXES: tuple[str, ...] = ()
    SOURCE_PATH_PATTERN: re.Pattern[str] | None = None

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        self._validate_source_url(source_url)
        soup = BeautifulSoup(html, "html.parser")
        facts = self.extract_facts(soup)

        name = self.extract_name(soup)
        headline = self.extract_headline(soup)
        if headline == name:
            headline = None

        description = self.extract_description(soup)
        warnings: list[str] = []
        if description is None:
            warnings.append("No substantive project description found")

        location = self.first_text(soup, self.LOCATION_SELECTORS) or fact_value(
            facts, "location", "project location", "place"
        )
        client = self.first_text(soup, self.CLIENT_SELECTORS) or fact_value(
            facts, "client", "clients"
        )
        status = self.first_text(soup, self.STATUS_SELECTORS) or fact_value(
            facts, "status", "project status", "completion", "completion date"
        )
        size = self.first_text(soup, self.SIZE_SELECTORS) or fact_value(
            facts, "size", "area"
        )

        services = self.list_text(soup, self.SERVICES_SELECTORS)
        if not services:
            services = split_fact_values(
                fact_value_raw(
                    facts,
                    "services",
                    "service",
                    "disciplines",
                    "expertise",
                    "markets/services",
                )
            )
        markets = self.list_text(soup, self.MARKETS_SELECTORS)
        if not markets:
            markets = split_fact_values(
                fact_value_raw(
                    facts,
                    "markets",
                    "market",
                    "sectors",
                    "sector",
                    "practice areas",
                    "markets/services",
                )
            )

        return ExtractedProject(
            project_name=name,
            headline=headline,
            description=description,
            location_raw=location,
            client_raw=client,
            status_raw=status,
            size_raw=size,
            services=services,
            markets=markets,
            facts=facts,
            warnings=warnings,
        )

    def _validate_source_url(self, source_url: str) -> None:
        if self.SOURCE_PATH_PATTERN is None:
            return
        if not self.SOURCE_PATH_PATTERN.fullmatch(urlparse(source_url).path):
            raise ValueError(f"Final URL is not a project detail page: {source_url}")

    def extract_name(self, soup: BeautifulSoup) -> str:
        name = self.first_text(soup, self.NAME_SELECTORS)
        if name:
            return name
        if soup.title is None:
            raise ValueError("Project page has no title")
        title = text_of(soup.title)
        for suffix in self.TITLE_SUFFIXES:
            if title.lower().endswith(suffix.lower()):
                title = title[: -len(suffix)].rstrip(" |-–—")
                break
        if not title:
            raise ValueError("Project page has no project name")
        return title

    def extract_headline(self, soup: BeautifulSoup) -> str | None:
        return self.first_text(soup, self.HEADLINE_SELECTORS)

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        parts: list[str] = []
        for selector in self.DESCRIPTION_SELECTORS:
            for node in soup.select(selector):
                paragraphs = node.select("p") if node.name != "p" else [node]
                values = [text_of(part) for part in paragraphs]
                if not any(values):
                    values = [text_of(node)]
                parts.extend(value for value in values if is_substantive(value))
        parts = dedupe(parts)
        if parts:
            return "\n\n".join(parts)
        return self.meta_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return {}

    @staticmethod
    def first_text(soup: BeautifulSoup | Tag, selectors: Iterable[str]) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            value = text_of(node)
            if value:
                return value
        return None

    @staticmethod
    def list_text(soup: BeautifulSoup | Tag, selectors: Iterable[str]) -> list[str]:
        values: list[str] = []
        for selector in selectors:
            values.extend(text_of(node) for node in soup.select(selector))
        return dedupe(value for value in values if value)

    @staticmethod
    def meta_description(soup: BeautifulSoup) -> str | None:
        node = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if node is None:
            node = soup.find("meta", attrs={"property": "og:description"})
        value = clean_text(node.get("content") if isinstance(node, Tag) else None)
        if value and is_substantive(value):
            return value
        return None

    @staticmethod
    def json_ld(soup: BeautifulSoup, schema_type: str) -> dict[str, object] | None:
        for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                payload = json.loads(node.string or node.get_text())
            except (TypeError, json.JSONDecodeError):
                continue
            for item in walk_json_objects(payload):
                item_type = item.get("@type")
                types = item_type if isinstance(item_type, list) else [item_type]
                if schema_type in types:
                    return item
        return None


def text_of(node: Tag | None) -> str:
    if node is None:
        return ""
    return clean_text(node.get_text(" ", strip=True)) or ""


def dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = clean_text(value)
        if cleaned and any(character.isalnum() for character in cleaned) and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def is_substantive(value: str) -> bool:
    normalized = value.strip().lower()
    return len(normalized) >= 40 and normalized not in {
        "no description.",
        "no description",
        "duis in libero consequat, placerat sapien at, rutrum diam. interdum et malesuada fames a ante ipsum.",
    }


def add_fact(facts: dict[str, FactValue], label: str, value: str | list[str]) -> None:
    key = (clean_text(label) or "").rstrip(":")
    values = value if isinstance(value, list) else [value]
    cleaned = dedupe(values)
    if not key or not cleaned:
        return
    new_value: FactValue = cleaned[0] if len(cleaned) == 1 else cleaned
    existing = facts.get(key)
    if existing is None:
        facts[key] = new_value
        return
    combined = split_fact_values(existing) + cleaned
    unique = dedupe(combined)
    facts[key] = unique[0] if len(unique) == 1 else unique


def facts_from_containers(
    root: BeautifulSoup | Tag,
    selector: str,
) -> dict[str, FactValue]:
    facts: dict[str, FactValue] = {}
    for container in root.select(selector):
        values = dedupe(
            clean_text(value) or "" for value in container.stripped_strings
        )
        if len(values) >= 2:
            add_fact(facts, values[0], values[1:])
    return facts


def facts_from_definition_lists(
    root: BeautifulSoup | Tag,
    selector: str = "dl",
) -> dict[str, FactValue]:
    facts: dict[str, FactValue] = {}
    for definition_list in root.select(selector):
        for term in definition_list.find_all("dt"):
            value = term.find_next_sibling("dd")
            if value is not None:
                add_fact(facts, text_of(term), text_of(value))
    return facts


def fact_value_raw(
    facts: dict[str, FactValue],
    *labels: str,
) -> FactValue | None:
    wanted = {label.casefold().rstrip(":") for label in labels}
    for key, value in facts.items():
        if key.casefold().rstrip(":") in wanted:
            return value
    return None


def fact_value(facts: dict[str, FactValue], *labels: str) -> str | None:
    value = fact_value_raw(facts, *labels)
    if isinstance(value, list):
        return "; ".join(value)
    return value


def split_fact_values(value: FactValue | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return dedupe(value)
    return dedupe(re.split(r"\s*[,;]\s*|\n+", value))


def walk_json_objects(value: object) -> Iterable[dict[str, object]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json_objects(child)


def html_fragment_text(value: str | None) -> str:
    if not value:
        return ""
    return text_of(BeautifulSoup(unescape(value), "html.parser"))

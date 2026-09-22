import json
import re

from bs4 import BeautifulSoup, Tag

from ..html import (
    HtmlProjectExtractor,
    add_fact,
    dedupe,
    fact_value_raw,
    split_fact_values,
    text_of,
)
from ..models import FactValue


class DarGroupExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".breadcrumb-item.active",)
    HEADLINE_SELECTORS = (".heading-with-description h2.title",)
    TITLE_SUFFIXES = ("Sidara", "Dar Group")
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        nodes = soup.select(
            "main #content .component.rich-text .component-content p, "
            "main #content .component.rich-text .component-content li, "
            "main #content .heading-with-description > .description, "
            "main #content .twocolumn_content > .description"
        )
        parts: list[str] = []
        for node in nodes:
            parent = node.find_parent(class_="twocolumn_content")
            heading = text_of(parent.select_one(".heading")) if parent else ""
            if heading.casefold() == "project details":
                continue
            value = text_of(node)
            if value:
                parts.append(value)
        values = dedupe(parts)
        if values:
            return "\n\n".join(values)
        return self.meta_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        fields = self._route_fields(soup)

        for field_name, label in (
            ("brand", "Brands"),
            ("geography", "Geography"),
            ("impact", "Impact"),
            ("sector", "Sectors"),
        ):
            add_fact(facts, label, self._item_titles(fields.get(field_name)))

        tags = fields.get("SxaTags")
        add_fact(facts, "Tags", self._item_titles(tags, title_key="Title"))

        markets = self._item_titles(fields.get("sector"))
        if not markets and isinstance(tags, list):
            markets = self._item_titles(
                [
                    item
                    for item in tags
                    if isinstance(item, dict)
                    and "/Sectors/" in str(item.get("url", ""))
                ],
                title_key="Title",
            )
        add_fact(facts, "Markets", markets)

        published = self._field_text(fields.get("date"))
        add_fact(facts, "Published", published or "")

        self._add_visible_project_details(soup, facts)
        if fact_value_raw(facts, "location") is None:
            geography = fact_value_raw(facts, "geography")
            if geography is not None:
                add_fact(facts, "Location", split_fact_values(geography))

        date = fact_value_raw(facts, "date")
        if date is not None and any(
            value.casefold().startswith("complet")
            for value in split_fact_values(date)
        ):
            add_fact(facts, "Status", split_fact_values(date))

        headings = self.list_text(
            soup,
            (
                "main #content .component.rich-text h2",
                "main #content .twocolumn_content > .heading",
                "main #content .one-column-text h2.title",
            ),
        )
        add_fact(
            facts,
            "Section headings",
            headings,
        )
        return facts

    @staticmethod
    def _route_fields(soup: BeautifulSoup) -> dict[str, object]:
        node = soup.select_one("script#__NEXT_DATA__")
        if node is None:
            return {}
        try:
            payload = json.loads(node.string or node.get_text())
            fields = payload["props"]["pageProps"]["layoutData"]["sitecore"][
                "route"
            ]["fields"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return {}
        return fields if isinstance(fields, dict) else {}

    @classmethod
    def _item_titles(
        cls,
        value: object,
        *,
        title_key: str = "title",
    ) -> list[str]:
        if not isinstance(value, list):
            return []
        titles: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            item_fields = item.get("fields")
            title = None
            if isinstance(item_fields, dict):
                title = cls._field_text(item_fields.get(title_key))
            if title is None:
                fallback = item.get("displayName") or item.get("name")
                title = fallback if isinstance(fallback, str) else None
            if title:
                titles.append(title)
        return dedupe(titles)

    @staticmethod
    def _field_text(value: object) -> str | None:
        if not isinstance(value, dict):
            return None
        field_value = value.get("value")
        return field_value.strip() if isinstance(field_value, str) else None

    @staticmethod
    def _add_visible_project_details(
        soup: BeautifulSoup,
        facts: dict[str, FactValue],
    ) -> None:
        for container in soup.select("main #content .twocolumn_content"):
            if text_of(container.select_one(".heading")).casefold() != (
                "project details"
            ):
                continue
            description = container.select_one(".description")
            if description is None:
                continue
            paragraphs = description.select("p")
            if paragraphs:
                for paragraph in paragraphs:
                    strings = list(paragraph.stripped_strings)
                    if len(strings) >= 2:
                        add_fact(
                            facts,
                            strings[0].rstrip(":"),
                            strings[1:],
                        )
                continue
            strings = list(description.stripped_strings)
            for index, value in enumerate(strings[:-1]):
                label = value.strip()
                if label.endswith(":"):
                    add_fact(facts, label, strings[index + 1])

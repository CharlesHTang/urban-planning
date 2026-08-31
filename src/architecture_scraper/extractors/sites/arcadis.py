import json
import re

from bs4 import BeautifulSoup

from ..html import (
    HtmlProjectExtractor,
    add_fact,
    dedupe,
    html_fragment_text,
    text_of,
)
from ..models import FactValue


class ArcadisExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ()
    DESCRIPTION_SELECTORS = ("main section p",)
    TITLE_SUFFIXES = ("| Arcadis  | Project | Arcadis", "| Project | Arcadis")
    SOURCE_PATH_PATTERN = re.compile(r"/en(?:-[a-z]{2})?/projects/.+")

    def extract_name(self, soup: BeautifulSoup) -> str:
        title = text_of(soup.title)
        name = title.split("|", 1)[0].strip()
        if not name:
            raise ValueError("Arcadis project page has no project name")
        return name

    def extract_headline(self, soup: BeautifulSoup) -> str | None:
        return html_fragment_text(str(self._data(soup).get("heading", ""))) or None

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        data = self._data(soup)
        parts: list[str] = []
        for prefix in ("challenge", "solution", "impact"):
            summary = html_fragment_text(str(data.get(f"{prefix}Summary", "")))
            if summary:
                parts.append(summary)
            details = data.get(f"{prefix}Detail", [])
            if isinstance(details, list):
                for item in details:
                    if isinstance(item, dict):
                        value = html_fragment_text(str(item.get("html", "")))
                        if value:
                            parts.append(value)
        values = dedupe(parts)
        return "\n\n".join(values) if values else super().extract_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        data = self._data(soup)
        facts: dict[str, FactValue] = {}
        add_fact(facts, "Client", str(data.get("clientName", "")))
        location = data.get("location")
        if isinstance(location, dict):
            address = location.get("address")
            if isinstance(address, dict):
                add_fact(
                    facts,
                    "Location",
                    [str(value) for value in address.values() if value],
                )
        sectors = data.get("industrySector")
        if isinstance(sectors, list):
            values = [
                str(item.get("title") or item.get("name") or "")
                for item in sectors
                if isinstance(item, dict)
            ]
            add_fact(facts, "Sectors", values)
        for item in data.get("impactAdditional", []):
            if not isinstance(item, dict):
                continue
            for stat in item.get("stats", []):
                if isinstance(stat, dict):
                    label = str(stat.get("description", ""))
                    value = f"{stat.get('value', '')}{stat.get('suffix', '')}"
                    add_fact(facts, label, value)
        return facts

    @staticmethod
    def _data(soup: BeautifulSoup) -> dict[str, object]:
        pattern = re.compile(
            r"React\.createElement\(Components\.ProjectPage,(\{.*?\})\)\);",
            re.S,
        )
        for node in soup.find_all("script"):
            match = pattern.search(node.string or node.get_text())
            if match:
                return json.loads(match.group(1))
        return {}

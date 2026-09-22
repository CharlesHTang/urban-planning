import re

from bs4 import BeautifulSoup, NavigableString, Tag

from ..html import HtmlProjectExtractor, add_fact, text_of
from ..models import FactValue


class StvExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("article.project h1", "main h1")
    DESCRIPTION_SELECTORS = (
        "article.project .dynamic-entry-content p, "
        "article.project .dynamic-entry-content li",
    )
    TITLE_SUFFIXES = ("STV",)
    SOURCE_PATH_PATTERN = re.compile(r"/project/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        root = soup.select_one(".stv-project-details")
        if root is None:
            return facts
        for heading in root.find_all(["h2", "h3", "h4"]):
            value = heading.find_next_sibling()
            if value is not None:
                add_fact(facts, text_of(heading), self._leading_text(value))
        return facts

    @staticmethod
    def _leading_text(node: Tag) -> str:
        parts: list[str] = []
        for child in node.children:
            if isinstance(child, Tag) and child.name in {"h2", "h3", "h4", "p"}:
                break
            if isinstance(child, (Tag, NavigableString)):
                parts.append(
                    child.get_text(" ", strip=True)
                    if isinstance(child, Tag)
                    else str(child)
                )
        return " ".join(parts)

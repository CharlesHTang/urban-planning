import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, dedupe, is_substantive, text_of
from ..models import FactValue


class ImegExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("article.project h1.entry-title",)
    DESCRIPTION_SELECTORS = (
        "article.project .project-content .main-content p, "
        "article.project .project-content .main-content li",
    )
    TITLE_SUFFIXES = ("IMEG",)
    SOURCE_PATH_PATTERN = re.compile(r"/project/[^/]+/?")

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        description = super().extract_description(soup)
        if description:
            return description
        parts = dedupe(
            text_of(node)
            for node in soup.select("article.project .main-content > div")
            if is_substantive(text_of(node))
        )
        return "\n\n".join(parts) or None

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        article = soup.select_one("article.project")
        classes = article.get("class", []) if article is not None else []
        markets = self._taxonomy_values(classes, "project_market-")
        services = self._taxonomy_values(classes, "project_service-")
        add_fact(facts, "Markets", markets)
        add_fact(facts, "Services", services)
        return facts

    @staticmethod
    def _taxonomy_values(classes: object, prefix: str) -> list[str]:
        if not isinstance(classes, list):
            return []
        return [
            value.removeprefix(prefix).replace("-", " ").title()
            for value in classes
            if isinstance(value, str) and value.startswith(prefix)
        ]

import re

from bs4 import BeautifulSoup

from ..html import (
    HtmlProjectExtractor,
    add_fact,
    facts_from_definition_lists,
)
from ..models import FactValue


class JacobsExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ()
    HEADLINE_SELECTORS = ("#block-jacobs-content h1",)
    DESCRIPTION_SELECTORS = ("#block-jacobs-content section:not(.content-header) p",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_name(self, soup: BeautifulSoup) -> str:
        project = self.json_ld(soup, "Project")
        name = project.get("name") if project else None
        if not isinstance(name, str) or not name.strip():
            return super().extract_name(soup)
        return name.strip()

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_definition_lists(soup, "#block-jacobs-content dl")
        project = self.json_ld(soup, "Project") or {}
        topics = project.get("about")
        if isinstance(topics, list):
            add_fact(
                facts,
                "Markets",
                [
                    str(item.get("name", ""))
                    for item in topics
                    if isinstance(item, dict)
                ],
            )
        return facts

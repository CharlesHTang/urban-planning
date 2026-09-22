import re

from bs4 import BeautifulSoup

from ..html import (
    HtmlProjectExtractor,
    dedupe,
    facts_from_definition_lists,
    is_substantive,
    text_of,
)
from ..models import FactValue


class BhArchitectsExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ()
    DESCRIPTION_SELECTORS = (
        "article.section .context-case_study p, "
        "article.section .context-case_study li",
    )
    TITLE_SUFFIXES = ("B+H Architects",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/project/[^/]+/?")

    def extract_name(self, soup: BeautifulSoup) -> str:
        title = text_of(soup.title)
        return (
            title.rsplit(" - B+H Architects", 1)[0].strip()
            or super().extract_name(soup)
        )

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        description = super().extract_description(soup)
        if description:
            return description
        parts = dedupe(
            text_of(node)
            for node in soup.select(".project-summary .project-meta p")
            if is_substantive(text_of(node))
        )
        return "\n\n".join(parts) or None

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_definition_lists(soup, ".project-summary dl")

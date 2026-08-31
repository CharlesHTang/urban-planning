import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, text_of
from ..models import FactValue


class SmithGroupExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("article.node-display-full h1",)
    DESCRIPTION_SELECTORS = ("article.node-display-full .layout--regular p",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        labels = {"client", "location", "markets/services", "size"}
        for heading in soup.select("article.node-display-full h3"):
            label = text_of(heading).rstrip(":")
            if label.casefold() not in labels:
                continue
            value = heading.find_next_sibling("p")
            add_fact(facts, label, text_of(value))
        return facts

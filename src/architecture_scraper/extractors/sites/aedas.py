import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_definition_lists
from ..models import FactValue


class AedasExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1", "h1")
    DESCRIPTION_SELECTORS = (".project-content article p", ".project-content p")
    TITLE_SUFFIXES = ("Aedas",)
    SOURCE_PATH_PATTERN = re.compile(r"/(?:en|sc)/project/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_definition_lists(soup, ".project-details dl")
        for label, value in tuple(facts.items()):
            if "area" in label.casefold():
                facts.setdefault("Size", value)
            if "completion" in label.casefold():
                facts.setdefault("Completion", value)
        return facts

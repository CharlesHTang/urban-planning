import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, facts_from_containers
from ..models import FactValue


class SomExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".hero-project__title",)
    DESCRIPTION_SELECTORS = ("main.main p",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(soup, ".hero-project__details__meta li")
        detail_facts = facts_from_containers(soup, ".rail-facts__item")
        for label, value in detail_facts.items():
            add_fact(facts, label, value if isinstance(value, list) else str(value))
        return facts

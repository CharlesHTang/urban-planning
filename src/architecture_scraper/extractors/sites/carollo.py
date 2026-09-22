import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class CarolloExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    HEADLINE_SELECTORS = ("main .caro-text--content-l",)
    DESCRIPTION_SELECTORS = (
        "main .caro-text--content-l p",
        "main .caro-columns--two p, main .caro-columns--two li",
        "main .caro-block--columns-flex-container h3",
    )
    TITLE_SUFFIXES = ("Carollo",)
    SOURCE_PATH_PATTERN = re.compile(r"/solutions/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(
            soup,
            ".caro-hero-flex--grid [data-g='c'], "
            ".caro-hero-flex--grid [data-g='d'], "
            ".caro-hero-flex--grid [data-g='e']",
        )
        solutions = facts.get("Solutions")
        if solutions is not None:
            facts["Services"] = solutions
        return facts

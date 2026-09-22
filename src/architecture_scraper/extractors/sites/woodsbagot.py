import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class WoodsBagotExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".blok.project-name", ".project-name")
    HEADLINE_SELECTORS = (
        ".row-project-primary .tagline",
        ".row-project-primary h1",
    )
    DESCRIPTION_SELECTORS = (
        ".row-project-primary > .container-fluid.iv p, "
        ".row-project-primary > .container-fluid.iv li",
    )
    MARKETS_SELECTORS = (".row-project-primary > .container-fluid.inv h4 a",)
    TITLE_SUFFIXES = ("Woods Bagot",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(soup, ".detail-table .detail-row")
        scope = facts.get("Scope")
        if scope is not None:
            facts["Services"] = scope
        return facts

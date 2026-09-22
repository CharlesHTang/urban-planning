import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class MBakerIntlExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = (
        "main section.grid-2col-80-20 > article p, "
        "main section.grid-2col-80-20 > article li",
    )
    TITLE_SUFFIXES = ("Michael Baker International",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts = facts_from_containers(soup, "aside.project-details li")
        services = facts.get("Related Services")
        markets = facts.get("Related Markets")
        if services is not None:
            facts["Services"] = services
        if markets is not None:
            facts["Markets"] = markets
        return facts

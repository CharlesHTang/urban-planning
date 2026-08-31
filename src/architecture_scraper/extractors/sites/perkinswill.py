import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class PerkinsWillExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".post-title",)
    HEADLINE_SELECTORS = (".project-subtitle",)
    DESCRIPTION_SELECTORS = (".project-description",)
    LOCATION_SELECTORS = (".overview-section .project-location",)
    SOURCE_PATH_PATTERN = re.compile(r"/project/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".project-metadata li")

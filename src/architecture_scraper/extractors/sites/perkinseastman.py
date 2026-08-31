import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class PerkinsEastmanExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".heroProjects-primaryHeading",)
    DESCRIPTION_SELECTORS = (".heroProjects-inner-content p",)
    LOCATION_SELECTORS = (".heroProjects-inner-content h3",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        project_facts = soup.select_one(".metaAccordion")
        if project_facts is None:
            return {}
        return facts_from_containers(project_facts, ".metaAccordion-item")

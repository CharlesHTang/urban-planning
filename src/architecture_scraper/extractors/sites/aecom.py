import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class AecomExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = (".aecom-main-content",)
    LOCATION_SELECTORS = (".project-location",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".sidebar-item.side-project-services")

import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class SwecoExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".a-showroom-intro__intro--title",)
    HEADLINE_SELECTORS = (".a-showroom-intro__intro .preamble",)
    DESCRIPTION_SELECTORS = ("main .editor-content p",)
    SOURCE_PATH_PATTERN = re.compile(r"/portfolio/.+")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".a-showroom-intro__facts li")

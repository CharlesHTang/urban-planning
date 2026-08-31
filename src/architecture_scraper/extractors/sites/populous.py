import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class PopulousExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("#modal h1",)
    DESCRIPTION_SELECTORS = ("#modal .c-content p", "#modal > p")
    LOCATION_SELECTORS = ("#modal .c-list-item_col.-location",)
    SOURCE_PATH_PATTERN = re.compile(r"/(?:[a-z]{2}/)?(?:projects|showcases)/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, "#modal .c-listing-table_item")

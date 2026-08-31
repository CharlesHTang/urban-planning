import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class HokExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main.projects.project_detail h1",)
    DESCRIPTION_SELECTORS = ("main.projects.project_detail p",)
    LOCATION_SELECTORS = ("main.projects.project_detail header .block-quarter.body-text",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/view/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(
            soup,
            "main.projects.project_detail .block-half.border",
        )

import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_definition_lists
from ..models import FactValue


class RambollExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = ("main p",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_definition_lists(soup, "main aside")

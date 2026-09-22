import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_definition_lists
from ..models import FactValue


class BvExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = ("main p",)
    TITLE_SUFFIXES = ("Black & Veatch",)
    SOURCE_PATH_PATTERN = re.compile(
        r"/(?:[a-z]{2}-[A-Z]{2}/)?projects/[^/]+/?"
    )

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_definition_lists(soup, "main dl")

import re

from bs4 import BeautifulSoup

from ..base import clean_text
from ..html import HtmlProjectExtractor


class DpaExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".pm__project-name",)
    HEADLINE_SELECTORS = (".pm__title",)
    DESCRIPTION_SELECTORS = (".prj__description p",)
    LOCATION_SELECTORS = (".pm__location",)
    TITLE_SUFFIXES = ("DP Architects",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

    def extract_name(self, soup: BeautifulSoup) -> str:
        node = soup.select_one(self.NAME_SELECTORS[0])
        if node is not None:
            values = [clean_text(value) for value in node.stripped_strings]
            if values and values[0]:
                return values[0]
        return super().extract_name(soup)

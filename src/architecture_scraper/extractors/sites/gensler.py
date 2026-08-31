import re

from ..html import HtmlProjectExtractor


class GenslerExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".detail-layout__title h1",)
    DESCRIPTION_SELECTORS = (".detail-layout__content__copy",)
    LOCATION_SELECTORS = (".detail-layout__content__subtitle",)
    MARKETS_SELECTORS = (".detail-layout__content__col--side a",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")

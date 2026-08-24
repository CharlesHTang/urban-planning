import re

from ..sitemap import SitemapProjectAdapter


class HksAdapter(SitemapProjectAdapter):
    SITE_LABEL = "HKS"
    HOST = "www.hksinc.com"
    CAPTURE_LISTING_PAGE = False
    SITEMAP_URLS = ("https://www.hksinc.com/case_study-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(
        r"^/what-we-do/projects/[^/]+/?$"
    )

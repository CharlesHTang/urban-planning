import re

from ..sitemap import SitemapProjectAdapter


class BvAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Black & Veatch"
    HOST = "www.bv.com"
    SITEMAP_URLS = ("https://www.bv.com/en-US/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")

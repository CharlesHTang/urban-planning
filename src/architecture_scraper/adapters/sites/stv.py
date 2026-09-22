import re

from ..sitemap import SitemapProjectAdapter


class StvAdapter(SitemapProjectAdapter):
    SITE_LABEL = "STV"
    HOST = "stvinc.com"
    LISTING_URL = "https://stvinc.com/our-portfolio/"
    SITEMAP_URLS = ("https://stvinc.com/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/project/[^/]+/?$")

import re

from ..sitemap import SitemapProjectAdapter


class RoyalHaskoningDhvAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Royal HaskoningDHV"
    HOST = "www.haskoning.com"
    LISTING_URL = "https://www.haskoning.com/en/projects"
    SITEMAP_URLS = ("https://www.haskoning.com/en/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/en/projects/[^/]+/?$")

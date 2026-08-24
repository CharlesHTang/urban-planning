import re

from ..sitemap import SitemapProjectAdapter


class SmithGroupAdapter(SitemapProjectAdapter):
    SITE_LABEL = "SmithGroup"
    HOST = "www.smithgroup.com"
    LISTING_URL = "https://www.smithgroup.com/our-work/projects"
    SITEMAP_INDEX_URL = "https://www.smithgroup.com/sitemap.xml"
    SITEMAP_URL_PATTERN = re.compile(
        r"^https://www\.smithgroup\.com/sitemap\.xml\?page=\d+$"
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")

import re

from ..sitemap import SitemapProjectAdapter


class SomAdapter(SitemapProjectAdapter):
    SITE_LABEL = "SOM"
    HOST = "www.som.com"
    CAPTURE_LISTING_PAGE = False
    SITEMAP_URLS = ("https://www.som.com/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")

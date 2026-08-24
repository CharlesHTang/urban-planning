import re

from ..sitemap import SitemapProjectAdapter


class PopulousAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Populous"
    HOST = "populous.com"
    SITEMAP_URLS = ("https://populous.com/app_project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(
        r"^/(?:projects|showcases)/[^/]+/?$"
    )

import re

from ..sitemap import SitemapProjectAdapter


class WoodsBagotAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Woods Bagot"
    HOST = "www.woodsbagot.com"
    SITEMAP_URLS = (
        "https://www.woodsbagot.com/sitemap-posttype-projects.xml",
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")

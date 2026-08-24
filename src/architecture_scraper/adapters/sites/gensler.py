import re

from ..sitemap import SitemapProjectAdapter


class GenslerAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Gensler"
    HOST = "www.gensler.com"
    SITEMAP_URLS = ("https://www.gensler.com/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
    EXCLUDED_PROJECT_PATHS = frozenset({"/projects/all", "/projects/all/"})

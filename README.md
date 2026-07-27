# Architecture Scraper

This package captures complete, unparsed HTML pages. It assumes that the main
projects-page URL is known for every website, while project detail URLs may not
be known yet.

The package deliberately separates two concerns:

- Shared code handles `curl_cffi`, Playwright lifecycle, rate limiting,
  concurrency, raw HTML storage, manifests, and errors.
- A site adapter handles only behavior unique to one website, such as clicking
  “show more,” scrolling, intercepting an API response, or discovering links.

There are no CSS selectors in the shared configuration.

## Install

```bash
python -m venv venv
venv/bin/pip install -e '.[test]'
venv/bin/playwright install chromium
```

## Stage 1: capture the known projects pages

Copy `sites.example.yml` to `sites.yml` and add the known projects-page URL for
each site. Initially, use `capture_only`:

```yaml
sites:
  - name: example-architects
    projects_url: https://example.com/projects
    adapter: capture_only
    listing_render: never
    detail_render: never
```

Then run:

```bash
venv/bin/architecture-scraper collect sites.yml -o raw-pages
```

By default, `collect` runs every site in the configuration. To run only one
configured site, select it by its `name`:

```bash
venv/bin/architecture-scraper collect sites.yml --site aecom -o raw-pages
```

`capture_only` retrieves the entire projects page and does no parsing. Output is
organized as:

```text
raw-pages/
├── manifest.jsonl
└── example-architects/
    ├── listing/
    │   └── <url-hash>.html
    └── project_urls.txt
```

The manifest records the requested URL, final URL, page type, file path, and
capture time. It is append-only, while a page with the same requested URL keeps
the same HTML filename.

## Stage 2: fetch detail pages after URL discovery

Parse the captured listing separately and put the resulting detail URLs in a
text file, one URL per line. Then fetch their complete HTML:

```bash
venv/bin/architecture-scraper fetch-details \
  sites.yml \
  example-architects \
  example-project-urls.txt \
  -o raw-pages
```

The detail HTML is saved under `raw-pages/example-architects/detail/`. It is not
parsed or transformed.

## Adding an individualized site adapter

Create one module per site under `src/architecture_scraper/adapters/sites/`.
An adapter may use ordinary HTTP, a fully controllable Playwright page, or both:

```python
from architecture_scraper.adapters import SiteAdapter
from architecture_scraper.fetcher import Fetcher
from architecture_scraper.models import DiscoveryResult


class MyStudioAdapter(SiteAdapter):
    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        async with fetcher.browser_page(self.config.projects_url) as page:
            # Put this site's clicks, scrolling, waits, or network handling here.
            # No shared selector configuration is required.

            listing = await self.listing_from_page(page)
            project_urls = []  # Add this site's discovery logic when ready.

        return DiscoveryResult([listing], project_urls)
```

Reference it in YAML by import path:

```yaml
adapter: architecture_scraper.adapters.sites.my_studio:MyStudioAdapter
```

Once an adapter returns detail URLs, the normal `collect` command automatically
deduplicates them, writes `project_urls.txt`, fetches all detail pages with
bounded concurrency, and saves their complete HTML.

## AECOM

The included AECOM adapter uses the site's public, paginated WordPress project
API to discover canonical detail URLs. It does not depend on the visible “Show
More” button or its HTML classes. Run it with the included `sites.yml`:

```bash
venv/bin/architecture-scraper collect sites.yml -o raw-pages
```

AECOM currently publishes well over one thousand project pages, so a complete
run will take time. Successful detail responses are saved immediately; an
individual failed detail request is reported without discarding other pages.

## WSP Global

The WSP adapter discovers `en-gl` project detail URLs from WSP's public sitemap.
This avoids the Cloudflare-protected interactive projects index. WSP's robots
policy specifies a three-second crawl delay, which is reflected in `sites.yml`.

Run only WSP with:

```bash
venv/bin/architecture-scraper collect sites.yml --site wsp -o raw-pages
```

The adapter stores the source sitemap as the listing record, writes the
discovered URLs to `raw-pages/wsp/project_urls.txt`, and saves complete detail
HTML under `raw-pages/wsp/detail/`.

## Arcadis

The Arcadis adapter uses the public search endpoint behind Arcadis's
global-English "All Projects" grid. It paginates through the current grid and
downloads the complete HTML for each returned project detail page.

Run only Arcadis with:

```bash
venv/bin/architecture-scraper collect sites.yml --site arcadis -o raw-pages
```

The projects page is stored as the listing record, discovered URLs are written
to `raw-pages/arcadis/project_urls.txt`, and complete detail HTML is saved under
`raw-pages/arcadis/detail/`.

## Jacobs

The Jacobs adapter follows the ordinary HTML pagination behind Jacobs's project
grid. It saves every listing page, validates direct `/projects/{slug}` links,
and downloads one complete HTML file for each unique linked detail page.

Run only Jacobs with:

```bash
venv/bin/architecture-scraper collect sites.yml --site jacobs -o raw-pages
```

The listing pages are saved under `raw-pages/jacobs/listing/`, discovered URLs
are written to `raw-pages/jacobs/project_urls.txt`, and complete detail HTML is
saved under `raw-pages/jacobs/detail/`.

## Rendering modes

- `never`: use only `curl_cffi`.
- `always`: use Playwright.
- `auto`: try `curl_cffi`, falling back to Playwright only if HTTP fetching
  fails. Without parsing rules, the shared code cannot determine whether an
  HTTP response is missing JavaScript-rendered content.

For dynamic listing pages, prefer a custom adapter using `browser_page()` so it
can explicitly decide when clicking or scrolling is complete.

Before collecting a site, confirm that collection is permitted and use a
respectful `request_delay`.

## Test

```bash
venv/bin/pytest
```

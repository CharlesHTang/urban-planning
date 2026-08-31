# Architecture Scraper

This package captures complete HTML pages and provides a shared layer for
extracting structured project records from them. It assumes that the main
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

## Extract downloaded detail pages

Extraction follows the same shared-versus-site-specific split as downloading:

- Shared code reads detail entries from `raw-pages/manifest.jsonl`, opens local
  HTML, validates records, attaches provenance, and writes JSONL.
- A site extractor contains only that website's HTML selectors and returns an
  `ExtractedProject`.

Create a site extractor by subclassing `ProjectExtractor`:

```python
from architecture_scraper.extractors import ExtractedProject, ProjectExtractor


class MyStudioExtractor(ProjectExtractor):
    VERSION = 1

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        # Parse this site's HTML and return its project fields here.
        return ExtractedProject(
            project_name="Example project",
            description="Complete extracted description",
            location_raw="City, Country",
            services=["Architecture"],
        )
```

Reference it in the site's YAML entry:

```yaml
extractor: architecture_scraper.extractors.sites.my_studio:MyStudioExtractor
```

Then extract one site:

```bash
venv/bin/architecture-scraper extract \
  sites.yml \
  --site my-studio \
  --raw raw-pages \
  -o extracted
```

Omit `--site` to run every site that has a configured extractor:

```bash
venv/bin/architecture-scraper extract sites.yml --raw raw-pages -o extracted
```

Output is deterministic and is replaced on each run:

```text
extracted/
└── my-studio/
    ├── my-studio_projects.jsonl
    └── my-studio_errors.jsonl
```

Each successful record includes the extracted fields plus `firm`, final and
requested source URLs, raw source file, capture timestamp, scrape date, and
extractor version. One malformed page is written to the errors file without
stopping extraction of the remaining pages. Repeated manifest entries and
redirect aliases for the same final URL are processed once using their latest
metadata.

The shared layer uses Beautiful Soup for safe HTML parsing while each site
extractor owns the selectors and embedded-data rules unique to that website.

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

## AtkinsRéalis

The AtkinsRéalis adapter paginates through the public GET API behind the
global-English project grid. It validates the returned project links and
downloads each complete detail page using Safari-impersonated HTTP requests.

Run only AtkinsRéalis with:

```bash
venv/bin/architecture-scraper collect sites.yml --site atkinsrealis -o raw-pages
```

The projects page is stored as the listing record, discovered URLs are written
to `raw-pages/atkinsrealis/project_urls.txt`, and complete detail HTML is saved
under `raw-pages/atkinsrealis/detail/`.

## Archello

The Archello adapter reads the project-only sitemap shards declared by the
site's public sitemap index. This avoids thousands of HTML listing pages and
discovers direct `/project/{slug}` detail URLs without CSS selectors or browser
rendering.

Run only Archello with:

```bash
venv/bin/architecture-scraper collect sites.yml --site archello -o raw-pages
```

Archello is an industry-wide project platform rather than one design firm and
publishes well over 100,000 project pages. A complete run will therefore take
many hours and may require tens of gigabytes of storage. Its one-second robots
crawl delay is reflected in `sites.yml`.

## Stantec

The Stantec adapter paginates through the public GET endpoint behind the global
project grid. It uses the API's reported page number and total rather than
assuming a fixed number of projects per response, validates every returned
Stantec detail URL, and downloads the complete server-rendered HTML.

Run only Stantec with:

```bash
venv/bin/architecture-scraper collect sites.yml --site stantec -o raw-pages
```

The projects page is stored as the listing record, discovered URLs are written
to `raw-pages/stantec/project_urls.txt`, and complete detail HTML is saved under
`raw-pages/stantec/detail/`.

## Arup

The Arup adapter paginates through the public JSON endpoint behind the US
English "All projects" grid. It sends the same project-only filter as the
frontend, validates each direct `/en-us/projects/{slug}/` URL, and downloads
the complete server-rendered project HTML without Playwright.

Run only Arup with:

```bash
venv/bin/architecture-scraper collect sites.yml --site arup -o raw-pages
```

The projects page is stored as the listing record, discovered URLs are written
to `raw-pages/arup/project_urls.txt`, and complete detail HTML is saved under
`raw-pages/arup/detail/`.

## HDR

The HDR adapter reads the public sitemap index and filters its sitemap pages
for direct `/portfolio/{slug}` URLs. This avoids the query-string pagination
that HDR disallows in `robots.txt` and downloads the complete server-rendered
portfolio HTML without Playwright.

Run only HDR with:

```bash
venv/bin/architecture-scraper collect sites.yml --site hdr -o raw-pages
```

The portfolio page is stored as the listing record, discovered URLs are written
to `raw-pages/hdr/project_urls.txt`, and complete detail HTML is saved under
`raw-pages/hdr/detail/`.

## Sweco

The Sweco adapter reads the sitemap index declared in `robots.txt`, selects its
numbered `showroom_cpt` portfolio sitemaps, and validates direct
`/portfolio/{category}/{slug}/` URLs. Both listing and detail pages contain
complete server-rendered HTML, so Playwright is not needed.

Run only Sweco with:

```bash
venv/bin/architecture-scraper collect sites.yml --site sweco -o raw-pages
```

The portfolio page is stored as the listing record, discovered URLs are written
to `raw-pages/sweco/project_urls.txt`, and complete detail HTML is saved under
`raw-pages/sweco/detail/`.

## Additional project adapters

The following adapters use each firm's public XML sitemap and strict project
URL patterns. The counts below are live verification results from August 2026;
they are not hard-coded and may change when a firm updates its portfolio.

| Site name | Discovery source | Verified URLs |
| --- | --- | ---: |
| `ramboll` | Global URL sitemap filtered to `/projects/{category}/{slug}` | 197 |
| `gensler` | Main sitemap filtered to direct `/projects/{slug}` pages | 2,199 |
| `perkinswill` | Dedicated `project-sitemap.xml` | 588 |
| `hks` | Dedicated `case_study-sitemap.xml` | 396 |
| `hok` | Two overlapping `projects-sitemap` files | 385 |
| `dlrgroup` | Dedicated `project-sitemap.xml` | 506 |
| `som` | Dedicated `project-sitemap.xml` with duplicate removal | 540 |
| `mottmac` | English sitemap filtered to `/en/projects/{slug}` | 239 |
| `perkinseastman` | Dedicated `projects-sitemap.xml` | 594 |
| `populous` | Project sitemap filtered to English `/projects` and `/showcases` pages | 295 |
| `smithgroup` | Paginated sitemap filtered to `/projects/{slug}` | 435 |

Run any one with its site name:

```bash
venv/bin/architecture-scraper collect sites.yml --site ramboll -o raw-pages
```

The supplied HKS, DLR Group, SOM, and SmithGroup listing routes have changed or
redirect elsewhere. Their adapters therefore use current canonical listing
pages where available or store the project sitemap as the listing record. HKS
specifies a 600-second crawl delay and SOM specifies a 10-second delay in
`robots.txt`; both delays are reflected in `sites.yml` and make their complete
downloads substantially slower.

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

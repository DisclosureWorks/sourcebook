Parallax public site builder

Renders either public repository's Markdown into a static site in _site/ for Cloudflare Pages.
Use the command for the repository being built:

    python3 .site-build/build.py --src . --out _site --surface atlas --base-url https://sourcebook.disclosureworks.ai
    python3 .site-build/build.py --src . --out _site --surface publications --base-url https://publications.disclosureworks.ai

Requires Python 3.12 and pandoc 3.x. The build skips hidden paths (this folder included) and refuses to
clear an output folder that does not hold a previous build. Output is deterministic: the same input gives
byte-identical files. Tests: python3 -m pytest -q .site-build/tests.

Markdown sources are also served verbatim at their original paths for downloads and manifest hashes.
Every rendered page has an absolute canonical URL using the same normalized base URL and route as the sitemap.

Topic pages: pass --areas <topic registry JSON> and --page-areas <page-to-topic map JSON>. A map entry
matches a page by its public_id, its path, or its file name without .md. Add --strict-page-areas so an
entry that matches no page fails the build instead of leaving a topic page short. These topic options
apply to the atlas surface.

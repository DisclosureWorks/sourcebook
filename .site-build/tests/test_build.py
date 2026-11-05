from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest


BUILD_ROOT = Path(__file__).resolve().parents[1]
BUILD = BUILD_ROOT / "build.py"


def run_build(
    src: Path,
    out: Path,
    surface: str = "atlas",
    *extra: str, supply_feed: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BUILD),
            "--src",
            str(src),
            "--out",
            str(out),
            "--surface",
            surface,
            "--base-url",
            f"https://{'atlas' if surface == 'atlas' else 'parallax'}.example.test",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def supply_test_feed(src):
    if (src / 'editions').is_dir() and any(p.name >= '2026-11' for p in (src / 'editions').iterdir()):
        feed = src / 'feed.xml'
        if not feed.exists():
            feed.write_text('<feed xmlns="http://www.w3.org/2005/Atom"><id>https://example.test/feed.xml</id><title>Fixture</title><updated>2026-11-05T00:00:00Z</updated><entry><id>https://example.test/editions/2026-11/</id><title>2026-11</title><updated>2026-11-05T00:00:00Z</updated></entry></feed>')

def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_base_fixture(src: Path) -> None:
    (src / "editions" / "2026-10").mkdir(parents=True)
    (src / "docs").mkdir()
    (src / ".git").mkdir()
    (src / ".hidden.md").write_text("# Hidden\n", encoding="utf-8")
    (src / ".git" / "config").write_text("not published\n", encoding="utf-8")
    (src / "LICENSE").write_text("Synthetic license\n", encoding="utf-8")
    (src / "data.json").write_text('{"ok": true}\n', encoding="utf-8")
    (src / "CITATION.md").write_text("# Citation Guide\n", encoding="utf-8")
    (src / "corrections-removal.md").write_text("# Corrections and Removal\n", encoding="utf-8")
    (src / "latest").mkdir()
    (src / "latest" / "index.md").write_text(
        "# Latest\n\nSee [the edition](../editions/2026-10/index.md).\n",
        encoding="utf-8",
    )
    (src / "editions" / "2026-10" / "index.md").write_text(
        "# Edition 2026-10\n\nSee [One](../../docs/one.md).\n",
        encoding="utf-8",
    )
    (src / "docs" / "one.md").write_text(
        """---
title: Plain One
---
# Ignored Heading

Raw HTML is disabled: <em>not markup</em>.

| A | B |
|---|---|
| 1 | 2 |

A note.[^1]

[^1]: Synthetic footnote.
""",
        encoding="utf-8",
    )


def test_build_is_deterministic_and_complete(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_base_fixture(src)
    first, second = tmp_path / "one", tmp_path / "two"

    result = run_build(src, first, "publications")
    assert result.returncode == 0, result.stderr
    result = run_build(src, second, "publications")
    assert result.returncode == 0, result.stderr
    assert tree_hashes(first) == tree_hashes(second)

    assert (first / "index.html").is_file()
    assert (first / "docs" / "one" / "index.html").is_file()
    assert (first / "editions" / "index.html").is_file()
    assert (first / "LICENSE").read_text(encoding="utf-8") == "Synthetic license\n"
    assert (first / "data.json").is_file()
    assert not (first / ".hidden.md").exists()
    for source in src.rglob("*.md"):
        if not source.name.startswith("."):
            assert (first / source.relative_to(src)).read_bytes() == source.read_bytes()

    edition = (first / "editions" / "2026-10" / "index.html").read_text(encoding="utf-8")
    assert 'href="/docs/one/"' in edition
    assert "Edition 2026-10" in edition
    page = (first / "docs" / "one" / "index.html").read_text(encoding="utf-8")
    assert "Plain One — DisclosureWorks Publications" in page
    assert "title: Plain One" not in page
    assert "<table>" in page
    assert "footnote" in page.lower()
    assert "<em>not markup</em>" not in page
    assert "&lt;em&gt;" in page
    assert "<script" not in page.lower()

    headers = (first / "_headers").read_text(encoding="utf-8")
    assert "default-src 'self'" in headers
    assert "X-Content-Type-Options: nosniff" in headers
    assert "Referrer-Policy: no-referrer" in headers
    assert "X-Frame-Options: DENY" in headers
    assert "https://parallax.example.test/docs/one/" in (
        first / "sitemap.xml"
    ).read_text(encoding="utf-8")
    manifest = json.loads((first / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["pandoc_version"].startswith("pandoc 3.")
    assert "src/docs/one.md" in manifest["inputs"]
    assert "docs/one/index.html" in manifest["outputs"]
    assert "build-manifest.json" in manifest["outputs"]


def test_nonempty_non_build_output_is_refused_without_deletion(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_base_fixture(src)
    out = tmp_path / "not-a-build"
    (out / "nested").mkdir(parents=True)
    keep = out / "nested" / "keep.txt"
    keep.write_text("user data\n", encoding="utf-8")

    result = run_build(src, out, "publications")

    assert result.returncode == 1
    assert str(out) in result.stderr
    assert "OUT" in result.stderr and "build-manifest.json" in result.stderr
    assert len(result.stderr.splitlines()) == 1
    assert keep.read_text(encoding="utf-8") == "user data\n"
    assert sorted(path.relative_to(out).as_posix() for path in out.rglob("*")) == [
        "nested",
        "nested/keep.txt",
    ]


def test_empty_output_and_previous_build_are_allowed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    write_base_fixture(src)
    out = tmp_path / "out"
    out.mkdir()

    first = run_build(src, out, "publications")
    assert first.returncode == 0, first.stderr
    assert (out / "build-manifest.json").is_file()

    stale = out / "stale.txt"
    stale.write_text("remove me\n", encoding="utf-8")
    second = run_build(src, out, "publications")
    assert second.returncode == 0, second.stderr
    assert not stale.exists()
    assert (out / "build-manifest.json").is_file()


@pytest.mark.parametrize(
    ("surface", "site_title"),
    [
        ("atlas", "DisclosureWorks Sourcebook"),
        ("publications", "DisclosureWorks Publications"),
    ],
)
def test_home_page_title_does_not_repeat_site_title(
    tmp_path: Path, surface: str, site_title: str
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    result = run_build(src, tmp_path / "out", surface)
    assert result.returncode == 0, result.stderr

    home = (tmp_path / "out" / "index.html").read_text(encoding="utf-8")
    assert f"<title>{site_title}</title>" in home
    assert f"{site_title} — {site_title}" not in home


def test_area_hubs_include_open_descendants_and_mapping(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "editions" / "2026-10").mkdir(parents=True)
    (src / "editions" / "2026-10" / "index.md").write_text("# Edition\n", encoding="utf-8")
    (src / "editions/2026-10/direct.md").write_text(
        "---\ntitle: Direct\npublic_id: atlas-direct\nareas: [oversight]\n---\n\n# Direct\n",
        encoding="utf-8",
    )
    (src / "editions/2026-10/mapped.md").write_text(
        "---\ntitle: Mapped\npublic_id: atlas-mapped\n---\n\n# Mapped\n",
        encoding="utf-8",
    )
    areas = tmp_path / "areas.json"
    areas.write_text(
        json.dumps(
            [
                {"slug": "oversight", "title": "Oversight", "parent": None, "status": "open"},
                {
                    "slug": "oversight/iran-contra",
                    "title": "Iran-Contra",
                    "parent": "oversight",
                    "status": "open",
                },
                {"slug": "closed", "title": "Closed", "parent": None, "status": "closed"},
            ]
        ),
        encoding="utf-8",
    )
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"atlas-mapped": ["oversight/iran-contra"]}), encoding="utf-8")
    out = tmp_path / "out"

    result = run_build(src, out, "atlas", "--areas", str(areas), "--page-areas", str(mapping))
    assert result.returncode == 0, result.stderr
    parent = (out / "areas" / "oversight" / "index.html").read_text(encoding="utf-8")
    child = (out / "areas" / "oversight" / "iran-contra" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "/editions/2026-10/direct/" in parent and "/editions/2026-10/mapped/" in parent
    assert "/editions/2026-10/mapped/" in child and "/editions/2026-10/direct/" not in child
    assert 'href="/areas/oversight/iran-contra/"' in parent
    assert 'href="/areas/oversight/"' in child
    assert not (out / "areas" / "closed").exists()
    assert 'href="/areas/"' in (out / "editions/2026-10/mapped" / "index.html").read_text(encoding="utf-8")


def test_area_index_is_recursive_and_navigation_is_deterministic(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "page.md").write_text(
        "---\ntitle: Assigned Page\nareas: [oversight/iran-contra/hearings]\n---\n\n# Page\n",
        encoding="utf-8",
    )
    areas = tmp_path / "areas.json"
    areas.write_text(
        json.dumps(
            [
                {"slug": "epstein", "title": "Epstein", "parent": None, "status": "open"},
                {
                    "slug": "epstein/legal-record",
                    "title": "The Legal Record",
                    "parent": "epstein",
                    "status": "open",
                },
                {
                    "slug": "oversight",
                    "title": "Congressional Oversight",
                    "parent": None,
                    "status": "open",
                },
                {
                    "slug": "oversight/oversight-law",
                    "title": "Oversight Law",
                    "parent": "oversight",
                    "status": "open",
                },
                {
                    "slug": "oversight/iran-contra",
                    "title": "Iran-Contra",
                    "parent": "oversight",
                    "status": "open",
                },
                {
                    "slug": "oversight/iran-contra/hearings",
                    "title": "Hearings",
                    "parent": "oversight/iran-contra",
                    "status": "open",
                },
                {
                    "slug": "oversight/secret",
                    "title": "Secret",
                    "parent": "oversight",
                    "status": "closed",
                },
                {"slug": "jfk", "title": "JFK", "parent": None, "status": "closed"},
            ]
        ),
        encoding="utf-8",
    )
    first, second = tmp_path / "first", tmp_path / "second"

    for out in (first, second):
        result = run_build(src, out, "atlas", "--areas", str(areas))
        assert result.returncode == 0, result.stderr
    assert tree_hashes(first) == tree_hashes(second)

    index = (first / "areas" / "index.html").read_text(encoding="utf-8")
    slugs = [
        "oversight",
        "oversight/iran-contra",
        "oversight/iran-contra/hearings",
        "oversight/oversight-law",
        "epstein",
        "epstein/legal-record",
    ]
    positions = [index.index(f'href="/areas/{slug}/"') for slug in slugs]
    assert positions == sorted(positions)
    assert "<ul>" in index[positions[0] : positions[1]]
    assert "<ul>" in index[positions[1] : positions[2]]
    assert "</ul>" in index[positions[3] : positions[4]]
    assert "/areas/oversight/secret/" not in index
    assert "/areas/jfk/" not in index

    oversight = (first / "areas" / "oversight" / "index.html").read_text(encoding="utf-8")
    iran_contra = (
        first / "areas" / "oversight" / "iran-contra" / "index.html"
    ).read_text(encoding="utf-8")
    hearings = (
        first / "areas" / "oversight" / "iran-contra" / "hearings" / "index.html"
    ).read_text(encoding="utf-8")
    assert oversight.index('/areas/oversight/iran-contra/') < oversight.index(
        '/areas/oversight/oversight-law/'
    )
    assert "/areas/oversight/secret/" not in oversight
    assert 'href="/areas/oversight/"' in iran_contra
    assert 'href="/areas/oversight/iran-contra/hearings/"' in iran_contra
    assert 'href="/areas/oversight/iran-contra/"' in hearings
    assert "/page/" in oversight and "/page/" in iran_contra and "/page/" in hearings
    assert not (first / "areas" / "oversight" / "secret").exists()
    assert not (first / "areas" / "jfk").exists()


def test_open_area_with_closed_ancestor_is_rejected_before_output(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    areas = tmp_path / "areas.json"
    areas.write_text(
        json.dumps(
            [
                {"slug": "root", "title": "Root", "parent": None, "status": "open"},
                {
                    "slug": "root/closed",
                    "title": "Closed",
                    "parent": "root",
                    "status": "closed",
                },
                {
                    "slug": "root/closed/open",
                    "title": "Invalid Open Descendant",
                    "parent": "root/closed",
                    "status": "open",
                },
            ]
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"

    result = run_build(src, out, "atlas", "--areas", str(areas))

    assert result.returncode == 1
    assert "closed" in result.stderr.lower()
    assert "root/closed/open" in result.stderr
    assert not out.exists()


def write_area_registry(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {"slug": "oversight", "title": "Oversight", "parent": None, "status": "open"},
                {
                    "slug": "oversight/subtopic",
                    "title": "Subtopic",
                    "parent": "oversight",
                    "status": "open",
                },
                {"slug": "closed", "title": "Closed", "parent": None, "status": "closed"},
            ]
        ),
        encoding="utf-8",
    )


def test_page_area_map_falls_back_to_filename_stem(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "nested").mkdir(parents=True)
    (src / "nested" / "atlas-stem.md").write_text(
        "---\ntitle: Stem Mapped\n---\n\n# Stem Mapped\n", encoding="utf-8"
    )
    areas = tmp_path / "areas.json"
    write_area_registry(areas)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"atlas-stem": ["oversight/subtopic"]}), encoding="utf-8")
    out = tmp_path / "out"

    result = run_build(src, out, "atlas", "--areas", str(areas), "--page-areas", str(mapping))

    assert result.returncode == 0, result.stderr
    parent = (out / "areas" / "oversight" / "index.html").read_text(encoding="utf-8")
    child = (out / "areas" / "oversight" / "subtopic" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "/nested/atlas-stem/" in parent
    assert "/nested/atlas-stem/" in child
    manifest = json.loads((out / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["unmatched_page_area_keys"] == []


@pytest.mark.parametrize(
    ("mapped_area", "needle"),
    [
        ("closed", "closed"),
        ("missing", "unknown area"),
    ],
)
def test_stem_fallback_preserves_area_validation(
    tmp_path: Path, mapped_area: str, needle: str
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "atlas-stem.md").write_text("# Stem Mapped\n", encoding="utf-8")
    areas = tmp_path / "areas.json"
    write_area_registry(areas)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"atlas-stem": [mapped_area]}), encoding="utf-8")

    result = run_build(
        src,
        tmp_path / "out",
        "atlas",
        "--areas",
        str(areas),
        "--page-areas",
        str(mapping),
    )

    assert result.returncode == 1
    assert "atlas-stem.md" in result.stderr
    assert needle in result.stderr.lower()


def test_mapped_duplicate_stem_is_ambiguous(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "one").mkdir(parents=True)
    (src / "two").mkdir()
    (src / "one" / "shared.md").write_text("# First\n", encoding="utf-8")
    (src / "two" / "shared.md").write_text("# Second\n", encoding="utf-8")
    areas = tmp_path / "areas.json"
    write_area_registry(areas)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"shared": ["oversight"]}), encoding="utf-8")

    result = run_build(
        src,
        tmp_path / "out",
        "atlas",
        "--areas",
        str(areas),
        "--page-areas",
        str(mapping),
    )

    assert result.returncode == 1
    assert "ambiguous" in result.stderr.lower()
    assert "one/shared.md" in result.stderr
    assert "two/shared.md" in result.stderr


def test_unmatched_page_area_keys_warn_manifest_and_strict_fail(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "page.md").write_text("# Page\n", encoding="utf-8")
    areas = tmp_path / "areas.json"
    write_area_registry(areas)
    mapping = tmp_path / "map.json"
    mapping.write_text(
        json.dumps({"z-missing": ["oversight"], "a-missing": ["oversight"]}),
        encoding="utf-8",
    )

    out = tmp_path / "out"
    result = run_build(src, out, "atlas", "--areas", str(areas), "--page-areas", str(mapping))
    assert result.returncode == 0, result.stderr
    assert result.stderr.splitlines() == [
        "warning: unmatched page-area key: 'a-missing'",
        "warning: unmatched page-area key: 'z-missing'",
    ]
    manifest = json.loads((out / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["unmatched_page_area_keys"] == ["a-missing", "z-missing"]

    strict = run_build(
        src,
        tmp_path / "strict-out",
        "atlas",
        "--areas",
        str(areas),
        "--page-areas",
        str(mapping),
        "--strict-page-areas",
    )
    assert strict.returncode == 1
    assert "unmatched" in strict.stderr.lower()
    assert "a-missing" in strict.stderr and "z-missing" in strict.stderr


@pytest.mark.parametrize(
    ("area_value", "needle"),
    [
        ("closed", "closed"),
        ("missing", "unknown area"),
    ],
)
def test_invalid_area_assignment_fails_with_file(
    tmp_path: Path, area_value: str, needle: str
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.md").write_text(
        f"---\ntitle: Bad\nareas: [{area_value}]\n---\n\n# Bad\n", encoding="utf-8"
    )
    areas = tmp_path / "areas.json"
    areas.write_text(
        json.dumps([{"slug": "closed", "title": "Closed", "parent": None, "status": "closed"}]),
        encoding="utf-8",
    )
    result = run_build(src, tmp_path / "out", "atlas", "--areas", str(areas))
    assert result.returncode == 1
    assert "bad.md" in result.stderr
    assert needle in result.stderr.lower()
    assert len(result.stderr.splitlines()) == 1


def test_wikilink_title_and_symlink_are_rejected(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.md").write_text(
        "---\ntitle: '[[concept/x|Bad]]'\n---\n\n# Safe Heading\n", encoding="utf-8"
    )
    result = run_build(src, tmp_path / "wikilink")
    assert result.returncode == 1
    assert "bad.md" in result.stderr and "title" in result.stderr.lower()

    (src / "bad.md").unlink()
    target = tmp_path / "outside.txt"
    target.write_text("outside\n", encoding="utf-8")
    (src / "linked.txt").symlink_to(target)
    result = run_build(src, tmp_path / "symlink")
    assert result.returncode == 1
    assert "linked.txt" in result.stderr and "symlink" in result.stderr.lower()


def test_without_area_registry_ignores_area_metadata(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "page.md").write_text(
        "---\ntitle: Page\nareas: legacy-scalar\n---\n\n# Page\n", encoding="utf-8"
    )
    result = run_build(src, tmp_path / "out")
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "out" / "areas").exists()


@pytest.mark.parametrize("surface", ["atlas", "publications"])
def test_markdown_sources_are_served_verbatim(tmp_path: Path, surface: str) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    sources = {
        "editions/2026-10/index.md": b"# Edition 2026-10\n",
        "editions/2026-10/atlas-fixture.md": (
            "---\r\ntitle: Café\r\n---\r\n# Café\r\n\r\nKeep trailing spaces.  \r\n"
        ).encode("utf-8"),
        "legislation/efta-ii-memo/2026-10/index.md": b"# Memo\n\nNo final newline",
    }
    for relative, data in sources.items():
        source = src / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(data)

    result = run_build(src, out, surface)

    assert result.returncode == 0, result.stderr
    manifest = json.loads((out / "build-manifest.json").read_bytes())
    for relative, data in sources.items():
        assert (out / relative).read_bytes() == data
        digest = hashlib.sha256(data).hexdigest()
        assert manifest["inputs"]["src/" + relative] == digest
        assert manifest["outputs"][relative] == digest
    assert (out / "editions/2026-10/atlas-fixture/index.html").is_file()
    assert (out / "legislation/efta-ii-memo/2026-10/index.html").is_file()


@pytest.mark.parametrize("surface", ["atlas", "publications"])
@pytest.mark.parametrize("base_url", [
    "https://example.test/", "https://example.test/research&notes///",
])
def test_canonical_links_match_sitemap_routes(
    tmp_path: Path, surface: str, base_url: str
) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    write_base_fixture(src)
    result = run_build(src, out, surface, "--base-url", base_url)
    assert result.returncode == 0, result.stderr

    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    # Includes the generated home/editions pages and all Markdown pages.
    for page in out.rglob("*.html"):
        relative = page.relative_to(out)
        route = "/" if relative == Path("index.html") else "/" + relative.parent.as_posix() + "/"
        canonical = html.escape(base_url.rstrip("/") + route, quote=True)
        rendered = page.read_text(encoding="utf-8")
        assert rendered.count('rel="canonical"') == 1
        assert f'<link rel="canonical" href="{canonical}">' in rendered
        assert f"<loc>{canonical}</loc>" in sitemap


def test_markdown_download_output_collision_is_refused_before_writes(tmp_path: Path) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "page.md").write_text("# Download\n", encoding="utf-8")
    # Rendering this source would create a directory at the first source's download path.
    (src / "page.md.md").write_text("# Conflicting route\n", encoding="utf-8")

    result = run_build(src, out)

    assert result.returncode == 1
    assert "output collision" in result.stderr
    assert "page.md" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("surface", ["atlas", "publications"])
@pytest.mark.parametrize("editions", [[], ["2027-03"], ["2027-03-patch-2"], ["2026-10", "2027-03"]])
def test_generated_indexes_show_actual_edition_labels_and_preserve_sources(
    tmp_path: Path, surface: str, editions: list[str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for edition in editions:
        directory = src / "editions" / edition
        directory.mkdir(parents=True)
        (directory / "index.md").write_text(f"# Edition {edition}\n", encoding="utf-8")
        (directory / "topic.md").write_text(
            f"# Topic\n\nEdition label: `{edition}`\n\n"
            "Source: [Public record](https://example.test/source).\n",
            encoding="utf-8",
        )
    areas = tmp_path / "areas.json"
    areas.write_text(json.dumps([
        {"slug": "parent", "title": "Parent", "parent": None, "status": "open"},
        {"slug": "parent/child", "title": "Child", "parent": "parent", "status": "open"},
        {"slug": "empty", "title": "Empty", "parent": None, "status": "open"},
    ]), encoding="utf-8")
    supply_test_feed(src)
    before = tree_hashes(src)
    out = tmp_path / "out"
    extra = ["--areas", str(areas)] if surface == "atlas" else []
    result = run_build(src, out, surface, *extra)
    assert result.returncode == 0, result.stderr
    assert tree_hashes(src) == before
    indexes = ["editions/index.html"] if editions else []
    if surface == "atlas":
        indexes += ["areas/index.html", "areas/parent/index.html",
                    "areas/parent/child/index.html", "areas/empty/index.html"]
    for relative in indexes:
        rendered = (out / relative).read_text(encoding="utf-8")
        labels = re.findall(r'<span class="edition-label">([^<]*)</span>', rendered)
        assert labels == [f"Edition {edition}" for edition in sorted(editions)]
    for edition in editions:
        relative = Path("editions") / edition / "topic.md"
        assert (out / relative).read_bytes() == (src / relative).read_bytes()
        rendered = (out / relative.with_suffix("") / "index.html").read_text(encoding="utf-8")
        labels = re.findall(r'<span class="edition-label">([^<]*)</span>', rendered)
        assert labels == [f"Edition {edition}"]
        assert 'href="https://example.test/source"' in rendered


def test_stylesheet_makes_no_external_requests() -> None:
    css = (BUILD_ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert "@import" not in code.lower()
    assert re.search(r"\burl\s*\(", code, re.I) is None
    assert re.search(r"(?:https?:)?//", code) is None
    assert len(css.encode("utf-8")) < 15 * 1024


@pytest.mark.parametrize(
    ("surface", "section_label"),
    [("atlas", "Sourcebook"), ("publications", "Publications")],
)
def test_header_home_opens_the_parallax_index_and_section_link_opens_this_site(
    tmp_path: Path, surface: str, section_label: str
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "page.md").write_text("# A page\n\nEdition label: `2026-10`\n\nBody.\n", encoding="utf-8")
    result = run_build(src, tmp_path / "out", surface)
    assert result.returncode == 0, result.stderr
    for rendered in (tmp_path / "out" / "index.html", tmp_path / "out" / "page" / "index.html"):
        text = rendered.read_text(encoding="utf-8")
        nav = text.split('<nav aria-label="Primary navigation">', 1)[1].split("</nav>", 1)[0]
        assert '<a href="https://disclosureworks.ai/">Home</a>' in nav
        assert f'<a href="/">{section_label}</a>' in nav
        assert nav.index("Home") < nav.index(section_label)


def test_home_url_can_be_overridden(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    result = run_build(src, tmp_path / "out", "atlas", "--home-url", "https://index.example.test")
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "out" / "index.html").read_text(encoding="utf-8")
    assert '<a href="https://index.example.test/">Home</a>' in text

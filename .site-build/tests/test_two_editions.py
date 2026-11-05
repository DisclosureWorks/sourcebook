"""Edition-scoped area resolution with frozen publication bytes."""
import json
from pathlib import Path

import pytest

from test_build import run_build, tree_hashes, write_area_registry, supply_test_feed


def fixture(tmp_path):
    src = tmp_path / "src"
    old = src / "editions/2026-10/atlas-shared.md"
    old.parent.mkdir(parents=True)
    (old.parent / "index.md").write_text("# October\n")
    old.write_text("# Frozen page\n")
    (old.parent / "manifest.json").write_text(json.dumps({"pages": [
        {"path": "editions/2026-10/atlas-shared.md", "topics": ["oversight"]}
    ]}))
    areas = tmp_path / "areas.json"
    write_area_registry(areas)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"atlas-shared": ["oversight"]}))
    return src, areas, mapping


def build(src, out, areas, mapping):
    return run_build(src, out, "atlas", "--areas", str(areas),
                     "--page-areas", str(mapping), "--strict-page-areas")


def add_current(src, name="atlas-shared.md", metadata=""):
    path = src / "editions/2026-11" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    (src / "editions/2026-11/index.md").write_text("# November\n")
    path.write_text(metadata + "# Current page\n")
    supply_test_feed(src)
    return path


def test_two_editions_preserve_frozen_html_placement_and_source_bytes(tmp_path):
    src, areas, mapping = fixture(tmp_path)
    before = tree_hashes(src / "editions/2026-10")
    baseline = tmp_path / "baseline"
    result = build(src, baseline, areas, mapping)
    assert result.returncode == 0, result.stderr
    add_current(src)
    mapping.write_text(json.dumps({"atlas-shared": ["oversight/subtopic"]}))
    out = tmp_path / "out"
    result = build(src, out, areas, mapping)
    assert result.returncode == 0, result.stderr
    parent = (out / "areas/oversight/index.html").read_text()
    child = (out / "areas/oversight/subtopic/index.html").read_text()
    assert '/editions/2026-10/atlas-shared/' not in parent
    assert parent.count('/editions/2026-11/atlas-shared/') == 1
    assert 'Current page' in parent and 'Frozen page' not in parent
    assert '/editions/2026-10/atlas-shared/' not in child
    assert '/editions/2026-11/atlas-shared/' in child
    assert (out / "editions/2026-10/atlas-shared/index.html").read_bytes() == (
        baseline / "editions/2026-10/atlas-shared/index.html").read_bytes()
    assert tree_hashes(src / "editions/2026-10") == before
    assert json.loads((out / "build-manifest.json").read_text())["unmatched_page_area_keys"] == []


@pytest.mark.parametrize("edition", ["2026-10", "2026-11"])
def test_duplicate_stem_within_one_edition_refused(tmp_path, edition):
    src, areas, mapping = fixture(tmp_path)
    add_current(src)
    duplicate = src / "editions" / edition / "nested/atlas-shared.md"
    duplicate.parent.mkdir()
    duplicate.write_text("# Duplicate\n")
    result = build(src, tmp_path / "out", areas, mapping)
    assert result.returncode == 1
    assert "ambiguous page-area stem" in result.stderr


def test_duplicate_explicit_public_id_within_one_edition_refused(tmp_path):
    src, areas, mapping = fixture(tmp_path)
    metadata = "---\npublic_id: atlas-shared\n---\n"
    add_current(src, "one.md", metadata)
    add_current(src, "two.md", metadata)
    result = build(src, tmp_path / "out", areas, mapping)
    assert result.returncode == 1
    assert "ambiguous page-area public id" in result.stderr


@pytest.mark.parametrize("metadata,name", [("", "atlas-unmapped.md"),
    ("---\npublic_id: unassigned\n---\n", "unmapped.md")])
def test_public_id_without_area_refused(tmp_path, metadata, name):
    src, areas, mapping = fixture(tmp_path)
    add_current(src)
    add_current(src, name, metadata)
    result = build(src, tmp_path / "out", areas, mapping)
    assert result.returncode == 1
    assert "public id has no area" in result.stderr


def test_frozen_page_never_inherits_current_map_without_frozen_metadata(tmp_path):
    src, areas, mapping = fixture(tmp_path)
    (src / "editions/2026-10/manifest.json").unlink()
    add_current(src)
    result = build(src, tmp_path / "out", areas, mapping)
    assert result.returncode == 1
    assert "editions/2026-10/atlas-shared.md: public id has no area" in result.stderr


@pytest.mark.parametrize('fault', ['old', 'duplicate'])
@pytest.mark.parametrize('location', ['index.md', 'unexpected/list.md'])
def test_current_list_fault_refuses_build(tmp_path, fault, location):
    src, areas, mapping = fixture(tmp_path)
    add_current(src)
    current = '[Current](/editions/2026-11/atlas-shared/)'
    bad = '[Old](/editions/2026-10/atlas-shared/)' if fault == 'old' else current
    page = src / location
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text('# List\n\n- ' + current + '\n- ' + bad + '\n')
    result = build(src, tmp_path / 'out', areas, mapping)
    assert result.returncode == 1
    assert ('current_pages_linking_to_older_edition_entry' if fault == 'old'
            else 'current_pages_listing_a_page_twice') in result.stderr


def test_newest_topics_use_new_title_and_numeric_patch_order(tmp_path):
    src, areas, mapping = fixture(tmp_path)
    add_current(src)
    for edition in ('2027-02-patch-2', '2027-02-patch-10'):
        path = src / 'editions' / edition
        path.mkdir()
        (path / 'index.md').write_text('# Edition\n')
        (path / 'atlas-shared.md').write_text('---\nareas: [oversight]\n---\n# ' + edition + '\n')
    # November is now frozen and needs its historical placement.
    (src / 'editions/2026-11/manifest.json').write_text(json.dumps({'pages': [
        {'path': 'editions/2026-11/atlas-shared.md', 'topics': ['oversight']}
    ]}))
    # Explicit frontmatter does not consume the external mapping; use an empty map.
    mapping.write_text('{}')
    result = build(src, tmp_path / 'out2', areas, mapping)
    assert result.returncode == 0, result.stderr
    out = tmp_path / 'out2'
    parent = (out / 'areas/oversight/index.html').read_text()
    assert parent.count('/editions/2027-02-patch-10/atlas-shared/') == 1
    assert '/editions/2027-02-patch-2/atlas-shared/' not in parent
    editions = (out / 'editions/index.html').read_text()
    assert editions.index('href="/editions/2027-02-patch-10/"') < editions.index('href="/editions/2027-02-patch-2/"')

"""Current footer navigation must not change frozen October pages."""
import re

import pytest

from test_build import run_build, tree_hashes, supply_test_feed


CONTACT = 'https://disclosureworks.ai/contact/'


def write_contact_fixture(src, surface, *, license=True, citation=True):
    pages = {
        'index.md': '# Welcome\n\nEdition label: `2026-11`\n',
        'latest/index.md': '# Latest\n\nEdition label: `2026-11`\n\n[Current](/editions/2026-11/)\n',
        'editions/2026-10/index.md': '# October\n\nEdition label: `2026-10`\n',
        'editions/2026-11/index.md': '# November\n\nEdition label: `2026-11`\n',
    }
    for section in (('research', 'legislation') if surface == 'publications' else ()):
        for edition in ('2026-10', '2026-11'):
            pages[f'{section}/sample/{edition}/index.md'] = (
                f'# Sample paper\n\nEdition label: `{edition}`\n'
            )
    for name, address in [('corrections-removal', 'corrections@example.test'),
                          ('security', 'security@example.test'),
                          ('policy', 'policy@example.test')]:
        pages[f'{name}.md'] = (
            f'# {name}\n\nEdition label: `2026-11`\n\n'
            f'[Email](mailto:{address})\n'
        )
    if license:
        pages['LICENSE'] = 'Synthetic license\n'
    if citation:
        pages['CITATION.md'] = '# Citation guidance\n\nEdition label: `2026-11`\n'
    for relative, text in pages.items():
        path = src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def footer(text):
    return re.search(r'<footer>.*?</footer>', text, re.S).group()


@pytest.mark.parametrize('surface', ['atlas', 'publications'])
@pytest.mark.parametrize('license,citation', [(True, True), (True, False),
                                              (False, True), (False, False)])
def test_contact_on_current_pages_only(tmp_path, surface, license, citation):
    src, out = tmp_path / 'src', tmp_path / 'out'
    write_contact_fixture(src, surface, license=license, citation=citation)
    supply_test_feed(src)
    before = tree_hashes(src)
    result = run_build(src, out, surface, '--strict-page-areas')
    assert result.returncode == 0, result.stderr
    for page in out.rglob('*.html'):
        relative = page.relative_to(out).as_posix()
        links = footer(page.read_text())
        frozen = relative.startswith('editions/2026-10/') or any(
            relative.startswith(f'{section}/sample/2026-10/')
            for section in ('research', 'legislation')
        )
        assert links.count(f'<a href="{CONTACT}">Contact</a>') == (0 if frozen else 1)
        expected = []
        if license:
            expected.append('License')
        if citation:
            expected.append('Citation guidance')
        if not frozen:
            expected.append('Contact')
        assert re.findall(r'<a [^>]*>(.*?)</a>', links) == expected
        assert links.count('aria-hidden="true"') == max(0, len(expected) - 1)
    assert tree_hashes(src) == before
    for name, address in [('corrections-removal', 'corrections@example.test'),
                          ('security', 'security@example.test'),
                          ('policy', 'policy@example.test')]:
        assert f'href="mailto:{address}"' in (out / name / 'index.html').read_text()
    assert "Content-Security-Policy: default-src 'self'" in (out / '_headers').read_text()

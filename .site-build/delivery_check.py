"""Offline delivery checks. Receipts contain paths and hashes, never list prose."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote, urlsplit

from note_display import inspect_notes, inspect_headings, inspect_raw_names, inspect_entry_text


def edition_key(value):
    match = re.fullmatch(r'(\d{4})-(\d{2})(?:-patch-(\d+))?', value)
    return tuple(int(x or 0) for x in match.groups()) if match else (0, 0, 0)


class PageLists(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.items = []
        self.active = []
        self.footnotes = 0
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'section', 'div'}:
            footnotes = (attrs.get('role') == 'doc-endnotes' or
                         'footnotes' in attrs.get('class', '').split())
            self.sections.append(footnotes)
            self.footnotes += int(footnotes)
        if tag == 'li':
            self.active.append({'links': [], 'text': [], 'footnote': bool(self.footnotes),
                                'nested': False})
            if len(self.active) > 1:
                self.active[-2]['nested'] = True
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
            if self.active:
                self.active[-1]['links'].append(attrs['href'])
        if tag in {'img', 'script', 'iframe', 'source'} and 'src' in attrs:
            self.links.append(attrs['src'])
        if tag == 'link' and 'href' in attrs:
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'li' and self.active:
            self.items.append(self.active.pop())
        if tag in {'section', 'div'} and self.sections:
            self.footnotes -= int(self.sections.pop())

    def handle_data(self, data):
        if self.active:
            self.active[-1]['text'].append(data)


def local_path(href, relative, base_url=''):
    url = urlsplit(href)
    if url.scheme or url.netloc:
        if not base_url or url.netloc != urlsplit(base_url).netloc:
            return None
    if not url.path:
        return None
    path = unquote(url.path)
    return posixpath.normpath(path.lstrip('/') if path.startswith('/') else
                              posixpath.join(posixpath.dirname(relative), path))


def entry_identity(path):
    parts = Path(path).parts
    if len(parts) < 3 or parts[0] != 'editions' or not edition_key(parts[1])[0]:
        return None
    tail = list(parts[2:])
    if tail[-1] in {'index.html', 'index.md'}:
        tail.pop()
    elif Path(tail[-1]).suffix in {'.html', '.md'}:
        tail[-1] = Path(tail[-1]).stem
    elif Path(tail[-1]).suffix:
        return None
    return (parts[1], '/'.join(tail)) if tail else None


def crawl_site(root, *, current_edition=None, base_url='', entry_ids=None, raw_name_hashes=()):
    root = Path(root).resolve()
    pages = sorted(root.rglob('*.html'))
    editions = [p.name for p in (root / 'editions').iterdir() if p.is_dir()] if (root / 'editions').is_dir() else []
    current_edition = current_edition or max(editions, key=edition_key, default=None)
    result = {key: [] for key in ('current_pages_linking_to_older_edition_entry',
        'current_pages_listing_a_page_twice', 'broken_internal_links', 'repeated_list_items',
        'other_repeated_current_items', 'november_pages_with_raw_note_markers',
        'pages_where_a_note_does_not_render', 'unused_note_definitions',
        'pages_with_raw_markdown_headings', 'pages_where_a_heading_does_not_render',
        'november_rows_showing_a_raw_name', 'november_entry_raw_page_names',
        'november_entry_collapsed_lists')}
    result['pages_crawled'] = len(pages)
    for page in pages:
        relative = page.relative_to(root).as_posix()
        parser = PageLists()
        parser.feed(page.read_text(encoding='utf-8'))
        sources = [page.with_suffix('.md')]
        if page.name == 'index.html':
            sources.append(page.parent.with_suffix('.md'))
        source = next((p for p in sources if p.is_file()), None)
        current = not relative.startswith('editions/')
        if current or relative.startswith(f'editions/{current_edition}/'):
            if entry_identity(relative) is not None and current_edition == '2026-11':
                display = inspect_entry_text(page.read_text(encoding='utf-8'), raw_name_hashes=raw_name_hashes,
                                             markdown=source.read_text(encoding='utf-8') if source else None)
                for key, source_key in [('november_entry_raw_page_names', 'raw_page_names'),
                                        ('november_entry_collapsed_lists', 'collapsed_lists')]:
                    result[key].extend({'page': relative, **row} for row in display[source_key])
            result['november_rows_showing_a_raw_name'].extend(
                {'page': relative, **row} for row in inspect_raw_names(page.read_text(encoding='utf-8'),
                    all_lists=entry_identity(relative) is not None))
            # The builder delivers source Markdown beside its rendered pages.
            candidates = [page.with_suffix('.md')]
            if page.name == 'index.html':
                candidates.append(page.parent.with_suffix('.md'))
            source = next((p for p in candidates if p.is_file()), None)
            headings = inspect_headings(source.read_text(encoding='utf-8') if source else '',
                                        page.read_text(encoding='utf-8'))
            if headings['raw_markdown_heading_count']:
                result['pages_with_raw_markdown_headings'].append({'page': relative, **headings})
            if headings['missing_rendered_heading_count']:
                result['pages_where_a_heading_does_not_render'].append({'page': relative, **headings})
            if source is not None:
                notes = inspect_notes(source.read_text(encoding='utf-8'), page.read_text(encoding='utf-8'))
                if notes['visible_raw_note_markers']:
                    result['november_pages_with_raw_note_markers'].append(
                        {'page': relative, 'note_ids': notes['visible_raw_note_markers']})
                if notes['referred_note_missing']:
                    result['pages_where_a_note_does_not_render'].append({'page': relative, **notes})
                result['unused_note_definitions'].extend(
                    {'page': relative, 'note_id': note} for note in notes['unused_definition_ids'])
        listed = Counter()
        repeated = Counter()
        footnote_counts = Counter()
        for item in parser.items:
            text = ' '.join(''.join(item['text']).split())
            # Footnote back-link numbers are presentation only. Keep prose private.
            text = re.sub(r'[↩\u21a9\ufe0e\ufe0f]+\d*', '', text).strip()
            if text and not item['nested']:
                fingerprint = hashlib.sha256(text.encode()).hexdigest()
                repeated[fingerprint] += 1
                footnote_counts[fingerprint] += int(item['footnote'])
            identities = set()
            for href in item['links']:
                path = local_path(href, relative, base_url)
                identity = entry_identity(path) if path is not None else None
                if not identity or item['footnote']:
                    continue
                edition, identifier = identity
                identifier = (entry_ids or {}).get(path, identifier)
                identities.add(identifier)
                if current and current_edition and edition_key(edition) < edition_key(current_edition):
                    row = {'page': relative, 'target': path, 'page_id': identifier}
                    if row not in result['current_pages_linking_to_older_edition_entry']:
                        result['current_pages_linking_to_older_edition_entry'].append(row)
            if current:
                listed.update(identities)
        for identifier, count in sorted(listed.items()):
            if count > 1:
                result['current_pages_listing_a_page_twice'].append(
                    {'page': relative, 'page_id': identifier, 'count': count})
        is_entry_or_paper = (entry_identity(relative) is not None or
            (len(Path(relative).parts) >= 4 and Path(relative).parts[0] in {'research', 'legislation'}))
        for fingerprint, count in sorted(repeated.items()):
            if count > 1:
                expected = is_entry_or_paper and footnote_counts[fingerprint] == count
                row = {'page': relative, 'count': count, 'item_sha256': fingerprint,
                       'expected_repeated_footnote': expected}
                result['repeated_list_items'].append(row)
                if current and not expected:
                    result['other_repeated_current_items'].append(row)
        for href in sorted(set(parser.links)):
            path = local_path(href, relative, base_url)
            if path is None:
                continue
            target = (root / path).resolve()
            if not target.is_relative_to(root) or not (target.is_file() or
                    (target.is_dir() and (target / 'index.html').is_file())):
                result['broken_internal_links'].append({'page': relative, 'target': path})
    return result


def require_current_lists(root, current_edition, base_url='', entry_ids=None):
    result = crawl_site(root, current_edition=current_edition, base_url=base_url, entry_ids=entry_ids)
    for key in ('current_pages_linking_to_older_edition_entry', 'current_pages_listing_a_page_twice'):
        if result[key]:
            raise ValueError(f"{key}: {len(result[key])} violation(s); first page {result[key][0]['page']}")
    return result

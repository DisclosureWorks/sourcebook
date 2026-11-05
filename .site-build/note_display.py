"""Public, dependency-free note display gate; reports identifiers, never prose."""
from html.parser import HTMLParser
from collections import Counter
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

DEFINITION = re.compile(r'^ {0,3}\[\^([^\]\s]+)\]:')
REFERENCE = re.compile(r'\[\^([^\]\s]+)\]')


class HeadingsHTML(HTMLParser):
    """Read visible block boundaries and heading text without publishing prose."""
    BLOCKS = {'p', 'div', 'section', 'aside', 'li', 'ul', 'ol', 'br', 'blockquote',
              'pre', 'main', 'header', 'footer', 'nav', 'td', 'th', 'tr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.visible, self.headings = [], []
        self.hidden = 0
        self.heading = None

    def handle_starttag(self, tag, attrs):
        if tag in {'head', 'script', 'style'}:
            self.hidden += 1
        if self.hidden:
            return
        if re.fullmatch(r'h[1-6]', tag):
            self.visible.append('\n')
            self.heading = (int(tag[1]), [])
        elif tag in self.BLOCKS:
            self.visible.append('\n')

    def handle_endtag(self, tag):
        if tag in {'head', 'script', 'style'}:
            self.hidden -= 1
            return
        if self.hidden:
            return
        if re.fullmatch(r'h[1-6]', tag) and self.heading is not None:
            level, parts = self.heading
            self.headings.append((level, ' '.join(''.join(parts).split())))
            self.heading = None
            self.visible.append('\n')
        elif tag in self.BLOCKS:
            self.visible.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)
            if self.heading is not None:
                self.heading[1].append(data)


def markdown_heading_lines(markdown):
    """ATX heading lines outside YAML and fenced code, including swallowed lines."""
    markdown = re.sub(r'\A---\s*\n.*?\n(?:---|\.\.\.)\s*(?:\n|$)', '', markdown, count=1, flags=re.S)
    headings, fence = [], None
    for line in markdown.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*', line):
                fence = None
        elif marker:
            fence = marker[1]
        elif re.match(r'^ {0,3}#{1,6}(?:\s|$)', line):
            headings.append(line)
    return headings


def inspect_headings(markdown, html):
    parsed = HeadingsHTML()
    parsed.feed(html)
    # Render isolated heading lines so a swallowed line cannot disappear from
    # the expected inventory. Pandoc handles emphasis, links and explicit IDs.
    lines = markdown_heading_lines(markdown)
    expected = HeadingsHTML()
    if lines:
        result = subprocess.run(['pandoc', '--from=markdown-raw_html', '--to=html5'],
                                input='\n\n'.join(lines) + '\n', text=True,
                                capture_output=True, check=True)
        expected.feed(result.stdout)
    missing = Counter(expected.headings) - Counter(parsed.headings)
    return {'raw_markdown_heading_count': len(re.findall(
                r'(?m)^[ \t]*#{1,6}[ \t]+(?=\S)', ''.join(parsed.visible))),
            'markdown_heading_count': len(lines),
            'missing_rendered_heading_count': sum(missing.values())}


def require_headings(markdown, html):
    result = inspect_headings(markdown, html)
    if result['raw_markdown_heading_count'] or result['missing_rendered_heading_count']:
        raise ValueError('raw Markdown heading or heading did not render')
    return result


def format_assessment_html(html):
    """Join Pandoc's adjacent quote paragraphs into the generated assessment box.

    Literal blank lines preserve the exported nonblank-line contract, but
    Pandoc treats them as separate blockquotes. Merge only the generated span
    delimited by its title and dated grading link; ordinary quotes stay intact.
    """
    pattern = (r'<blockquote>\s*<p><strong>Our assessment</strong></p>'
               r'.*?<p>Assessed\s+\d{4}-\d{2}-\d{2}\.\s+'
               r'<a href="/grading/">How\s+we\s+grade\s+conclusions</a></p>\s*</blockquote>')
    def merge(match):
        block = re.sub(r'</blockquote>\s*<blockquote>', '\n', match[0])
        return block.replace('<blockquote>', '<blockquote class="assessment">', 1)
    return re.sub(pattern, merge, html, flags=re.S)


class NotesHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.visible, self.notes, self.references = [], [], []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'head', 'script', 'style'}:
            self.hidden += 1
        if tag == 'li' and re.fullmatch(r'fn\d+', attrs.get('id', '')):
            self.notes.append(attrs['id'])
        if tag == 'a' and attrs.get('role') == 'doc-noteref':
            self.references.append(attrs.get('href', ''))

    def handle_endtag(self, tag):
        if tag in {'head', 'script', 'style'}:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


def note_inventory(markdown):
    definitions, references, fence = [], [], None
    for line in markdown.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif fence is None:
            definition = DEFINITION.match(line)
            if definition:
                definitions.append(definition[1])
            else:
                references.extend(REFERENCE.findall(re.sub(r'`[^`]*`', '', line)))
    return definitions, references


def inspect_notes(markdown, html):
    definitions, references = note_inventory(markdown)
    parsed = NotesHTML()
    parsed.feed(html)
    missing_targets = [href for href in parsed.references if href.removeprefix('#') not in parsed.notes]
    missing = sorted(set(references) - set(definitions))
    return {'unused_definition_ids': sorted(set(definitions) - set(references)),
            'undefined_reference_ids': missing,
            'visible_raw_note_markers': REFERENCE.findall(''.join(parsed.visible)),
            'missing_rendered_targets': missing_targets,
            'references': len(references), 'rendered_references': len(parsed.references),
            'rendered_notes': len(parsed.notes),
            'referred_note_missing': bool(missing or missing_targets or
                len(parsed.references) != len(references) or len(parsed.notes) < len(references))}


def require_notes(markdown, html):
    result = inspect_notes(markdown, html)
    if result['visible_raw_note_markers'] or result['referred_note_missing']:
        raise ValueError('raw note marker or referenced note did not render')
    return result


def require_atom(payload):
    root = ET.fromstring(payload)
    ns = '{http://www.w3.org/2005/Atom}'
    if root.tag != ns + 'feed' or not root.findall(ns + 'entry'):
        raise ValueError('invalid or empty Atom feed')
    for node in [root, *root.findall(ns + 'entry')]:
        if any(not node.findtext(ns + field) for field in ('id', 'title', 'updated')):
            raise ValueError('missing Atom fields')
# Exact authored prose alias confirmed against the unchanged approved November
# source: row text, displayed alias and destination identifier, all SHA-256.
# This is not a general exemption for lowercase words, targets, or names.
AUTHORED_LIST_ALIAS = frozenset({
    ('e8a03c0a8f663b7b074d8b22389fe167db9b29731a0add8464f503b8989236eb', 'dd5c5362e52908c07c75195b77538bed8fe3784da5402e54675112bab9b6a5d4', '9fd0c5556bfe33c874a283e249538b041f89f0b523210981ce34887879c4f9c7'),
})


class RawNameLabels(HTMLParser):
    """Check labels in every list, regardless of heading or row position.

    Entry lists are checked in full; administrative pages retain the original
    related-list scope. Diagnostics never disclose the rejected name.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = []
        self.rows = []
        self.heading = None
        self.related = False
        self.list_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if re.fullmatch(r'h[1-6]', tag):
            self.heading = []
        if tag == 'li':
            self.list_text.append({'text': '', 'rows': []})
        if tag in {'a', 'code'} or (tag == 'span' and 'link-unavailable' in attrs.get('class', '').split()):
            field = bool(self.list_text)
            related_field = bool(self.related and self.list_text and
                                 not re.search(r'\s[—–-]\s', self.list_text[-1]['text']))
            target = attrs.get('href', '').split('#', 1)[0].split('?', 1)[0].rstrip('/').rsplit('/', 1)[-1]
            target = re.sub(r'\.(?:html|md)$', '', target)
            self.active.append((tag, [], field, related_field, hashlib.sha256(target.encode()).hexdigest()))

    def handle_endtag(self, tag):
        if self.active and self.active[-1][0] == tag:
            kind, parts, field, related_field, target_hash = self.active.pop()
            text = ''.join(parts).strip()
            if re.fullmatch(r'[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*', text):
                row = {'kind': kind, 'related_name_field': related_field, 'list_name_field': field,
                       'hyphenated': bool(re.search('[-_]', text)),
                       'label_sha256': hashlib.sha256(text.encode()).hexdigest(),
                       'target_sha256': target_hash}
                self.rows.append(row)
                if self.list_text:
                    self.list_text[-1]['rows'].append(row)
        if re.fullmatch(r'h[1-6]', tag) and self.heading is not None:
            heading = ''.join(self.heading).strip().casefold()
            self.related = heading.startswith('related ') or heading == 'connections'
            self.heading = None
        if tag == 'li' and self.list_text:
            item = self.list_text.pop()
            context = hashlib.sha256(' '.join(item['text'].split()).encode()).hexdigest()
            for row in item['rows']:
                row['list_text_sha256'] = context
                row['authored_alias'] = row['kind'] == 'a' and (
                    context, row['label_sha256'], row['target_sha256']) in AUTHORED_LIST_ALIAS

    def handle_data(self, data):
        for _, parts, _, _, _ in self.active:
            parts.append(data)
        if self.heading is not None:
            self.heading.append(data)
        if self.list_text:
            self.list_text[-1]['text'] += data


def inspect_raw_names(html, *, related_only=True, all_lists=True):
    parser = RawNameLabels()
    parser.feed(html)
    return [row for row in parser.rows if not row.get('authored_alias') and
            (not related_only or row['list_name_field' if all_lists else 'related_name_field'])]


def require_readable_names(html, *, all_lists=True):
    rows = inspect_raw_names(html, all_lists=all_lists)
    if rows:
        raise ValueError(f'raw page name label: {len(rows)} row(s); sha256={rows[0]["label_sha256"]}')
    return rows


def inline_dash_quotes(markdown):
    """Read exact quoted inline punctuation from the current source AST.

    A dash after a SoftBreak can be a swallowed list marker and never qualifies.
    No hash, name or edition exception: quotes must match the source verbatim
    after the same Pandoc rendering used for the entry.
    """
    document = json.loads(subprocess.run(
        ['pandoc', '--from=markdown', '--to=json'], input=markdown, text=True,
        capture_output=True, check=True).stdout)
    quotes = []

    def walk(value):
        if isinstance(value, dict):
            if value.get('t') == 'Quoted':
                tokens = value['c'][1]
                dashes = [i for i, node in enumerate(tokens) if node == {'t': 'Str', 'c': '-'}]
                if dashes and all(i > 0 and tokens[i-1]['t'] == 'Space' for i in dashes):
                    quotes.append(value)
                # Do not exempt a nested quote inside an ambiguous outer quote.
                return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(document['blocks'])
    rendered = []
    for quote in quotes:
        fragment = dict(document, meta={}, blocks=[{'t': 'Para', 'c': [quote]}])
        html = subprocess.run(['pandoc', '--from=json', '--to=html5'], input=json.dumps(fragment),
                              text=True, capture_output=True, check=True).stdout
        visible = HeadingsHTML()
        visible.feed(html)
        rendered.append(' '.join(''.join(visible.visible).split()))
    return rendered


def inspect_entry_text(html, *, raw_name_hashes=None, markdown=None):
    """Check raw page labels in prose, quotes, headings and lists alike.

    With a page inventory, only exact known tokens are names. Unknown
    hyphenated English stays prose. Inline markup does not break visible tokens.
    """
    names = [row for row in inspect_raw_names(html, related_only=False)
             if row['list_name_field'] or row.get('hyphenated')]
    known = set(raw_name_hashes or ())
    if raw_name_hashes is not None:
        names = [row for row in names if row['label_sha256'] in known]
    class VisibleParagraphs(HeadingsHTML):
        def handle_data(self, data):
            super().handle_data(re.sub(r'\s+', ' ', data))

    visible = VisibleParagraphs()
    visible.feed(html)
    collapsed = []
    text = ''.join(visible.visible)
    for match in re.finditer(r'(?<![\w-])[a-z][a-z0-9]*(?:[-_][a-z0-9]+)+(?![\w-])', text):
        fingerprint = hashlib.sha256(match[0].encode()).hexdigest()
        if fingerprint in known and not any(row['label_sha256'] == fingerprint for row in names):
            names.append({'kind': 'visible-text', 'label_sha256': fingerprint})
    quotes = inline_dash_quotes(markdown) if markdown is not None and re.search(r'\s-\s', text) else []
    for line in text.splitlines():
        # Preserve inline punctuation only inside an exact source-backed quote;
        # any dash left outside those spans is still a build failure.
        checked = line
        for quote in quotes:
            checked = checked.replace(quote, quote.replace(' - ', ' — '))
        # Pandoc folds a source newline inside a paragraph into whitespace.
        if re.search(r'\S[^\n]*[ \t]-[ \t]+\S', checked):
            collapsed.append({'text_sha256': hashlib.sha256(line.encode()).hexdigest()})
    return {'raw_page_names': names, 'collapsed_lists': collapsed}


def require_entry_text(html, *, raw_name_hashes=None, markdown=None):
    result = inspect_entry_text(html, raw_name_hashes=raw_name_hashes, markdown=markdown)
    if result['raw_page_names'] or result['collapsed_lists']:
        raise ValueError('entry text display failed: raw page names=' +
                         str(len(result['raw_page_names'])) + '; collapsed lists=' +
                         str(len(result['collapsed_lists'])))
    return result

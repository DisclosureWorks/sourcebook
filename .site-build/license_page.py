"""Render the exact local license text as readable, escaped HTML."""
from __future__ import annotations

import html
import re


def license_html(text: str) -> str:
    """Keep every word and list label; only whitespace and markup change."""
    introduction = (
        '<p>This site uses Creative Commons Attribution 4.0 International. '
        '<a href="https://creativecommons.org/licenses/by/4.0/">Read the official deed</a> '
        'or the <a href="/LICENSE">plain-text license</a>.</p>'
    )
    blocks = []
    paragraph = []

    def flush() -> None:
        if paragraph:
            blocks.append('<p>' + html.escape(' '.join(paragraph)) + '</p>')
            paragraph.clear()

    for number, line in enumerate(text.splitlines()):
        value = line.strip()
        if not value:
            flush()
        elif number == 0 or re.fullmatch(r'Section [0-9]+ -- .+', value):
            flush()
            tag = 'h1' if number == 0 else 'h2'
            blocks.append(f'<{tag}>' + html.escape(value) + f'</{tag}>')
        else:
            # Labels stay literal text, including adjacent a./b. and i./ii.
            if re.match(r'(?:[A-Za-z]|[0-9]+|[ivx]+)\.\s', value):
                flush()
            paragraph.append(value)
    flush()
    if not blocks:
        raise ValueError('LICENSE must contain text')
    return introduction + '\n<section aria-label="Full license text">\n' + '\n'.join(blocks) + '\n</section>'

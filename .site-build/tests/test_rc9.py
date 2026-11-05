from test_build import run_build
import pytest


@pytest.mark.parametrize('fault', ['raw', 'missing-note', 'invalid-xml', 'missing-feed'])
def test_current_delivery_fault_refuses(tmp_path, fault):
    src = tmp_path / 'src'
    (src / 'editions/2026-11').mkdir(parents=True)
    (src / 'editions/2026-11/index.md').write_text('# Edition\n')
    text = '# Entry\n\nA.[^1]\n\n[^1]: Source.\n'
    if fault == 'raw':
        text += '\n[^99]\n'
    elif fault == 'missing-note':
        text = text.replace('[^1]: Source.', '')
    (src / 'editions/2026-11/entry.md').write_text(text)
    if fault != 'missing-feed':
        feed = '<feed xmlns="http://www.w3.org/2005/Atom"><id>https://example.test/feed.xml</id><title>Fixture</title><updated>2026-11-05T00:00:00Z</updated><entry><id>https://example.test/editions/2026-11/</id><title>2026-11</title><updated>2026-11-05T00:00:00Z</updated></entry></feed>'
        (src / 'feed.xml').write_text('<feed>invalid' if fault == 'invalid-xml' else feed)
    result = run_build(src, tmp_path / 'out')
    assert result.returncode == 1
    assert ('note' in result.stderr if fault in {'raw', 'missing-note'} else 'feed' in result.stderr)


def test_assessment_paragraphs_form_one_box(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    text = '\n\n'.join(['# Assessment', '> **Our assessment**', '> **Conclusion:** Conclusion.',
        '> **Evidence base:** Sources.', '> **Would revise if:** Condition.',
        '> **Strongest counterargument:** Counter.', '> **Response:** Response.',
        '> Assessed 2026-11-01. [How we grade conclusions](/grading/)'])
    (src / 'index.md').write_text(text)
    (src / 'grading.md').write_text('# Grading\n')
    result = run_build(src, tmp_path / 'out')
    assert result.returncode == 0, result.stderr
    html = (tmp_path / 'out/index.html').read_text()
    assert html.count('<blockquote class="assessment">') == html.count('</blockquote>') == 1
    assert html.count('<p><strong>') == 6

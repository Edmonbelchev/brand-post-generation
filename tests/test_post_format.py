from app.generation.post_format import normalize_post_content, plain_text_to_html
from app.validation.plain_text import plain_text_from_post
from app.validation.hard_rules.validator import validate_hard_rules


def test_plain_text_converted_to_paragraphs():
    html = plain_text_to_html("Line one.\n\nLine two.")
    assert html == "<p>Line one.</p><p>Line two.</p>"


def test_html_sanitized_and_links_kept():
    raw = (
        '<p>Hello <strong>friend</strong> see '
        '<a href="https://driftwood.coffee/roast">our notes</a>.</p>'
        '<script>alert(1)</script>'
    )
    out = normalize_post_content(raw)
    assert "<strong>friend</strong>" in out
    assert 'href="https://driftwood.coffee/roast"' in out
    assert "script" not in out


def test_empty_anchor_gets_visible_href_text():
    raw = '<p>More at <a href="https://driftwood.coffee/roast"></a>.</p>'
    out = normalize_post_content(raw)
    assert "https://driftwood.coffee/roast" in out
    assert plain_text_from_post(out).count("https://driftwood.coffee/roast") == 1


def test_validation_uses_visible_text_from_html():
    post = '<p>We are <strong>the best</strong>. <a href="https://x.com">Shop</a></p>'
    plain = plain_text_from_post(post)
    assert "the best" in plain
    assert not validate_hard_rules(plain).passed

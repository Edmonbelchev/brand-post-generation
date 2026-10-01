from app.validation.plain_text import plain_text_from_post
from app.validation.hard_rules.validator import validate_hard_rules


def test_html_stripped_for_hard_rules():
    post = "<p>Our coffee is <strong>the best</strong>. <a href='https://x.com'>Buy now</a></p>"
    plain = plain_text_from_post(post)
    assert "the best" in plain
    assert "Buy now" in plain
    result = validate_hard_rules(plain)
    assert not result.passed


def test_markdown_link_stripped():
    plain = plain_text_from_post("Read [our story](https://example.com) today.")
    assert plain == "Read our story today."

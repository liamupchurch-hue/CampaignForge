"""Render light Markdown into Tk Text tags; keep clean copy independent of tags."""
from __future__ import annotations
import re
from oracle_session import clean_markdown


def render_message(text_widget, raw: str):
    """Add a legible formatted response without raw markdown punctuation.

    Tk's built-in text spans are used instead of embedding an HTML browser.
    """
    for original in str(raw or '').splitlines():
        line = original.strip()
        is_heading = bool(re.match(r'^#{1,6}\s+', line))
        is_list = bool(re.match(r'^[-*+]\s+', line))
        is_quote = line.startswith('> ')
        display = clean_markdown(original)
        tag = 'oracle_heading' if is_heading else ('oracle_list' if is_list else ('oracle_quote' if is_quote else 'oracle_body'))
        if not display:
            text_widget.insert('end', '\n')
            continue
        if is_heading:
            text_widget.insert('end', '\n' + display + '\n', tag)
        else:
            text_widget.insert('end', display + '\n', tag)
    text_widget.insert('end', '\n')

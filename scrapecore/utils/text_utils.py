"""
Text processing and Unicode normalization utilities.
"""

import re
import unicodedata


def strip_accents(text: str) -> str:
    """Convert accented Vietnamese text to plain ASCII for fuzzy searching and matching."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()


def clean_article_text(article_soup) -> str:
    """Extract clean multi-line text from an article HTML element."""
    if not article_soup:
        return ""
    # Replace <br/> tags with clean newlines
    for br in article_soup.find_all("br"):
        br.replace_with("\n")
    text = article_soup.get_text().strip()
    # Normalize carriage returns and excessive whitespace
    text = text.replace("\r", "")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

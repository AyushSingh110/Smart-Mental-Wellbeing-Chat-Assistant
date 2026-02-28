"""
Text preprocessing utilities applied before any ML model inference.
"""

from __future__ import annotations

import re
import unicodedata


def preprocess(text: str) -> str:
    """
    Clean and normalise user input:
      1. Unicode → ASCII‑safe
      2. Lowercase
      3. Strip URLs, emails, excessive whitespace
      4. Light contraction expansion
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.lower().strip()
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Remove emails
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Expand common contractions
    text = _expand_contractions(text)
    return text


_CONTRACTIONS: dict[str, str] = {
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "couldn't": "could not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "they're": "they are",
    "we're": "we are",
    "you're": "you are",
    "let's": "let us",
    "what's": "what is",
    "who's": "who is",
    "he's": "he is",
    "she's": "she is",
}


def _expand_contractions(text: str) -> str:
    for contraction, expansion in _CONTRACTIONS.items():
        text = text.replace(contraction, expansion)
    return text

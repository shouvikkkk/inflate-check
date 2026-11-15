"""Split instruction text into comparable items.

An "item" is one instruction: a bullet/numbered list entry, or one sentence
of a paragraph. Headings are kept as context on the item that follows them
so a rule like "## Testing" + "prefer pytest" stays one item.
"""

import re

_BULLET_RE = re.compile(r"^\s*(?:[-*•+]|\d+[.)])\s+(.*)$")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.*)$")

# Split sentences on . ! ? followed by whitespace + a capital letter or a
# digit, while protecting common abbreviations and decimal numbers.
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])"
)
_ABBREVIATIONS = ("e.g.", "i.e.", "vs.", "etc.", "Mr.", "Ms.", "Dr.", "St.")


def _split_sentences(text):
    """Split a paragraph into sentences, keeping abbreviations intact."""
    # Protect abbreviations with a placeholder so the split regex skips them.
    protected = text
    placeholders = {}
    for i, abbr in enumerate(_ABBREVIATIONS):
        token = "\x00ABBR%d\x00" % i
        if abbr in protected:
            protected = protected.replace(abbr, token)
            placeholders[token] = abbr
    parts = _SENTENCE_SPLIT_RE.split(protected)
    out = []
    for part in parts:
        for token, abbr in placeholders.items():
            part = part.replace(token, abbr)
        part = part.strip()
        if part:
            out.append(part)
    return out


def segment(text):
    """Return a list of instruction items from ``text``.

    Each item is a stripped string. Blank lines are skipped. A heading
    attaches to the next item as a ``"Heading: item"`` prefix so the item
    keeps its context.
    """
    items = []
    heading = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            heading = heading_match.group(1).strip()
            continue
        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            body = bullet_match.group(1).strip()
            if heading:
                items.append("%s: %s" % (heading, body))
                heading = None
            else:
                items.append(body)
            continue
        # Plain paragraph line: split into sentences.
        for sentence in _split_sentences(line):
            if heading:
                items.append("%s: %s" % (heading, sentence))
                heading = None
            else:
                items.append(sentence)
    return items

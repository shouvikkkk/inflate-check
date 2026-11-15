"""Classify aligned original/summary item pairs.

Verdicts per original item:

- ``PRESERVED`` — the summary keeps the instruction at the same strength
  and scope.
- ``INFLATED`` — the summary keeps the instruction but makes it broader or
  stronger. ``inflation_type`` names one of the four types from the
  Constraint Inflation paper; ``evidence`` quotes the exact word change.
- ``LOST`` — no summary item matches the original item at all.

A fifth verdict, ``EXTRA``, marks summary items that match no original
item (a summary addition, not an inflation — reported separately, never
counted in the inflation rate).

Confidence is HIGH when the trigger is an explicit modal/scope/quantifier
word change or a named old value; MEDIUM when the evidence is a single
weak marker (e.g. the original scope word is just "once"). No detector
fires on a bare similarity score.
"""

from . import lexicon
from .align import align


def _norm(value):
    return " ".join(value.lower().split())


# Leading words that carry no identity for a value ("the old X" is X).
_VALUE_FILLERS = ("the", "a", "an", "old", "new", "current", "previous",
                  "former", "legacy")


def _clean_value(value):
    """Strip leading articles/age words so "the old Memcached layer" -> "memcached layer".

    Also cuts a trailing prepositional tail ("pnpm for the build" -> "pnpm")
    so the value is the thing itself, not the sentence around it.
    """
    words = _norm(value).split()
    while words and words[0] in _VALUE_FILLERS:
        words.pop(0)
    cleaned = " ".join(words)
    for sep in (" for ", " in ", " with ", " to ", " on "):
        if sep in cleaned:
            cleaned = cleaned.split(sep, 1)[0]
    return cleaned.strip()


def _contains_value(text, value):
    """True when ``value`` appears as a whole-word phrase in ``text``."""
    import re

    pattern = r"(?<!\w)" + re.escape(value.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def detect_modal_inflation(original, summary):
    """Preference -> requirement: weak modal in original, strong in summary.

    Returns ``(strong_word, weak_word)`` or ``None``.
    """
    weak = lexicon.find_phrase(original, lexicon.WEAK_MODALS)
    if weak is None:
        return None
    strong = lexicon.find_phrase(summary, lexicon.STRONG_MODALS)
    if strong is None:
        return None
    # If the original already had a strong modal, the summary is not
    # strengthening anything.
    if lexicon.find_phrase(original, lexicon.STRONG_MODALS) is not None:
        return None
    return (strong, weak)


def detect_oneoff_inflation(original, summary):
    """One-off -> standing rule: scope marker dropped, standing phrasing added.

    Returns ``(marker, standing_word_or_None)`` or ``None``.
    """
    marker = lexicon.find_phrase(original, lexicon.ONE_OFF_MARKERS)
    if marker is None:
        return None
    if lexicon.find_phrase(summary, lexicon.ONE_OFF_MARKERS) is not None:
        return None  # summary kept the scope — no inflation
    standing = lexicon.find_phrase(summary, lexicon.STANDING_MARKERS)
    # Even without an explicit standing word, dropping the scope marker
    # turns a one-off into an unscoped (standing) rule.
    return (marker, standing)


def detect_scope_inflation(original, summary):
    """Narrow -> broad: narrow quantifier replaced by a broad one.

    Returns ``(broad_word, narrow_word)`` or ``None``.
    """
    narrow = lexicon.find_phrase(original, lexicon.NARROW_QUANTIFIERS)
    if narrow is None:
        return None
    broad = lexicon.find_phrase(summary, lexicon.BROAD_QUANTIFIERS)
    if broad is None:
        return None
    if lexicon.find_phrase(original, lexicon.BROAD_QUANTIFIERS) is not None:
        return None  # original was already broad
    return (broad, narrow)


def find_replacements(original):
    """Extract ``(old_value, new_value)`` pairs from replacement phrasing."""
    replacements = []
    for pattern in lexicon.REPLACEMENT_PATTERNS:
        for match in pattern.finditer(original):
            old = _clean_value(match.group("old"))
            new = _clean_value(match.group("new"))
            # Guard against runaway captures: values are short noun phrases.
            if old and new and len(old) <= 40 and len(new) <= 40 and old != new:
                replacements.append((old, new))
    return replacements


def detect_stale_value(original, summary):
    """Replaced value kept as current in the summary.

    The original says old -> new; the summary asserts the old value as
    current (mentions it without the new value and without a negation).
    Returns ``(old_value, new_value)`` or ``None``.
    """
    for old, new in find_replacements(original):
        if not _contains_value(summary, old):
            continue
        if _contains_value(summary, new):
            continue  # summary mentions the new value too — not stale
        if lexicon.find_phrase(summary, lexicon.NEGATION_WORDS) is not None:
            # "do not use Y" / "Y is deprecated" correctly rejects the old
            # value; only flag when the negation is near the old value.
            lowered = summary.lower()
            idx = lowered.find(old)
            window = lowered[max(0, idx - 30):idx + len(old) + 30]
            if lexicon.find_phrase(window, lexicon.NEGATION_WORDS) is not None:
                continue
        return (old, new)
    return None


def classify_pair(original, summary):
    """Classify one aligned pair. Returns a dict with verdict + evidence."""
    modal = detect_modal_inflation(original, summary)
    if modal is not None:
        strong, weak = modal
        return {
            "verdict": "INFLATED",
            "inflation_type": "preference-to-requirement",
            "confidence": "high",
            "evidence": "'%s' in original became '%s' in summary" % (weak, strong),
        }
    oneoff = detect_oneoff_inflation(original, summary)
    if oneoff is not None:
        marker, standing = oneoff
        if standing:
            evidence = "scope '%s' dropped; summary says '%s'" % (marker, standing)
            confidence = "high"
        else:
            evidence = "scope '%s' dropped; summary states the rule unscoped" % marker
            # "once" alone is a weak marker — medium confidence.
            confidence = "medium" if marker == "once" else "high"
        return {
            "verdict": "INFLATED",
            "inflation_type": "one-off-to-standing",
            "confidence": confidence,
            "evidence": evidence,
        }
    scope = detect_scope_inflation(original, summary)
    if scope is not None:
        broad, narrow = scope
        return {
            "verdict": "INFLATED",
            "inflation_type": "scope-broadening",
            "confidence": "medium" if broad == "any" else "high",
            "evidence": "'%s' in original became '%s' in summary" % (narrow, broad),
        }
    stale = detect_stale_value(original, summary)
    if stale is not None:
        old, new = stale
        return {
            "verdict": "INFLATED",
            "inflation_type": "stale-value-retained",
            "confidence": "high",
            "evidence": "original replaced '%s' with '%s'; summary still states '%s' as current"
            % (old, new, old),
        }
    return {
        "verdict": "PRESERVED",
        "inflation_type": None,
        "confidence": "high",
        "evidence": "same strength and scope",
    }


def audit(original_text, summary_text, min_similarity=None):
    """Audit a summary against its original. Returns the full report dict."""
    from .segment import segment

    kwargs = {}
    if min_similarity is not None:
        kwargs["min_similarity"] = min_similarity
    original_items = segment(original_text)
    summary_items = segment(summary_text)
    pairs, lost, extra = align(original_items, summary_items, **kwargs)

    results = []
    for oi, si, sim in pairs:
        verdict = classify_pair(original_items[oi], summary_items[si])
        results.append(
            {
                "original_index": oi,
                "summary_index": si,
                "similarity": round(sim, 2),
                "original": original_items[oi],
                "summary": summary_items[si],
                **verdict,
            }
        )
    for oi in lost:
        results.append(
            {
                "original_index": oi,
                "summary_index": None,
                "similarity": 0.0,
                "original": original_items[oi],
                "summary": None,
                "verdict": "LOST",
                "inflation_type": None,
                "confidence": "high",
                "evidence": "no matching summary item",
            }
        )
    results.sort(key=lambda r: r["original_index"])
    extras = [
        {"summary_index": si, "summary": summary_items[si]} for si in extra
    ]

    eligible = len(pairs)
    inflated = [r for r in results if r["verdict"] == "INFLATED"]
    high_inflated = [r for r in inflated if r["confidence"] == "high"]
    rate = (len(inflated) / eligible * 100.0) if eligible else 0.0
    return {
        "original_items": len(original_items),
        "summary_items": len(summary_items),
        "aligned": eligible,
        "lost": len(lost),
        "extra": extras,
        "inflated": len(inflated),
        "inflated_high_confidence": len(high_inflated),
        "inflation_rate_pct": round(rate, 1),
        "results": results,
    }

"""Align original items with summary items by token overlap.

Alignment is deliberately simple and transparent: normalised token sets,
Jaccard similarity, greedy best-match. A pair aligns when its similarity
meets ``MIN_SIMILARITY``; anything below that is treated as lost (original
side) or extra (summary side). No embedding, no model — the alignment is
fully inspectable, which is the point of a fail-closed audit tool.
"""

import re

MIN_SIMILARITY = 0.25

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Words that carry no alignment signal; they are dropped from the token
# sets so "the" and "a" cannot inflate a match.
STOPWORDS = frozenset(
    """
    a an the and or but if then else when while of to in on for with by at
    from as is are was were be been being it its this that these those
    you your we our they their he she his her not no do does did don't
    can could will would should may might must shall have has had
    """.split()
)


def tokenize(text):
    """Lowercase alphanumeric tokens, stopwords removed."""
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def jaccard(a, b):
    """Jaccard similarity of two token sets (0.0 when either is empty)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def align(original_items, summary_items, min_similarity=MIN_SIMILARITY):
    """Align each original item with its best summary item.

    Returns ``(pairs, lost, extra)`` where ``pairs`` is a list of
    ``(original_index, summary_index, similarity)`` in original order,
    ``lost`` is a list of original indices with no match, and ``extra`` is
    a list of summary indices matched to nothing.
    """
    orig_tokens = [tokenize(item) for item in original_items]
    summ_tokens = [tokenize(item) for item in summary_items]
    used_summary = set()
    pairs = []
    lost = []
    for oi, otoks in enumerate(orig_tokens):
        best_si = None
        best_sim = 0.0
        for si, stoks in enumerate(summ_tokens):
            if si in used_summary:
                continue
            sim = jaccard(otoks, stoks)
            if sim > best_sim:
                best_sim = sim
                best_si = si
        if best_si is not None and best_sim >= min_similarity:
            used_summary.add(best_si)
            pairs.append((oi, best_si, best_sim))
        else:
            lost.append(oi)
    extra = [si for si in range(len(summary_items)) if si not in used_summary]
    return pairs, lost, extra

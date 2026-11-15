"""Word lists for the inflation detectors.

The four inflation types from "Constraint Inflation: Context Compaction in
LLM Agents Rarely Loses Instructions but Often Overstates Them"
(ResearchSquare, posted 6 Nov 2026, preprint — not yet peer-reviewed):

1. preference -> requirement (modal ladder)
2. one-off -> standing rule (temporal scope dropped)
3. narrow scope -> broad scope (quantifier broadening)
4. replaced value kept as current (stale value)

These lists are deliberately conservative: a detector only fires on an
*explicit* word change, never on a bare similarity score. That keeps false
positives low at the cost of missing paraphrased inflation — the honest
trade-off, stated in the README.
"""

import re

# ---------------------------------------------------------------------------
# 1. Modal ladder: weak (preference) -> strong (requirement)
# ---------------------------------------------------------------------------

# Words/phrases that mark a preference, suggestion, or soft default.
WEAK_MODALS = (
    "prefer",
    "preferably",
    "try to",
    "try",
    "consider",
    "ideally",
    "if possible",
    "optionally",
    "optional",
    "maybe",
    "usually",
    "sometimes",
    "might",
    "could",
    "should",
    "when convenient",
    "if you like",
    "nice to have",
)

# Words/phrases that mark a hard requirement.
STRONG_MODALS = (
    "must",
    "always",
    "never",
    "required",
    "mandatory",
    "strictly",
    "only",
    "without exception",
    "at all times",
    "every time",
    "under no circumstances",
    "do not ever",
    "forbidden",
)

# ---------------------------------------------------------------------------
# 2. One-off scope markers
# ---------------------------------------------------------------------------

# Explicit markers that an instruction applies once / to one occasion.
ONE_OFF_MARKERS = (
    "just this once",
    "only this time",
    "this once",
    "for this file",
    "for this task",
    "for now",
    "today only",
    "in this session",
    "one-off",
    "one off",
    "once",
    "temporarily",
    "just for now",
    "just today",
    "this time only",
)

# Phrases that mark a standing rule (used to confirm a one-off became one).
STANDING_MARKERS = (
    "always",
    "every time",
    "from now on",
    "going forward",
    "as a rule",
    "in general",
    "whenever",
)

# ---------------------------------------------------------------------------
# 3. Quantifier broadening: narrow -> broad
# ---------------------------------------------------------------------------

NARROW_QUANTIFIERS = (
    "some",
    "this",
    "these",
    "a few",
    "certain",
    "specific",
    "particular",
    "that",
    "those",
)

BROAD_QUANTIFIERS = (
    "all",
    "every",
    "each",
    "any",
    "every single",
    "all of the",
)

# ---------------------------------------------------------------------------
# 4. Value replacement patterns
# ---------------------------------------------------------------------------

# Patterns that say "old value Y is replaced by new value X".
# Each pattern has one named group: ``old`` and one named group: ``new``.
REPLACEMENT_PATTERNS = (
    # "use X instead of Y"
    re.compile(
        r"use\s+(?P<new>[A-Za-z0-9_.\-/ ]+?)\s+instead of\s+(?P<old>[A-Za-z0-9_.\-/ ]+?)(?:[.,;]|$)",
        re.IGNORECASE,
    ),
    # "replace Y with X"
    re.compile(
        r"replace\s+(?P<old>[A-Za-z0-9_.\-/ ]+?)\s+with\s+(?P<new>[A-Za-z0-9_.\-/ ]+?)(?:[.,;]|$)",
        re.IGNORECASE,
    ),
    # "Y is now X" / "Y is replaced by X"
    re.compile(
        r"(?P<old>[A-Za-z0-9_.\-/ ]+?)\s+is (?:now|replaced by)\s+(?P<new>[A-Za-z0-9_.\-/ ]+?)(?:[.,;]|$)",
        re.IGNORECASE,
    ),
    # "switch from Y to X" / "change from Y to X"
    re.compile(
        r"(?:switch|change|move)\s+from\s+(?P<old>[A-Za-z0-9_.\-/ ]+?)\s+to\s+(?P<new>[A-Za-z0-9_.\-/ ]+?)(?:[.,;]|$)",
        re.IGNORECASE,
    ),
    # "X, not Y" (new first, old after "not")
    re.compile(
        r"(?P<new>[A-Za-z0-9_.\-/ ]+?),\s+not\s+(?P<old>[A-Za-z0-9_.\-/ ]+?)(?:[.,;]|$)",
        re.IGNORECASE,
    ),
)

# Words that negate a value mention in the summary ("do not use Y" is not
# a stale-value claim — the summary correctly rejects the old value).
NEGATION_WORDS = (
    "not",
    "no longer",
    "don't",
    "do not",
    "never",
    "instead of",
    "replaced",
    "deprecated",
    "removed",
    "avoid",
)


def find_phrase(text, phrases):
    """Return the first phrase from ``phrases`` present in ``text``.

    Matching is case-insensitive and word-boundary aware, so "only" does
    not match inside "lonely". Returns ``None`` when nothing matches.
    """
    lowered = text.lower()
    for phrase in phrases:
        if re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", lowered):
            return phrase
    return None


def find_all_phrases(text, phrases):
    """Return every phrase from ``phrases`` present in ``text``."""
    lowered = text.lower()
    found = []
    for phrase in phrases:
        if re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", lowered):
            found.append(phrase)
    return found

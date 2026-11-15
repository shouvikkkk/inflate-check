# inflate-check

Detect **constraint inflation** in compacted agent summaries — the failure
where a summary keeps an instruction but makes it broader or stronger than
the user meant.

## The problem

Long-running coding agents compress their conversation history when it
exceeds the context window. Prior work showed compaction can *lose*
instructions; the opposite failure is worse because it passes every
loss-check: the summary still contains the rule, so a survival auditor
scores it correct — while the agent now misbehaves on a rule that was
never that strong.

> "a summary keeps an instruction but makes it broader or stronger than
> the user meant" — *Constraint Inflation: Context Compaction in LLM
> Agents Rarely Loses Instructions but Often Overstates Them*,
> ResearchSquare, posted 6 Nov 2026 (preprint — not yet peer-reviewed).

Measured in that paper (InflateBench: 240 sessions, 10,080 summaries,
two model families):

- Standing instructions were almost never lost (**below 0.8%**), but
  summaries inflated **13%** of eligible items (free summary) and **19%**
  (sectioned template), mostly by turning preferences into requirements.
- One-offs without an explicit scope word were promoted to standing rules
  in **30%** of cases (12% with one).
- The published fixes *for loss* had no loss to prevent, yet raised
  inflation to **23%** and **41%** — and kept replaced values as current
  in up to **94%** of cases.

So the existing fix direction is actively harmful here, and every
existing compaction tool measures the *opposite* failure.

## What it checks

`inflate-check original.md summary.md` segments both files into
instruction items, aligns them by token overlap, and classifies each
aligned pair into one of the paper's four inflation types:

| Type | Original | Summary |
| --- | --- | --- |
| **preference-to-requirement** | "Prefer pytest" | "Always use pytest" |
| **one-off-to-standing** | "Just this once, skip the lint step" | "Skip the lint step" |
| **scope-broadening** | "Run it on some staging databases" | "Run it on all staging databases" |
| **stale-value-retained** | "Use Redis instead of Memcached" | "Memcached is the current cache" |

Each finding quotes the exact word change as evidence. Items with no
match are reported `LOST`; summary additions are reported separately
(they are not inflation).

## Usage

```bash
pip install .
inflate-check original.md summary.md
inflate-check original.md summary.md --format json
inflate-check original.md summary.md --threshold 5   # allow up to 5% inflation
```

Exit codes: `0` no inflation above the threshold, `1` inflation rate
exceeds `--threshold` (default: any inflation), `2` usage/input error.

```
$ inflate-check examples/inflated-original.md examples/inflated-summary.md
inflate-check: compaction inflation audit
original items: 6  |  summary items: 5  |  aligned: 5  |  lost: 1
inflated: 4 (high confidence: 4)  |  inflation rate: 80.0%  |  threshold: 0.0%

[INFLATED] Prefer pytest for new tests, but unittest is fine for quick checks.
    summary: Always use pytest for new tests; unittest is never allowed.
    preference-to-requirement (high confidence): 'prefer' in original became 'always' in summary
...
```

## How it works

- **Segmentation** — bullets/numbered items are instructions; paragraphs
  split into sentences (abbreviations protected); headings attach as
  context to the next item.
- **Alignment** — normalised token sets, Jaccard similarity, greedy
  best-match (threshold 0.25, `--min-similarity` to change). No model,
  no embeddings — the alignment is fully inspectable.
- **Detection** — a detector fires only on an *explicit* word change:
  a weak modal replaced by a strong one, a one-off scope word dropped,
  a narrow quantifier replaced by a broad one, or a replaced value
  asserted as current (with a negation guard, so "do not use MySQL"
  is not flagged). Never on a bare similarity score.
- **Confidence** — `high` for explicit lexical evidence; `medium` for
  a single weak marker (e.g. the original scope word is just "once",
  or the broad quantifier is the ambiguous "any").

## Differentiation

- **InflateBench** (the paper) is a benchmark of 240 synthetic sessions
  scored by model judges — not a tool you can run on your own summary.
- **compactsim / compaction-conformance-kit** measure loss/survival —
  exactly the blind spot: an inflated summary still *contains* the rule.
- **ARCBench** measures rule compliance by agent replay after
  compaction — a different failure (retained rule still violated).
- **ctxproof** (by the same author) checks compressor *integrity*
  (byte-exact corruption), not scope semantics. The two are
  complementary: a summary can be byte-faithful and still inflated.

## Honest limitations

- **Heuristic, not semantic.** Paraphrased inflation with no shared
  modal/scope/quantifier word is missed (false negatives). The fixture
  suite measures this: 24 paired cases, precision and recall ≥ 0.9 on
  fixtures — real summaries will be lower, and the README says so.
- **Short items align weakly.** Two one-line rules sharing a single
  content word can misalign; raise `--min-similarity` for strictness.
- **Value replacement is pattern-based.** "Use X instead of Y" style
  phrasing is recognised; pronoun values ("the old one") and
  multi-sentence supersession are not.
- **Weakening is not flagged.** A summary that *weakens* a rule ("always"
  → "use") is a different failure (loss of strength), reported as
  preserved here.
- **The evidence paper is a preprint** (ResearchSquare, 6 Nov 2026),
  not yet peer-reviewed; its numbers are quoted as reported.

## Tests

```bash
python3 -m unittest discover -s tests
```

45 tests: segmentation, alignment, each detector, the 24-pair fixture
suite with a precision/recall self-check, CLI exit codes and JSON shape.
All green locally.

## License

MIT — Copyright (c) 2026 Shouvik Maji.

"""Render audit reports as human-readable text or JSON."""

import json


def render_text(report, threshold):
    """Render the audit as plain text."""
    lines = []
    lines.append("inflate-check: compaction inflation audit")
    lines.append(
        "original items: %d  |  summary items: %d  |  aligned: %d  |  lost: %d"
        % (
            report["original_items"],
            report["summary_items"],
            report["aligned"],
            report["lost"],
        )
    )
    lines.append(
        "inflated: %d (high confidence: %d)  |  inflation rate: %.1f%%  |  threshold: %.1f%%"
        % (
            report["inflated"],
            report["inflated_high_confidence"],
            report["inflation_rate_pct"],
            threshold,
        )
    )
    lines.append("")
    for result in report["results"]:
        verdict = result["verdict"]
        if verdict == "PRESERVED":
            continue
        lines.append("[%s] %s" % (verdict, result["original"]))
        if result["summary"]:
            lines.append("    summary: %s" % result["summary"])
        lines.append(
            "    %s (%s confidence): %s"
            % (
                result["inflation_type"] or "lost",
                result["confidence"],
                result["evidence"],
            )
        )
        lines.append("")
    if report["extra"]:
        lines.append("Summary additions (no original item — not inflation):")
        for item in report["extra"]:
            lines.append("    + %s" % item["summary"])
        lines.append("")
    if report["inflated"] == 0 and report["lost"] == 0:
        lines.append("No inflation detected. Summary preserves scope and strength.")
    elif report["inflated"] == 0:
        lines.append("No inflation detected (%d item(s) lost — see above)." % report["lost"])
    return "\n".join(lines).rstrip() + "\n"


def render_json(report, threshold):
    """Render the audit as JSON (report plus the threshold used)."""
    payload = dict(report)
    payload["threshold_pct"] = threshold
    return json.dumps(payload, indent=2) + "\n"

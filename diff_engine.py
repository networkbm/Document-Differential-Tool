"""
diff_engine.py — Compares two sets of ControlSection objects and produces a DiffResult.
"""

import difflib
import re
from typing import List, Dict
from control_models import (
    ControlSection, ControlChange, DiffSummary, DiffResult
)

EXPAND_RATIO = 1.20
REDUCE_RATIO = 0.80
MINOR_CHANGE_RATIO = 0.95
SIGNIFICANT_CHANGE = 0.50
MAX_DETAILED_EDITS = 12
MAX_EDIT_TOKENS = 12

STRENGTHENING_SIGNALS = {
    "must": "stronger requirement language: must",
    "shall": "stronger requirement language: shall",
    "required": "stronger requirement language: required",
    "mandatory": "stronger requirement language: mandatory",
    "enforced": "explicit enforcement language",
    "all users": "broader scope (all users)",
    "automatically": "automation added",
    "automated": "automation added",
    "mfa": "stronger authentication controls (MFA)",
    "multi-factor": "stronger authentication controls (multi-factor)",
    "encrypt": "stronger encryption requirements",
    "waf": "added web application firewall control",
    "firewall": "stronger network boundary control",
    "segmentation": "added network segmentation control",
    "zero trust": "added zero trust control",
    "monitor": "expanded monitoring activity",
    "audit": "expanded audit activity",
}

WEAKENING_SIGNALS = {
    "optional": "requirement made optional",
    "may": "weaker discretionary language: may",
    "if applicable": "scope conditionalized: if applicable",
    "when possible": "implementation relaxed: when possible",
    "no longer": "explicit removal language",
    "deprecated": "capability marked deprecated",
    "manual": "manual process language introduced",
}

CADENCE_TO_DAYS = {
    "hourly": 1 / 24,
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "annually": 365,
    "yearly": 365,
}

SSP_FIELDS = [
    ("Responsible Role", ["responsible role", "responsible roles"]),
    ("Implementation Status", ["implementation status"]),
    ("Control Origination", ["control origination", "origination"]),
    (
        "Control Implementation",
        [
            "control implementation",
            "what is the solution and how is it implemented",
            "what is the solution and hos is it implemented",
            "how is it implemented",
            "implementation description",
        ],
    ),
]

TOOL_KEYWORDS = [
    "splunk", "elastic", "elk", "crowdstrike", "sentinelone", "defender",
    "okta", "ping", "cyberark", "tenable", "nessus", "qualys",
    "aws config", "guardduty", "security hub", "wiz", "prisma",
    "servicenow", "jira", "ansible", "terraform", "chef", "puppet",
]


def compute_diff(
    old_sections: Dict[str, ControlSection],
    new_sections: Dict[str, ControlSection],
    framework: str = "unknown",
    old_doc: str = "",
    new_doc: str = "",
    detailed_descriptions: bool = False,
    quick_scan: bool = False,
) -> DiffResult:
    result = DiffResult(framework=framework, old_doc=old_doc, new_doc=new_doc)
    summary = DiffSummary()
    changes: List[ControlChange] = []

    all_ids = sorted(set(old_sections) | set(new_sections))

    for cid in all_ids:
        old_sec = old_sections.get(cid)
        new_sec = new_sections.get(cid)

        if old_sec is None and new_sec is not None:
            description = "Control section added in new document."
            if detailed_descriptions and not quick_scan:
                details = _added_removed_details(new_sec.content, added=True)
                if details:
                    description = f"{description} {details}"
            elif quick_scan:
                description = _quick_scan_description("", new_sec.content)
            changes.append(ControlChange(
                control_id=cid,
                title=new_sec.title,
                change_type="added",
                new_content=new_sec.content,
                description=description,
                impact="New requirement introduced",
            ))
            summary.added += 1

        elif old_sec is not None and new_sec is None:
            description = "Control section removed from new document."
            if detailed_descriptions and not quick_scan:
                details = _added_removed_details(old_sec.content, added=False)
                if details:
                    description = f"{description} {details}"
            elif quick_scan:
                description = _quick_scan_description(old_sec.content, "")
            changes.append(ControlChange(
                control_id=cid,
                title=old_sec.title,
                change_type="removed",
                old_content=old_sec.content,
                description=description,
                impact="Requirement no longer present — review needed",
            ))
            summary.removed += 1

        else:
            change = _compare_sections(
                old_sec,
                new_sec,
                detailed_descriptions=detailed_descriptions,
                quick_scan=quick_scan,
            )
            if change:
                changes.append(change)
                if change.change_type == "expanded":
                    summary.expanded += 1
                elif change.change_type == "reduced":
                    summary.reduced += 1
                elif change.change_type == "narrative_changed":
                    summary.modified += 1
                else:
                    summary.modified += 1
            else:
                summary.unchanged += 1

    result.summary = summary
    result.changes = changes
    return result


def _compare_sections(
    old: ControlSection,
    new: ControlSection,
    detailed_descriptions: bool = False,
    quick_scan: bool = False,
) -> ControlChange | None:
    old_text = old.content.strip()
    new_text = new.content.strip()

    old_norm = " ".join(old_text.split())
    new_norm = " ".join(new_text.split())

    if old_norm == new_norm:
        return None

    ratio = difflib.SequenceMatcher(None, old_norm, new_norm).ratio()
    old_len = len(old_norm)
    new_len = len(new_norm)

    if ratio >= MINOR_CHANGE_RATIO:
        change_type = "narrative_changed"
        description = _describe_minor_change(old_norm, new_norm)
        impact = "Minor rewording or formatting change"
    elif new_len > old_len * EXPAND_RATIO:
        change_type = "expanded"
        description = _describe_expansion(old_norm, new_norm, ratio)
        impact = _expansion_impact(old_norm, new_norm)
    elif new_len < old_len * REDUCE_RATIO:
        change_type = "reduced"
        description = _describe_reduction(old_norm, new_norm, ratio)
        impact = _reduction_impact(old_norm, new_norm)
    else:
        change_type = "modified"
        description = _describe_modification(old_norm, new_norm, ratio)
        impact = _modification_impact(old_norm, new_norm)

    if quick_scan:
        description = _quick_scan_description(old_text, new_text)

    ssp_details = _ssp_field_changes(old_text, new_text, detailed=detailed_descriptions)
    if ssp_details and not quick_scan:
        if detailed_descriptions:
            description = f"{description}\n\nSSP field changes:\n{ssp_details}"
        else:
            description = f"{description} {ssp_details}"

    if detailed_descriptions and not ssp_details and not quick_scan:
        details = _detailed_sentence_changes(old_text, new_text)
        if details:
            description = f"{description}\n\nDetailed changes:\n{details}"

    return ControlChange(
        control_id=old.control_id,
        title=new.title or old.title,
        change_type=change_type,
        old_content=old.content,
        new_content=new.content,
        description=description,
        impact=impact,
    )


def _diff_lines(old: str, new: str) -> List[str]:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    return list(difflib.unified_diff(old_lines, new_lines, lineterm=""))


def _first_diff(old: str, new: str) -> str:
    sm = difflib.SequenceMatcher(None, old.split(), new.split())
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            removed = " ".join(old.split()[i1:i2])[:60]
            added = " ".join(new.split()[j1:j2])[:60]
            return f'"{removed}" -> "{added}"'
        if tag == "delete":
            removed = " ".join(old.split()[i1:i2])[:80]
            return f'Removed: "{removed}"'
        if tag == "insert":
            added = " ".join(new.split()[j1:j2])[:80]
            return f'Added: "{added}"'
    return "Content changed."


def _describe_minor_change(old: str, new: str) -> str:
    return f"Minor wording change. {_first_diff(old, new)}"


def _describe_expansion(old: str, new: str, ratio: float) -> str:
    added_pct = int(((len(new) - len(old)) / max(len(old), 1)) * 100)
    return f"Content expanded by approximately {added_pct}%. {_first_diff(old, new)}"


def _describe_reduction(old: str, new: str, ratio: float) -> str:
    removed_pct = int(((len(old) - len(new)) / max(len(old), 1)) * 100)
    return f"Content reduced by approximately {removed_pct}%. {_first_diff(old, new)}"


def _describe_modification(old: str, new: str, ratio: float) -> str:
    similarity = int(ratio * 100)
    return f"Content modified (similarity: {similarity}%). {_first_diff(old, new)}"


def _expansion_impact(old: str, new: str) -> str:
    impact = _impact_summary(old, new)
    if impact.startswith("Review required") or impact.startswith("Mixed impact"):
        return f"Implementation scope expanded; {impact}"
    return impact


def _modification_impact(old: str, new: str) -> str:
    return _impact_summary(old, new)


def _reduction_impact(old: str, new: str) -> str:
    impact = _impact_summary(old, new)
    if impact.startswith("Security posture likely weakened"):
        return impact
    if impact.startswith("Security posture likely strengthened"):
        return f"Content reduced, but controls appear stronger: {impact.split(': ', 1)[-1]}"
    if impact.startswith("Mixed impact"):
        return f"Implementation narrative reduced with mixed impact: {impact.split(': ', 1)[-1]}"
    return "Implementation narrative reduced — review for coverage gaps"


def _impact_summary(old: str, new: str) -> str:
    old_lower = old.lower()
    new_lower = new.lower()

    strengthening_reasons: List[str] = []
    weakening_reasons: List[str] = []

    added_strong, removed_strong = _signal_deltas(old_lower, new_lower, STRENGTHENING_SIGNALS)
    added_weak, removed_weak = _signal_deltas(old_lower, new_lower, WEAKENING_SIGNALS)

    strengthening_reasons.extend(added_strong)
    strengthening_reasons.extend([f"removed weaker language ({reason})" for reason in removed_weak])

    weakening_reasons.extend(added_weak)
    weakening_reasons.extend([f"removed stronger control ({reason})" for reason in removed_strong])

    cadence_reason = _cadence_delta(old_lower, new_lower)
    if cadence_reason:
        direction, detail = cadence_reason
        if direction == "stronger":
            strengthening_reasons.append(detail)
        else:
            weakening_reasons.append(detail)

    strengthening_reasons = _dedupe(strengthening_reasons)
    weakening_reasons = _dedupe(weakening_reasons)

    if strengthening_reasons and not weakening_reasons:
        return f"Security posture likely strengthened: {', '.join(strengthening_reasons[:3])}"
    if weakening_reasons and not strengthening_reasons:
        return f"Security posture likely weakened: {', '.join(weakening_reasons[:3])}"
    if strengthening_reasons and weakening_reasons:
        return (
            f"Mixed impact: strengthened by {', '.join(strengthening_reasons[:2])}; "
            f"weakened by {', '.join(weakening_reasons[:2])}"
        )
    return "Review required to assess security impact"


def _signal_deltas(old_lower: str, new_lower: str, signal_map: Dict[str, str]) -> tuple[list, list]:
    added_reasons = []
    removed_reasons = []
    for phrase, reason in signal_map.items():
        in_old = _contains_phrase(old_lower, phrase)
        in_new = _contains_phrase(new_lower, phrase)
        if in_new and not in_old:
            added_reasons.append(reason)
        elif in_old and not in_new:
            removed_reasons.append(reason)
    return added_reasons, removed_reasons


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, text) is not None


def _cadence_delta(old_lower: str, new_lower: str) -> tuple[str, str] | None:
    old_cadence = _best_cadence(old_lower)
    new_cadence = _best_cadence(new_lower)
    if not old_cadence or not new_cadence or old_cadence == new_cadence:
        return None

    old_days = CADENCE_TO_DAYS[old_cadence]
    new_days = CADENCE_TO_DAYS[new_cadence]
    if new_days < old_days:
        return "stronger", f"review cadence tightened ({old_cadence} -> {new_cadence})"
    return "weaker", f"review cadence relaxed ({old_cadence} -> {new_cadence})"


def _best_cadence(text: str) -> str | None:
    found = [c for c in CADENCE_TO_DAYS if _contains_phrase(text, c)]
    if not found:
        return None
    return min(found, key=lambda c: CADENCE_TO_DAYS[c])


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def _normalize_label(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _extract_ssp_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, List[str]] = {}
    current_field = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current_field and fields.get(current_field):
                fields[current_field].append("")
            continue

        normalized = _normalize_label(line)
        matched_field = None
        remainder = ""

        for field_name, aliases in SSP_FIELDS:
            for alias in aliases:
                if normalized == alias or normalized.startswith(alias + " "):
                    matched_field = field_name
                    pattern = rf"^\s*[#\-\*\d\.\)\(\s]*{re.escape(alias)}\s*[:\-–—]?\s*(.*)$"
                    m = re.match(pattern, line, flags=re.IGNORECASE)
                    remainder = (m.group(1) if m else "").strip()
                    break
            if matched_field:
                break

        if matched_field:
            current_field = matched_field
            fields.setdefault(current_field, [])
            if remainder:
                fields[current_field].append(remainder)
            continue

        if current_field:
            fields.setdefault(current_field, []).append(line)

    result: Dict[str, str] = {}
    for key, values in fields.items():
        compact = " ".join(v for v in values if v.strip()).strip()
        if compact:
            result[key] = compact
    return result


def _ssp_field_changes(old_text: str, new_text: str, detailed: bool = False) -> str:
    old_fields = _extract_ssp_fields(old_text)
    new_fields = _extract_ssp_fields(new_text)
    changed = []

    for field_name, _ in SSP_FIELDS:
        old_val = old_fields.get(field_name)
        new_val = new_fields.get(field_name)
        if old_val is None and new_val is None:
            continue
        old_norm = " ".join((old_val or "").split())
        new_norm = " ".join((new_val or "").split())
        if old_norm == new_norm:
            continue
        changed.append((field_name, old_val, new_val))

    if not changed:
        return ""

    if detailed:
        lines = []
        for field_name, old_val, new_val in changed:
            if old_val and new_val:
                lines.append(f'- {field_name}: "{_clip(old_val, 140)}" -> "{_clip(new_val, 140)}"')
            elif new_val:
                lines.append(f'- {field_name}: added "{_clip(new_val, 140)}"')
            else:
                lines.append(f'- {field_name}: removed "{_clip(old_val, 140)}"')
        return "\n".join(lines)

    parts = []
    for field_name, old_val, new_val in changed:
        if field_name == "Implementation Status" and old_val and new_val:
            parts.append(f'{field_name} ({_clip(old_val, 40)} -> {_clip(new_val, 40)})')
        else:
            parts.append(field_name)

    preview = ", ".join(parts[:3])
    if len(parts) > 3:
        preview += f", +{len(parts) - 3} more"
    return f"SSP fields changed: {preview}."


def _find_all(text: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, text, flags=re.IGNORECASE))


def _quick_scan_description(old: str, new: str) -> str:
    old_lower = old.lower()
    new_lower = new.lower()
    findings: List[str] = []

    if "http://" in old_lower and "https://" in new_lower and "https://" not in old_lower:
        findings.append("protocol HTTP -> HTTPS")
    elif "https://" in old_lower and "http://" in new_lower and "http://" not in old_lower:
        findings.append("protocol HTTPS -> HTTP")

    old_tls = _find_all(old_lower, r"tls\s*1\.[0-3]")
    new_tls = _find_all(new_lower, r"tls\s*1\.[0-3]")
    added_tls = sorted(new_tls - old_tls)
    removed_tls = sorted(old_tls - new_tls)
    if added_tls:
        findings.append(f"TLS added ({', '.join(added_tls)})")
    if removed_tls:
        findings.append(f"TLS removed ({', '.join(removed_tls)})")

    old_ports = _find_all(old_lower, r"\bport\s+(\d{2,5})\b")
    new_ports = _find_all(new_lower, r"\bport\s+(\d{2,5})\b")
    if old_ports != new_ports and (old_ports or new_ports):
        added_ports = sorted(new_ports - old_ports)
        removed_ports = sorted(old_ports - new_ports)
        if added_ports:
            findings.append(f"ports added ({', '.join(added_ports)})")
        if removed_ports:
            findings.append(f"ports removed ({', '.join(removed_ports)})")

    added_tools = [t for t in TOOL_KEYWORDS if t in new_lower and t not in old_lower]
    removed_tools = [t for t in TOOL_KEYWORDS if t in old_lower and t not in new_lower]
    if added_tools:
        findings.append(f"new tools ({', '.join(added_tools[:4])})")
    if removed_tools:
        findings.append(f"tools removed ({', '.join(removed_tools[:4])})")

    if _ssp_field_changes(old, new, detailed=True):
        findings.append("SSP fields updated")

    if not findings:
        return f"Quick scan summary: {_first_diff(' '.join(old.split()), ' '.join(new.split()))}"

    findings = findings[:6]
    return "Quick scan summary: " + "; ".join(findings) + "."


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _clip(text: str, max_len: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1].rstrip() + "…"


def _added_removed_details(content: str, added: bool) -> str:
    sentences = _split_sentences(content)
    if not sentences:
        return ""
    if len(sentences) == 1:
        prefix = "Added text:" if added else "Removed text:"
        return f'{prefix} "{_clip(sentences[0])}"'
    prefix = "Added content includes" if added else "Removed content included"
    items = "\n".join([f"- {_clip(s)}" for s in sentences])
    return f"{prefix} {len(sentences)} sentence(s):\n{items}"


def _tokenize_change_units(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9_./-]*", text)


def _format_edit_chunk(tokens: List[str]) -> str:
    if not tokens:
        return ""
    return _clip(" ".join(tokens[:MAX_EDIT_TOKENS]), 90)


def _detailed_sentence_changes(old: str, new: str) -> str:
    old_tokens = _tokenize_change_units(old)
    new_tokens = _tokenize_change_units(new)
    if not old_tokens and not new_tokens:
        return ""

    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
    lines: List[str] = []
    truncated = False

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        old_chunk = _format_edit_chunk(old_tokens[i1:i2])
        new_chunk = _format_edit_chunk(new_tokens[j1:j2])

        if tag == "replace":
            if old_chunk and new_chunk and old_chunk != new_chunk:
                lines.append(f'- Changed: "{old_chunk}" -> "{new_chunk}"')
        elif tag == "delete":
            if old_chunk:
                lines.append(f'- Removed: "{old_chunk}"')
        elif tag == "insert":
            if new_chunk:
                lines.append(f'- Added: "{new_chunk}"')

        if len(lines) >= MAX_DETAILED_EDITS:
            truncated = True
            break

    if not lines:
        return ""
    if truncated:
        lines.append("- Additional edits omitted for brevity.")
    return "\n".join(lines)


def inline_diff(old: str, new: str) -> str:
    old_lines = old.strip().splitlines()
    new_lines = new.strip().splitlines()
    diff = difflib.unified_diff(old_lines, new_lines, lineterm="", n=2)
    return "\n".join(list(diff)[2:])

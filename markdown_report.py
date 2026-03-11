"""
markdown_report.py — Renders a DiffResult as a Markdown document.
"""

from control_models import DiffResult

CHANGE_EMOJI = {
    "added":            "🟢",
    "removed":          "🔴",
    "modified":         "🟡",
    "expanded":         "🔵",
    "reduced":          "🟠",
    "narrative_changed": "⬜",
}


def _append_multiline_markdown(lines: list[str], title: str, text: str):
    lines.append(f"**{title}:**")
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- "):
            lines.append(line)
        else:
            lines.append(f"- {line}")
    lines.append("")


def render(result: DiffResult, include_content: bool = True) -> str:
    s = result.summary
    lines = []

    lines.append("# FrameDiff Report")
    lines.append("")
    lines.append(f"**Framework:** {result.framework.upper()}  ")
    lines.append(f"**Old document:** `{result.old_doc}`  ")
    lines.append(f"**New document:** `{result.new_doc}`  ")
    lines.append(f"**Generated:** {result.generated_at}  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Controls Modified | {s.modified + s.expanded + s.reduced} |")
    lines.append(f"| Controls Added | {s.added} |")
    lines.append(f"| Controls Removed | {s.removed} |")
    lines.append(f"| Rewording Only | {s.modified} |")
    lines.append(f"| Unchanged | {s.unchanged} |")
    lines.append(f"| **Total Changes** | **{s.total_changes}** |")
    lines.append("")

    if not result.changes:
        lines.append("> ✅ No meaningful changes detected between documents.")
        return "\n".join(lines)

    lines.append("---")
    lines.append("")
    lines.append("## Changes")
    lines.append("")

    for change in result.changes:
        emoji = CHANGE_EMOJI.get(change.change_type, "⬜")
        title = change.title or change.control_id
        lines.append(f"### {emoji} {change.control_id} — {title}")
        lines.append("")
        lines.append(f"**Change Type:** `{change.change_type.upper()}`")
        lines.append("")
        _append_multiline_markdown(lines, "Description", change.description)
        if change.impact:
            _append_multiline_markdown(lines, "Impact", change.impact)

        if include_content and change.old_content and change.new_content:
            lines.append("<details>")
            lines.append("<summary>View old/new content</summary>")
            lines.append("")
            lines.append("**Old:**")
            lines.append("```")
            lines.append(change.old_content.strip())
            lines.append("```")
            lines.append("")
            lines.append("**New:**")
            lines.append("```")
            lines.append(change.new_content.strip())
            lines.append("```")
            lines.append("")
            lines.append("</details>")
            lines.append("")

    return "\n".join(lines)

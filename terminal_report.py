"""
terminal_report.py — Renders a DiffResult to the terminal with ANSI color.
Falls back gracefully if colors aren't supported.
"""

import sys
import os
from control_models import DiffResult, ControlChange

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(text: str, *codes: str) -> str:
    if not _USE_COLOR:
        return text
    return "".join(codes) + text + RESET


def _change_color(change_type: str) -> str:
    return {
        "added": GREEN,
        "removed": RED,
        "modified": YELLOW,
        "expanded": CYAN,
        "reduced": YELLOW,
        "narrative_changed": BLUE,
    }.get(change_type, WHITE)


def _change_label(change_type: str) -> str:
    return {
        "added": "ADDED",
        "removed": "REMOVED",
        "modified": "MODIFIED",
        "expanded": "EXPANDED",
        "reduced": "REDUCED",
        "narrative_changed": "REWORDING",
    }.get(change_type, change_type.upper())


def _append_block(lines: list[str], label: str, content: str):
    block_lines = content.splitlines() if content else [""]
    first = block_lines[0] if block_lines else ""
    lines.append(f"    {_c(label, DIM)} {first}")
    for extra in block_lines[1:]:
        lines.append(f"    {_c('', DIM):<11} {extra}")


def render(result: DiffResult, show_diff: bool = False, verbose: bool = False) -> str:
    lines = []

    lines.append("")
    lines.append(_c("╔══════════════════════════════════════════╗", BOLD, BLUE))
    lines.append(_c("║           FrameDiff Report               ║", BOLD, BLUE))
    lines.append(_c("╚══════════════════════════════════════════╝", BOLD, BLUE))
    lines.append("")
    lines.append(f"  {_c('Framework:', BOLD)} {result.framework.upper()}")
    lines.append(f"  {_c('Old doc:', BOLD)}  {result.old_doc}")
    lines.append(f"  {_c('New doc:', BOLD)}  {result.new_doc}")
    lines.append(f"  {_c('Generated:', BOLD)} {result.generated_at}")
    lines.append("")

    s = result.summary
    lines.append(_c("  Summary", BOLD, WHITE))
    lines.append("  " + "─" * 42)
    lines.append(f"  {_c('Controls Modified:', BOLD)}   {_c(str(s.modified + s.expanded + s.reduced), YELLOW)}")
    lines.append(f"  {_c('Controls Added:', BOLD)}      {_c(str(s.added), GREEN)}")
    lines.append(f"  {_c('Controls Removed:', BOLD)}    {_c(str(s.removed), RED)}")
    lines.append(f"  {_c('Rewording Only:', BOLD)}      {_c(str(s.modified), BLUE)}")
    lines.append(f"  {_c('Unchanged:', BOLD)}           {_c(str(s.unchanged), GRAY)}")
    lines.append(f"  {_c('Total Changes:', BOLD)}       {_c(str(s.total_changes), WHITE)}")
    lines.append("")

    if not result.changes:
        lines.append(_c("  ✓ No changes detected between documents.", GREEN, BOLD))
        lines.append("")
        return "\n".join(lines)

    lines.append(_c("  Changes", BOLD, WHITE))
    lines.append("  " + "─" * 42)
    lines.append("")

    for change in result.changes:
        color = _change_color(change.change_type)
        label = _change_label(change.change_type)
        title = change.title or change.control_id

        lines.append(f"  {_c(change.control_id, BOLD, color)}  {_c(title, BOLD)}")
        lines.append(f"    {_c('Change Type:', DIM)} {_c(label, color)}")
        _append_block(lines, "Description:", change.description)
        if change.impact:
            _append_block(lines, "Impact:", change.impact)

        if verbose and change.old_content and change.new_content:
            from diff_engine import inline_diff
            diff_text = inline_diff(change.old_content, change.new_content)
            if diff_text.strip():
                lines.append(f"    {_c('Diff:', DIM)}")
                for dline in diff_text.splitlines():
                    if dline.startswith("+"):
                        lines.append("      " + _c(dline, GREEN))
                    elif dline.startswith("-"):
                        lines.append("      " + _c(dline, RED))
                    elif dline.startswith("@"):
                        lines.append("      " + _c(dline, CYAN))
                    else:
                        lines.append("      " + _c(dline, GRAY))

        lines.append("")

    return "\n".join(lines)

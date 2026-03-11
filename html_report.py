"""
html_report.py — Renders a DiffResult as a self-contained HTML file.
"""

import html as html_lib
import re
from control_models import DiffResult

CHANGE_COLORS = {
    "added":            ("#d4edda", "#28a745", "ADDED"),
    "removed":          ("#f8d7da", "#dc3545", "REMOVED"),
    "modified":         ("#fff3cd", "#856404", "MODIFIED"),
    "expanded":         ("#cce5ff", "#004085", "EXPANDED"),
    "reduced":          ("#ffeeba", "#856404", "REDUCED"),
    "narrative_changed": ("#e2e3e5", "#383d41", "REWORDING"),
}


def _format_multiline(text: str) -> str:
    parts = []
    for raw in text.splitlines():
        line = html_lib.escape(raw.strip())
        if not line:
            continue
        if line.startswith("- "):
            parts.append(f"&bull; {line[2:]}")
        else:
            parts.append(line)
    return "<br>".join(parts)


def _normalize_display_content(text: str) -> str:
    cleaned = []
    for raw in text.splitlines():
        line = raw.replace("\u00a0", " ").replace("\t", " ")
        line = re.sub(r"[ ]{2,}", " ", line).rstrip()
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def render(result: DiffResult, include_content: bool = True) -> str:
    s = result.summary
    changes_html = ""

    for change in result.changes:
        bg, fg, label = CHANGE_COLORS.get(change.change_type, ("#fff", "#000", change.change_type.upper()))
        title = html_lib.escape(change.title or change.control_id)
        cid = html_lib.escape(change.control_id)
        desc_html = _format_multiline(change.description)
        impact_html = _format_multiline(change.impact or "")
        old_c = html_lib.escape(_normalize_display_content(change.old_content or ""))
        new_c = html_lib.escape(_normalize_display_content(change.new_content or ""))

        diff_section = ""
        if include_content and change.old_content and change.new_content:
            diff_section = f"""
            <details>
              <summary style="cursor:pointer;color:#555;font-size:0.9em;">▶ View old/new content</summary>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;">
                <div>
                  <div style="font-size:0.8em;font-weight:bold;color:#666;margin-bottom:4px;">OLD</div>
                  <pre style="background:#f8f9fa;padding:10px;border-radius:4px;font-size:0.8em;overflow:auto;white-space:pre-wrap;border-left:3px solid #dc3545;">{old_c}</pre>
                </div>
                <div>
                  <div style="font-size:0.8em;font-weight:bold;color:#666;margin-bottom:4px;">NEW</div>
                  <pre style="background:#f8f9fa;padding:10px;border-radius:4px;font-size:0.8em;overflow:auto;white-space:pre-wrap;border-left:3px solid #28a745;">{new_c}</pre>
                </div>
              </div>
            </details>"""

        changes_html += f"""
        <div style="border:1px solid #dee2e6;border-radius:6px;margin-bottom:16px;overflow:hidden;">
          <div style="background:{bg};border-left:5px solid {fg};padding:12px 16px;">
            <div style="display:flex;align-items:center;gap:12px;">
              <code style="font-size:1.1em;font-weight:bold;color:{fg};">{cid}</code>
              <span style="font-weight:bold;">{title}</span>
              <span style="margin-left:auto;background:{fg};color:white;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:bold;">{label}</span>
            </div>
          </div>
          <div style="padding:12px 16px;font-size:0.9em;">
            <p style="margin:6px 0;"><strong>Description:</strong><br>{desc_html}</p>
            {f'<p style="margin:6px 0;"><strong>Impact:</strong><br>{impact_html}</p>' if impact_html else ''}
            {diff_section}
          </div>
        </div>"""

    no_changes = ""
    if not result.changes:
        no_changes = '<div style="background:#d4edda;border:1px solid #c3e6cb;border-radius:6px;padding:20px;text-align:center;color:#155724;font-weight:bold;">✅ No meaningful changes detected between documents.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FrameDiff Report — {html_lib.escape(result.framework.upper())}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f7fa; color: #212529; }}
    .container {{ max-width: 960px; margin: 40px auto; padding: 0 20px; }}
    header {{ background: #1b3a6b; color: white; padding: 24px 32px; border-radius: 8px; margin-bottom: 24px; }}
    header h1 {{ margin: 0 0 4px 0; font-size: 1.8em; }}
    header p {{ margin: 0; opacity: 0.75; font-size: 0.9em; }}
    .meta {{ display: flex; gap: 24px; flex-wrap: wrap; margin-top: 12px; font-size: 0.85em; opacity: 0.9; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 24px; }}
    .stat {{ background: white; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .stat .number {{ font-size: 2em; font-weight: bold; }}
    .stat .label {{ font-size: 0.8em; color: #666; margin-top: 4px; }}
    h2 {{ color: #1b3a6b; border-bottom: 2px solid #dee2e6; padding-bottom: 8px; }}
    pre {{ margin: 0; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🔍 FrameDiff Report</h1>
      <p>Compliance Document Comparison</p>
      <div class="meta">
        <span><strong>Framework:</strong> {html_lib.escape(result.framework.upper())}</span>
        <span><strong>Old:</strong> {html_lib.escape(result.old_doc)}</span>
        <span><strong>New:</strong> {html_lib.escape(result.new_doc)}</span>
        <span><strong>Generated:</strong> {html_lib.escape(result.generated_at)}</span>
      </div>
    </header>

    <h2>Summary</h2>
    <div class="summary-grid">
      <div class="stat"><div class="number" style="color:#856404;">{s.modified + s.expanded + s.reduced}</div><div class="label">Modified</div></div>
      <div class="stat"><div class="number" style="color:#28a745;">{s.added}</div><div class="label">Added</div></div>
      <div class="stat"><div class="number" style="color:#dc3545;">{s.removed}</div><div class="label">Removed</div></div>
      <div class="stat"><div class="number" style="color:#004085;">{s.expanded}</div><div class="label">Expanded</div></div>
      <div class="stat"><div class="number" style="color:#856404;">{s.reduced}</div><div class="label">Reduced</div></div>
      <div class="stat"><div class="number" style="color:#383d41;">{s.unchanged}</div><div class="label">Unchanged</div></div>
    </div>

    <h2>Changes</h2>
    {no_changes}
    {changes_html}
  </div>
</body>
</html>"""

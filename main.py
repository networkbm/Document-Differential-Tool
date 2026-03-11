# ================================================================
# ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗██████╗ ███╗   ███╗
# ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔══██╗████╗ ████║
# ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝ ██████╔╝██╔████╔██║
# ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══██╗██║╚██╔╝██║
# ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗██████╔╝██║ ╚═╝ ██║
# ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝
#
#                        Crafted by networkbm
# ================================================================
#!/usr/bin/env python3
"""
framediff — Compliance document diff tool.

Usage:
    framediff compare --framework fedramp --old old.docx --new new.docx
    framediff analyze --framework fedramp --file doc.docx
    framediff report --input diff.json --output markdown
    framediff version
    framediff frameworks
"""

import argparse
import sys
import os
from __init__ import load_document, supported_extensions
from control_parser import parse_controls, sections_to_map
from diff_engine import compute_diff
from helpers import load_framework, list_frameworks, resolve_framework
import terminal_report
import json_report
import markdown_report
import html_report

VERSION = "1.0.0"


def _load_and_parse(path: str, framework_map: dict, label: str):
    if not os.path.exists(path):
        print(f"Error: {label} file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        text = load_document(path)
    except Exception as e:
        print(f"Error loading {label} file: {e}", file=sys.stderr)
        sys.exit(1)
    sections = parse_controls(text, framework_map)
    return sections


def _write_output(content: str, output_file: str | None = None):
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Output written to: {output_file}")
    else:
        print(content)


def cmd_compare(args):
    framework_key = resolve_framework(args.framework)
    framework_map = load_framework(framework_key)

    if not framework_map:
        print(f"Warning: Framework '{args.framework}' not found or has no controls. "
              f"Available: {', '.join(list_frameworks())}", file=sys.stderr)

    old_sections = sections_to_map(
        _load_and_parse(args.old, framework_map, "old")
    )
    new_sections = sections_to_map(
        _load_and_parse(args.new, framework_map, "new")
    )

    result = compute_diff(
        old_sections,
        new_sections,
        framework=framework_key,
        old_doc=args.old,
        new_doc=args.new,
        detailed_descriptions=bool(getattr(args, "out_file", None)) and not args.quick_scan,
        quick_scan=args.quick_scan,
    )

    if args.ignore_formatting:
        result.changes = [c for c in result.changes if c.change_type != "narrative_changed"]

    if args.strict_controls and framework_map:
        known = set(framework_map.keys())
        result.changes = [c for c in result.changes if c.control_id in known]

    fmt = (args.output or "terminal").lower()

    if fmt == "terminal":
        output = terminal_report.render(result, verbose=getattr(args, "verbose", False))
    elif fmt == "json":
        output = json_report.render(result)
    elif fmt == "markdown":
        output = markdown_report.render(result, include_content=not args.quick_scan)
    elif fmt == "html":
        output = html_report.render(result, include_content=not args.quick_scan)
    else:
        print(f"Unknown output format '{fmt}'. Use: terminal, json, markdown, html", file=sys.stderr)
        sys.exit(1)

    _write_output(output, getattr(args, "out_file", None))


def cmd_analyze(args):
    """Analyze a single document and list detected controls."""
    framework_key = resolve_framework(args.framework)
    framework_map = load_framework(framework_key)

    sections = _load_and_parse(args.file, framework_map, "document")

    print(f"\n  Document: {args.file}")
    print(f"  Framework: {framework_key.upper()}")
    print(f"  Controls detected: {len(sections)}")
    print()
    print(f"  {'Control ID':<20} {'Title':<50} {'Content (chars)'}")
    print("  " + "─" * 80)
    for s in sections:
        title = (s.title or "—")[:48]
        print(f"  {s.control_id:<20} {title:<50} {len(s.content)}")
    print()


def cmd_report(args):
    """Re-render a saved JSON diff result."""
    import json as _json

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        data = _json.load(f)

    from control_models import DiffResult, DiffSummary, ControlChange
    s = data.get("summary", {})
    summary = DiffSummary(
        added=s.get("added", 0),
        removed=s.get("removed", 0),
        modified=s.get("modified", 0),
        expanded=s.get("expanded", 0),
        reduced=s.get("reduced", 0),
        unchanged=s.get("unchanged", 0),
    )
    changes = [
        ControlChange(
            control_id=c["control_id"],
            title=c.get("title", ""),
            change_type=c["change_type"],
            old_content=c.get("old_content"),
            new_content=c.get("new_content"),
            description=c.get("description", ""),
            impact=c.get("impact"),
        )
        for c in data.get("changes", [])
    ]
    result = DiffResult(
        framework=data.get("framework", "unknown"),
        old_doc=data.get("old_doc", ""),
        new_doc=data.get("new_doc", ""),
        summary=summary,
        changes=changes,
        generated_at=data.get("generated_at", ""),
    )

    fmt = (args.output or "terminal").lower()
    if fmt == "terminal":
        output = terminal_report.render(result)
    elif fmt == "markdown":
        output = markdown_report.render(result, include_content=not args.quick_scan)
    elif fmt == "html":
        output = html_report.render(result, include_content=not args.quick_scan)
    elif fmt == "json":
        output = json_report.render(result)
    else:
        print(f"Unknown output format '{fmt}'.", file=sys.stderr)
        sys.exit(1)

    _write_output(output, getattr(args, "out_file", None))


def cmd_version(_args):
    print(f"framediff {VERSION}")


def cmd_frameworks(_args):
    print("\n  Available frameworks:\n")
    for fw in sorted(list_frameworks()):
        fw_map = load_framework(fw)
        print(f"    {fw:<20} ({len(fw_map)} controls)")
    print()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="framediff",
        description="FrameDiff — Compliance document diff tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  framediff compare --framework fedramp --old SSP_v1.docx --new SSP_v2.docx
  framediff compare --framework nist80053 --old policy_v1.md --new policy_v2.md --output json
  framediff compare --framework fedramp --old old.docx --new new.docx --output html --file report.html
  framediff analyze --framework fedramp --file SSP.docx
  framediff report --input diff.json --output markdown
  framediff frameworks
        """
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p_compare = sub.add_parser("compare", help="Compare two compliance documents")
    p_compare.add_argument("--framework", "-f", required=True,
                           help="Framework context (fedramp, nist80053, cmmc, iso27001, soc2)")
    p_compare.add_argument("--old", required=True, metavar="PATH",
                           help="Path to the original document")
    p_compare.add_argument("--new", required=True, metavar="PATH",
                           help="Path to the updated document")
    p_compare.add_argument("--output", "-o", default="terminal",
                           choices=["terminal", "json", "markdown", "html"],
                           help="Output format (default: terminal)")
    p_compare.add_argument("--file", dest="out_file", metavar="PATH",
                           help="Write output to file instead of stdout")
    p_compare.add_argument("--strict-controls", action="store_true",
                           help="Only report changes for known framework control IDs")
    p_compare.add_argument("--ignore-formatting", action="store_true",
                           help="Suppress narrative/rewording-only changes")
    p_compare.add_argument("--verbose", "-v", action="store_true",
                           help="Show inline diffs for each change")
    p_compare.add_argument("--quick-scan", action="store_true",
                           help="Show concise quick-scan findings (protocol, tooling, config signals)")

    p_analyze = sub.add_parser("analyze", help="List control sections detected in a document")
    p_analyze.add_argument("--framework", "-f", required=True)
    p_analyze.add_argument("--file", required=True, metavar="PATH")

    p_report = sub.add_parser("report", help="Re-render a saved JSON diff result")
    p_report.add_argument("--input", "-i", required=True, metavar="PATH",
                          help="Path to a saved JSON diff result")
    p_report.add_argument("--output", "-o", default="terminal",
                          choices=["terminal", "json", "markdown", "html"])
    p_report.add_argument("--file", dest="out_file", metavar="PATH",
                          help="Write output to file")
    p_report.add_argument("--quick-scan", action="store_true",
                          help="Hide old/new content blocks in rendered reports")

    sub.add_parser("version", help="Show version")

    sub.add_parser("frameworks", help="List available frameworks")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "compare":    cmd_compare,
        "analyze":    cmd_analyze,
        "report":     cmd_report,
        "version":    cmd_version,
        "frameworks": cmd_frameworks,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()

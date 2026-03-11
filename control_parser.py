"""
control_parser.py — Parses plain text into ControlSection objects.

Detects:
  - Standard NIST/FedRAMP control IDs: AC-2, IA-5, SC-7 (4), AU-12 (4)
  - CMMC control IDs: AC.1.001, SC.3.177
  - ISO 27001 control IDs: A.9.2.1, A.13.1
  - SOC 2 control IDs: CC6.1, PI1.3
  - Numbered headings: 1.2.3 Title
  - Markdown headings: # Title, ## Title
  - ALL-CAPS section headers
"""

import re
import sys
from typing import List, Optional
from control_models import ControlSection


NIST_PATTERN = re.compile(
    r'^([A-Z]{2,3}-\d{1,3}(?:\(\d+\))?)'
    r'(?:[:\s\-–—]+(.*))?$',
    re.IGNORECASE
)

CMMC_PATTERN = re.compile(
    r'^([A-Z]{2,3}\.\d+\.\d{3})'
    r'(?:[:\s\-–—]+(.*))?$',
    re.IGNORECASE
)

ISO_PATTERN = re.compile(
    r'^(A\.\d{1,2}(?:\.\d{1,2}){0,2})'
    r'(?:[:\s\-–—]+(.*))?$',
    re.IGNORECASE
)

SOC2_PATTERN = re.compile(
    r'^([A-Z]{1,2}\d{1,2}\.\d{1,2})'
    r'(?:[:\s\-–—]+(.*))?$',
    re.IGNORECASE
)

MARKDOWN_HEADING = re.compile(r'^(#{1,6})\s+(.+)$')

NUMBERED_HEADING = re.compile(r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]+)$')

ALLCAPS_HEADING = re.compile(r'^([A-Z][A-Z0-9 :\-–]{3,})$')

ALL_CONTROL_PATTERNS = [NIST_PATTERN, CMMC_PATTERN, ISO_PATTERN, SOC2_PATTERN]


def _match_control_id(line: str) -> Optional[tuple]:
    """Return (control_id, title_remainder) or None."""
    line = line.strip()
    for pattern in ALL_CONTROL_PATTERNS:
        m = pattern.match(line)
        if m:
            cid = m.group(1).upper()
            title = (m.group(2) or "").strip()
            return cid, title
    return None


def _is_section_header(line: str) -> Optional[tuple]:
    """Returns (header_text, level) or None. Level 1 = top-level."""
    line = line.strip()
    if not line:
        return None

    m = MARKDOWN_HEADING.match(line)
    if m:
        level = len(m.group(1))
        return m.group(2).strip(), level

    m = NUMBERED_HEADING.match(line)
    if m:
        depth = len(m.group(1).split("."))
        return f"{m.group(1)} {m.group(2)}".strip(), depth

    m = ALLCAPS_HEADING.match(line)
    if m:
        return line, 1

    return None


def parse_controls(text: str, framework_map: dict = None) -> List[ControlSection]:
    """
    Parse text into a flat list of ControlSection objects.

    Strategy:
    1. Scan line-by-line for control ID patterns or section headers.
    2. Everything between two headers becomes the content of the first header.
    3. If no control IDs are found, fall back to section-header detection.
    """
    lines = text.splitlines()
    sections: List[ControlSection] = []

    current_id: Optional[str] = None
    current_title: str = ""
    current_lines: List[str] = []

    def flush():
        nonlocal current_id, current_title, current_lines
        if current_id:
            content = "\n".join(current_lines).strip()
            resolved_title = current_title
            if framework_map and current_id in framework_map and not resolved_title:
                resolved_title = framework_map[current_id]
            sections.append(ControlSection(
                control_id=current_id,
                title=resolved_title,
                content=content,
            ))
        current_id = None
        current_title = ""
        current_lines = []

    for raw_line in lines:
        line = raw_line.strip()

        match = _match_control_id(line)
        if match:
            flush()
            current_id, current_title = match
            if framework_map and current_id in framework_map and not current_title:
                current_title = framework_map[current_id]
            continue

        header = _is_section_header(line)
        if header:
            heading_text = header[0]
            inner_match = _match_control_id(heading_text)
            if inner_match:
                flush()
                current_id, current_title = inner_match
                if framework_map and current_id in framework_map and not current_title:
                    current_title = framework_map[current_id]
                continue
            else:
                flush()
                current_id = _slugify(heading_text)
                current_title = heading_text
                continue

        if current_id is not None:
            current_lines.append(raw_line)

    flush()

    if not sections:
        sections.append(ControlSection(
            control_id="DOCUMENT",
            title="Full Document",
            content=text.strip(),
        ))

    return sections


def _slugify(text: str) -> str:
    """Create a slug ID from arbitrary heading text."""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    parts = text.strip().split()[:4]
    return "-".join(p.upper() for p in parts)


def sections_to_map(sections: List[ControlSection]) -> dict:
    """Convert a list of sections to a dict keyed by control_id."""
    return {s.control_id: s for s in sections}

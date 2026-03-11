"""
json_report.py — Serializes a DiffResult to JSON.
"""

import json
from dataclasses import asdict
from control_models import DiffResult


def render(result: DiffResult, indent: int = 2) -> str:
    data = {
        "framework": result.framework,
        "old_doc": result.old_doc,
        "new_doc": result.new_doc,
        "generated_at": result.generated_at,
        "summary": {
            "modified": result.summary.modified,
            "added": result.summary.added,
            "removed": result.summary.removed,
            "expanded": result.summary.expanded,
            "reduced": result.summary.reduced,
            "unchanged": result.summary.unchanged,
            "total_changes": result.summary.total_changes,
        },
        "changes": [
            {
                "control_id": c.control_id,
                "title": c.title,
                "change_type": c.change_type,
                "description": c.description,
                "impact": c.impact,
                "old_content": c.old_content,
                "new_content": c.new_content,
            }
            for c in result.changes
        ],
    }
    return json.dumps(data, indent=indent, ensure_ascii=False)

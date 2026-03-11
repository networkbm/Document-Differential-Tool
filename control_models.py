from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ControlSection:
    control_id: str
    title: str
    content: str
    subsections: List["ControlSection"] = field(default_factory=list)
    source_doc: str = ""

    def __repr__(self):
        return f"ControlSection(id={self.control_id!r}, title={self.title!r}, content_len={len(self.content)})"


@dataclass
class ControlChange:
    control_id: str
    title: str
    change_type: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    description: str = ""
    impact: Optional[str] = None


@dataclass
class DiffSummary:
    added: int = 0
    removed: int = 0
    modified: int = 0
    expanded: int = 0
    reduced: int = 0
    unchanged: int = 0

    @property
    def total_changes(self):
        return self.added + self.removed + self.modified + self.expanded + self.reduced


@dataclass
class DiffResult:
    framework: str
    old_doc: str
    new_doc: str
    summary: DiffSummary = field(default_factory=DiffSummary)
    changes: List[ControlChange] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

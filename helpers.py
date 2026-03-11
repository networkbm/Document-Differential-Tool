import os
import json
import pathlib

_THIS_DIR = pathlib.Path(__file__).parent
_CANDIDATE_DIRS = [
    _THIS_DIR / "frameworks",
    _THIS_DIR,
]

FRAMEWORK_ALIASES = {
    "fedramp": "fedramp",
    "nist": "nist80053",
    "nist80053": "nist80053",
    "nist-800-53": "nist80053",
    "cmmc": "cmmc",
    "iso27001": "iso27001",
    "iso": "iso27001",
    "soc2": "soc2",
    "soc 2": "soc2",
}


def resolve_framework(name: str) -> str:
    """Normalize a framework name to its canonical key."""
    return FRAMEWORK_ALIASES.get(name.lower().replace(" ", ""), name.lower())


def load_framework(name: str) -> dict:
    """Load a framework control map from JSON. Returns empty dict if not found."""
    key = resolve_framework(name)
    for framework_dir in _CANDIDATE_DIRS:
        path = framework_dir / f"{key}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


def list_frameworks() -> list:
    names = set()
    for framework_dir in _CANDIDATE_DIRS:
        if framework_dir.exists():
            names.update(p.stem for p in framework_dir.glob("*.json"))
    return sorted(names)


def clamp(text: str, max_len: int = 120) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def similarity_ratio(a: str, b: str) -> float:
    """Quick character-level similarity using difflib."""
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()

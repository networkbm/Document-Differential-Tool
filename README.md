# FrameDiff

**Compliance document differential tool — framework aware comparison for FedRAMP, NIST 800-53, CMMC, ISO 27001, and SOC 2.**

**Privacy first:** Runs entirely locally

---

## Project Status: Work in Progress

**FrameDiff is currently under active development**

## Features

- **Framework-aware** — understands FedRAMP, NIST 800-53, CMMC, ISO 27001, SOC 2 control IDs
- **Multi-format** — DOCX, Markdown, TXT, JSON, YAML, CSV, PDF
- **Smart change classification** — Added, Removed, Modified, Expanded, Reduced, Rewording
- **Impact analysis** — flags security-strengthening and security weakening changes
- **Multiple output formats** — terminal, JSON, Markdown, HTML
- **No cloud** — 100% local processing

---

## Test it with the bottom cmmand:

```bash
python3 framediff.py compare --framework fedramp --old test_old.md --new test_new.md
```
```bash
# Quick-Scan
python3 framediff.py compare --framework fedramp --old old.md --new new.md --quick-scan

```

**Dependencies:**
- Python 3.11+
- `python-docx` (for DOCX files)
- `PyYAML` (for YAML files)
- Optional: `pypdf` (for PDF files)

---

### Save as JSON for FULL report

```bash
python3 framediff.py compare --framework nist80053 --old policy_v1.md --new policy_v2.md --output json --file diff_result.json
```

### Generate an HTML report for FULL report

```bash
python3 framediff.py compare --framework fedramp --old SSP_v1.docx --new SSP_v2.docx --output html --file report.html
```
---

## Supported Frameworks

| Framework | Controls |
|-----------|----------|
| FedRAMP | 160 |
| NIST SP 800-53 | 253 |
| CMMC | 98 |
| ISO 27001 | 149 |
| SOC 2 | 61 |

---

## Supported File Formats

| Format | Extensions |
|--------|-----------|
| Word Document | `.docx` |
| Markdown | `.md` |
| Plain Text | `.txt` |
| JSON | `.json` |
| YAML | `.yaml`, `.yml` |
| CSV | `.csv` |
| PDF (text-based) | `.pdf` |

---

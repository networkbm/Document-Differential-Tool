# FrameDiff

**Compliance document diff tool — framework aware comparison for FedRAMP, NIST 800-53, CMMC, ISO 27001, and SOC 2.**

**Privacy first:** Runs entirely locally

---

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

**Dependencies:**
- Python 3.11+
- `python-docx` (for DOCX files)
- `PyYAML` (for YAML files)
- Optional: `pypdf` (for PDF files)

---

### Save as JSON

```bash
python3 framediff compare --framework nist80053 --old policy_v1.md --new policy_v2.md --output json --file diff_result.json
```

### Generate an HTML report

```bash
python3 framediff compare --framework fedramp --old SSP_v1.docx --new SSP_v2.docx --output html --file report.html
```

### Inspect detected controls in a document

```bash
python3 framediff.py analyze --framework fedramp --file SSP.docx
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
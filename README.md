# FrameDiff

**Compliance document diff tool — framework aware comparison for FedRAMP, NIST 800-53, CMMC, ISO 27001, and SOC 2.**

> 🔒 **Privacy first:** Runs entirely locally

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

## Quick Start

### Compare two SSP versions

```bash
framediff compare \
  --framework fedramp \
  --old SSP_v1.docx \
  --new SSP_v2.docx
```

### Save as JSON

```bash
framediff compare \
  --framework nist80053 \
  --old policy_v1.md \
  --new policy_v2.md \
  --output json \
  --file diff_result.json
```

### Generate an HTML report

```bash
framediff compare \
  --framework fedramp \
  --old SSP_v1.docx \
  --new SSP_v2.docx \
  --output html \
  --file report.html
```

### Inspect detected controls in a document

```bash
framediff analyze --framework fedramp --file SSP.docx
```

---

## Commands

| Command | Description |
|---------|-------------|
| `framediff compare` | Compare two compliance documents |
| `framediff analyze` | List detected controls in a document |
| `framediff report` | Re-render a saved JSON diff result |
| `framediff frameworks` | List available frameworks |
| `framediff version` | Show version |

---

## Options (`compare`)

| Option | Description |
|--------|-------------|
| `--framework` | Framework context: `fedramp`, `nist80053`, `cmmc`, `iso27001`, `soc2` |
| `--old PATH` | Path to the original document |
| `--new PATH` | Path to the updated document |
| `--output FORMAT` | Output format: `terminal` (default), `json`, `markdown`, `html` |
| `--file PATH` | Write output to a file instead of stdout |
| `--strict-controls` | Only report changes for known framework control IDs |
| `--ignore-formatting` | Suppress rewording-only changes |
| `--verbose` | Show inline diffs for each change |

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
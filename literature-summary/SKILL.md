---
name: literature-summary
description: "Zotero literature summary automation: prepare paper artifacts from Zotero, read the paper, fill a structured Chinese summary template, export to Word (DOCX), and optionally upload to Feishu/Lark. Use when the user asks to summarize a paper, generate a literature review, or process a Zotero reference."
---

# Literature Summary Automation

> From Zotero PDF to structured Chinese literature summary, Word export, and optional Feishu upload.

## When to Use

- User asks to summarize a paper / literature from Zotero
- User mentions "literature summary", "paper summary", or "文献总结"
- User wants to export a paper summary to Word
- User wants to upload a paper summary to Feishu

## Tool Location

All scripts and templates live inside this skill directory:

```
SKILL_DIR = ~/.claude/skills/literature-summary\tool
```

Scripts are in `SKILL_DIR\scripts\`, templates in `SKILL_DIR\templates\`.

## Prerequisites

Before first use, ensure the user has:

1. **Python 3.10+** with packages: `python-docx`, `requests`
2. **Poppler** installed and on PATH (`pdftotext`, `pdftoppm`)
3. **Zotero** with a local data directory containing `zotero.sqlite` and `storage/`
4. **Configuration file** at `SKILL_DIR\.env.local` (see Configuration section)

Run the config self-check first:

```powershell
python "SKILL_DIR\scripts\config_doctor.py"
```

If the user wants Feishu upload, also run:

```powershell
python "SKILL_DIR\scripts\config_doctor.py" --test-feishu
```

## Configuration (.env.local)

The `.env.local` file must be created at `SKILL_DIR\.env.local`. It contains:

```text
ZOTERO_DATA_DIR=<path to Zotero data directory>
SUMMARY_OUT_ROOT=<path to output directory for summaries>

FEISHU_APP_ID=<Feishu app ID>
FEISHU_APP_SECRET=<Feishu app secret>
FEISHU_PARENT_NODE=<Feishu folder token>
FEISHU_PARENT_TYPE=explorer
```

**Security rule**: Never display, echo, or log `FEISHU_APP_SECRET` values. Never write API keys or private paths into generated summaries, READMEs, or chat messages.

## Workflow

### Step 1: Configuration Check

Run `config_doctor.py` to verify the setup. Fix any missing items before proceeding.

```powershell
python "SKILL_DIR\scripts\config_doctor.py"
```

### Step 2: Prepare Paper Artifacts

Given a paper title, DOI, or Zotero item key, run the preparation script:

```powershell
python "SKILL_DIR\scripts\run_literature_summary.py" --query "<paper title or DOI>" --zotero-dir "<ZOTERO_DATA_DIR>" --out-root "<SUMMARY_OUT_ROOT>"
```

This will:
- Find the Zotero item by title/DOI/key
- Locate the local PDF attachment
- Extract text from PDF (`zotero_pdf_text.txt`)
- Render PDF pages as PNG screenshots (`pdf_pages/`)
- Create output directory with `paper_metadata.json`
- Generate `summary.md` from the template (with fields pre-filled from Zotero metadata)
- Generate `codex_task.md` with instructions for the AI agent

Optionally, check attachments first:

```powershell
python "SKILL_DIR\scripts\check_zotero_attachments.py" --query "<paper title>" --zotero-dir "<ZOTERO_DATA_DIR>"
```

### Step 3: Read the Paper and Fill the Summary

This is the core AI step. Read the following files from the output directory:

1. `paper_metadata.json` - metadata from Zotero (title, DOI, authors, journal, etc.)
2. `zotero_pdf_text.txt` - full extracted text from the PDF
3. `pdf_pages/` - page-by-page PNG screenshots (useful for figures and tables)

Then fill in `summary.md` following the template structure. Every `{placeholder}` field must be replaced with actual content. The template sections are:

#### Summary Template Sections

| Section | What to Write |
|---|---|
| **选文结论** | Why this paper is high-quality and worth reading |
| **基本信息表** | Fill all metadata fields from `paper_metadata.json` and PDF content |
| **实验方法** | 4 key methods/approaches from the paper |
| **值得学习的图截图** | Pick 2 best figures (method diagrams, system architecture, experimental results, ablation tables). Copy them from `pdf_pages/` to `figures/`, crop if needed. Images MUST come from the local Zotero PDF, not web thumbnails. |
| **创新点** | 4 key innovations/contributions |
| **可改进方向** | Limitations or areas for improvement |
| **可借鉴写法** | Notable writing patterns for introduction, methods, experiments, and figures/tables |
| **资料来源** | Auto-filled paths to DOI, PDF, extracted text, screenshots |

**Rules for filling the template:**

- Title must include today's date in format `YYYY年MM月DD日`
- Do NOT list references individually; summarize reference count, types, year span, or citation patterns
- Do NOT write any API keys, App Secrets, internal URLs, or private paths
- For the info table: query CrossRef or Semantic Scholar if needed for impact factor, keywords, etc.
- For figures: prioritize method framework diagrams, system architecture, experimental results, deployment figures, parameter tables, or ablation tables
- Write everything in Chinese except for the English title and technical terms

### Step 4: Export to Word

After `summary.md` is complete, export to DOCX:

```powershell
python "SKILL_DIR\scripts\summary_md_to_docx.py" --summary "<output_dir>\summary.md" --output "<output_dir>\<folder_name>_文献总结_YYYYMMDD.docx"
```

The DOCX export handles:
- Chinese fonts (宋体 for body, 微软雅黑 for headings)
- Markdown tables with colored headers
- Embedded images from relative/absolute paths
- Numbered and bulleted lists
- Headings hierarchy

### Step 5: Upload to Feishu (Optional)

Only if the user explicitly requests Feishu upload and `.env.local` has Feishu credentials:

```powershell
python "SKILL_DIR\scripts\upload_to_feishu.py" --file "<docx_path>"
```

## Attachment Repair

If PDF attachments are missing or broken:

```powershell
# Check all attachments
python "SKILL_DIR\scripts\check_zotero_attachments.py" --all --zotero-dir "<ZOTERO_DATA_DIR>"

# Repair with local copies
python "SKILL_DIR\scripts\check_zotero_attachments.py" --all --repair --zotero-dir "<ZOTERO_DATA_DIR>"

# Also try downloading from DOI
python "SKILL_DIR\scripts\check_zotero_attachments.py" --all --repair --download --zotero-dir "<ZOTERO_DATA_DIR>"
```

Reports are saved to `SKILL_DIR\tool\reports\`.

## Troubleshooting

| Problem | Solution |
|---|---|
| `pdftotext not found` | Install Poppler, add `bin` to PATH |
| `Cannot find Zotero database` | Check `ZOTERO_DATA_DIR` in `.env.local` |
| `no local PDF attachment found` | Verify PDF exists in Zotero and can be double-clicked |
| `ModuleNotFoundError: docx` | Run `python -m pip install python-docx` |
| Feishu upload fails | Run `config_doctor.py --test-feishu`; check `FEISHU_PARENT_NODE` is folder token, not full URL |
| App Secret exposed | Immediately reset on Feishu Open Platform, then update `.env.local` |

## Security Reminders

- Never include App Secret, tenant tokens, or full Feishu folder URLs in summaries
- Never copy `.env.local` when sharing the tool
- Only show whether Feishu credentials exist, never their values
- If secrets may have been exposed in logs or screenshots, reset them immediately

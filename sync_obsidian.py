"""Sync CLAUDE.md from the Obsidian AMS-KB-Setup.md file."""

import re
from datetime import date
from pathlib import Path

OBSIDIAN_FILE = Path(
    r"C:\Users\Krit\OneDrive - iamconsulting.co.th\99 AI Document\Obsidian\I AM AMS KB\AMS-KB-Setup.md"
)
CLAUDE_MD = Path(__file__).parent / "CLAUDE.md"


def extract_section(text: str, heading: str) -> str:
    pattern = rf"(## {re.escape(heading)}.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def find_current_step(progress_block: str) -> str:
    lines = progress_block.splitlines()
    for line in lines:
        if line.startswith("- [ ]"):
            m = re.search(r"(Step \d+[^)]*)", line)
            if m:
                return m.group(1).strip()
    return "Unknown"


def build_claude_md(obs_text: str) -> str:
    today = date.today().isoformat()

    progress_section = extract_section(obs_text, "✅ Progress Tracker")
    progress_lines = "\n".join(
        line for line in progress_section.splitlines() if line.startswith("- ")
    )

    current_step_name = find_current_step(progress_lines)

    # find and mark current step in progress list
    marked_progress = []
    first_incomplete = True
    for line in progress_lines.splitlines():
        if line.startswith("- [ ]") and first_incomplete:
            marked_progress.append(line + " ← CURRENT")
            first_incomplete = False
        else:
            marked_progress.append(line)
    progress_md = "\n".join(marked_progress)

    # extract step number for current step detail section
    step_num_match = re.search(r"Step (\d+)", current_step_name)
    current_step_detail = ""
    if step_num_match:
        step_num = step_num_match.group(1)
        # find matching step section in obsidian file
        pattern = rf"(## 📦 Step {step_num}.*?)(?=\n## |\Z)"
        m = re.search(pattern, obs_text, re.DOTALL)
        if m:
            current_step_detail = m.group(1).strip()

    step5_sql_section = extract_section(obs_text, "📦 Step 5 — Supabase Setup")
    sql_match = re.search(r"```sql(.*?)```", step5_sql_section, re.DOTALL)
    sql_block = f"```sql{sql_match.group(1)}```" if sql_match else ""

    error_section = extract_section(obs_text, "🐛 Error Log")
    error_table = "\n".join(
        line for line in error_section.splitlines() if line.startswith("|")
    )

    return f"""# IAM-KB Project — Claude Code Context

> **Auto-synced from:** `{OBSIDIAN_FILE}`
> **Last sync:** {today}

---

## Project Goal

RAG-based Knowledge Base for I AM Consulting AMS team using OpenAI API + Supabase (pgvector).

**Stack:** OpenAI API (gpt-4o + text-embedding-3-small) → Python → Supabase (pgvector) → FastAPI → React
**OS:** Windows 11

---

## Critical Windows Notes

- **Always use `py` instead of `python`** on this machine (Python launcher)
- Python version: 3.13.13
- Node.js version: v24.14.1
- Claude Code version: 2.1.121

---

## Progress Tracker

{progress_md}

---

## Current Step: {current_step_name}

{current_step_detail}

---

## Step 5 Reference — Supabase SQL

{sql_block}

Supabase region: Southeast Asia (Singapore)
Settings → API → save Project URL and Anon Key to password manager.

---

## Data Directory

```
C:\\iam-kb\\data\\    ← all raw data files go here
```

---

## Error Log

{error_table}
"""


def main():
    if not OBSIDIAN_FILE.exists():
        print(f"ERROR: Obsidian file not found: {OBSIDIAN_FILE}")
        return 1

    obs_text = OBSIDIAN_FILE.read_text(encoding="utf-8")
    content = build_claude_md(obs_text)
    CLAUDE_MD.write_text(content, encoding="utf-8")
    print(f"Synced CLAUDE.md from Obsidian ({date.today()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

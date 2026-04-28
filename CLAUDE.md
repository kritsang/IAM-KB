# IAM-KB Project — Claude Code Context

> **Auto-synced from:** `C:\Users\Krit\OneDrive - iamconsulting.co.th\99 AI Document\Obsidian\I AM AMS KB\AMS-KB-Setup.md`
> **Last sync:** 2026-04-28

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

- [x] Step 1 — ติดตั้ง Node.js
- [x] Step 2 — ติดตั้ง Claude Code
- [x] Step 3 — ติดตั้ง Python
- [x] Step 4 — ติดตั้ง VS Code
- [x] Step 5 — สร้าง Supabase project + pgvector
- [x] Step 6 — เตรียม data (ServiceNow export + docs)
- [x] Step 7 — สร้าง project folder + virtual environment
- [x] Step 8 — เขียน ingestion script ด้วย Claude Code
- [x] Step 9 — ทดสอบ RAG query
- [x] Step 10 — สร้าง FastAPI backend
- [x] Step 11 — สร้าง React UI
- [ ] Step 12 — Deploy (Vercel + Railway) ← CURRENT

---

## Current Step: Step 12 — Deploy (Vercel + Railway

## 📦 Step 12 — Deploy

**สถานะ:** 🔲 รอ Step 11 เสร็จก่อน

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | - |
| Backend | Railway | - |

---

---

## Step 5 Reference — Supabase SQL

```sql
create extension if not exists vector;

create table documents (
  id uuid primary key default gen_random_uuid(),
  content text,
  embedding vector(1536),
  metadata jsonb
);

create index on documents
using ivfflat (embedding vector_cosine_ops);
```

Supabase region: Southeast Asia (Singapore)
Settings → API → save Project URL and Anon Key to password manager.

---

## Data Directory

```
C:\iam-kb\data\    ← all raw data files go here
```

---

## Error Log

| วันที่ | Step | Error | วิธีแก้ |
|--------|------|-------|---------|
| - | Step 3 | `python` not found | ใช้ `py` แทนบน Windows |
| 2026-04-28 | Step 7 | `py` ไม่อยู่ใน PATH ใน PowerShell/bash | ใช้ full path `C:\Users\Krit\AppData\Local\Programs\Python\Python313\python.exe` |
| 2026-04-28 | Step 8 | Supabase RLS blocked insert | ใช้ SUPABASE_SERVICE_KEY แทน anon key |
| 2026-04-28 | Step 8 | SUPABASE_URL มี `/rest/v1/` ต่อท้าย | ใช้แค่ base URL เช่น `https://xxx.supabase.co` |
| 2026-04-28 | Step 9 | Supabase SQL Editor รัน filename แทน SQL | Copy-paste เฉพาะ SQL content ไม่ใช่ชื่อไฟล์ |
| 2026-04-28 | Step 9 | `curl` ใน PowerShell ใช้ไม่ได้กับ JSON | ใช้ `Invoke-RestMethod` หรือ `Invoke-WebRequest` แทน |
| 2026-04-28 | Step 9 | ANTHROPIC_API_KEY ไม่มีใน .env | เปลี่ยนมาใช้ OpenAI API แทน Claude (ไม่ต้องใช้ Anthropic key) |

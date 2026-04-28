import os
import json
import pandas as pd
import pdfplumber
from docx import Document
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

EMBED_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


# ── text chunking ──────────────────────────────────────────────────────────────

def chunk_text(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= CHUNK_SIZE:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── file readers ───────────────────────────────────────────────────────────────

def load_xlsx(path: str, ticket_type: str) -> list[dict]:
    df = pd.read_excel(path)
    df = df.fillna("")
    records = []
    for _, row in df.iterrows():
        text_parts = []
        for col in ["Title", "Module", "Root Cause", "Close notes"]:
            if col in row and str(row[col]).strip():
                text_parts.append(f"{col}: {row[col]}")
        text = "\n".join(text_parts)
        if not text.strip():
            continue
        records.append({
            "text": text,
            "metadata": {
                "source": os.path.basename(path),
                "type": ticket_type,
                "number": str(row.get("Number", "")),
                "priority": str(row.get("Priority", "")),
                "company": str(row.get("Company", "")),
                "state": str(row.get("State", "")),
            },
        })
    return records


def load_pdf(path: str) -> list[dict]:
    records = []
    with pdfplumber.open(path) as pdf:
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
    for chunk in chunk_text(full_text):
        records.append({
            "text": chunk,
            "metadata": {"source": os.path.basename(path), "type": "solution_doc"},
        })
    return records


def load_docx(path: str) -> list[dict]:
    doc = Document(path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    records = []
    for chunk in chunk_text(full_text):
        records.append({
            "text": chunk,
            "metadata": {"source": os.path.basename(path), "type": "solution_doc"},
        })
    return records


# ── embedding + upsert ─────────────────────────────────────────────────────────

def embed_batch(texts: list[str]) -> list[list[float]]:
    response = openai.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


def upsert_records(records: list[dict]) -> None:
    BATCH = 100
    for i in range(0, len(records), BATCH):
        batch = records[i : i + BATCH]
        texts = [r["text"] for r in batch]
        embeddings = embed_batch(texts)
        rows = [
            {
                "content": r["text"],
                "embedding": emb,
                "metadata": r["metadata"],
            }
            for r, emb in zip(batch, embeddings)
        ]
        supabase.table("documents").insert(rows).execute()
        print(f"  inserted {i + len(batch)} / {len(records)}")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    all_records: list[dict] = []

    # XLSX tickets
    xlsx_files = {
        "incident.xlsx": "incident",
        "change_request.xlsx": "change_request",
        "sc_request.xlsx": "sc_request",
    }
    for filename, ticket_type in xlsx_files.items():
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            recs = load_xlsx(path, ticket_type)
            print(f"[xlsx] {filename}: {len(recs)} records")
            all_records.extend(recs)

    # Solution docs
    solution_dir = os.path.join(DATA_DIR, "Solution Doc")
    if os.path.isdir(solution_dir):
        for fname in os.listdir(solution_dir):
            fpath = os.path.join(solution_dir, fname)
            if fname.lower().endswith(".pdf"):
                recs = load_pdf(fpath)
                print(f"[pdf]  {fname}: {len(recs)} chunks")
                all_records.extend(recs)
            elif fname.lower().endswith(".docx"):
                recs = load_docx(fpath)
                print(f"[docx] {fname}: {len(recs)} chunks")
                all_records.extend(recs)

    print(f"\nTotal: {len(all_records)} chunks — embedding & uploading...")
    upsert_records(all_records)
    print("Done.")


if __name__ == "__main__":
    main()

import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
TOP_K = 5
SIMILARITY_THRESHOLD = 0.3


def embed_query(text: str) -> list[float]:
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def search_documents(query_embedding: list[float]) -> list[dict]:
    result = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": TOP_K,
            "match_threshold": SIMILARITY_THRESHOLD,
        },
    ).execute()
    return result.data or []


def build_context(docs: list[dict]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        source = meta.get("source", "unknown")
        doc_type = meta.get("type", "")
        header = f"[{i}] Source: {source}"
        if doc_type:
            header += f" | Type: {doc_type}"
        if meta.get("number"):
            header += f" | Ticket: {meta['number']}"
        parts.append(f"{header}\n{doc['content']}")
    return "\n\n---\n\n".join(parts)


def format_sources(docs: list[dict]) -> list[dict]:
    sources = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        sources.append({
            "index": i,
            "source": meta.get("source", "unknown"),
            "type": meta.get("type", ""),
            "ticket": meta.get("number", ""),
            "similarity": round(doc.get("similarity", 0), 3),
        })
    return sources


SYSTEM_PROMPT = (
    "You are a helpful assistant for the I AM Consulting AMS (Application Managed Services) team. "
    "Answer questions based on the provided knowledge base excerpts. "
    "If the answer is not in the context, say so clearly. "
    "Cite the source numbers (e.g. [1], [2]) when referencing specific documents. "
    "Respond in the same language as the question (Thai or English)."
)


def stream_answer(question: str, context: str):
    """Yields text chunks from OpenAI streaming chat completion."""
    stream = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context from the knowledge base:\n\n{context}\n\n---\n\nQuestion: {question}"},
        ],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

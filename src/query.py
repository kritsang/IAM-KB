import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag import embed_query, search_documents, build_context, format_sources, stream_answer


def rag_query(question: str) -> None:
    print("\nSearching knowledge base...", flush=True)
    embedding = embed_query(question)
    docs = search_documents(embedding)

    if not docs:
        print("No relevant documents found. Try rephrasing your question.")
        return

    print(f"Found {len(docs)} relevant document(s). Generating answer...\n")
    context = build_context(docs)

    for token in stream_answer(question, context):
        print(token, end="", flush=True)
    print()

    print("\n--- Sources ---")
    for s in format_sources(docs):
        print(f"[{s['index']}] {s['source']} (similarity: {s['similarity']})")


def main() -> None:
    print("IAM-KB RAG Query — type 'quit' to exit\n")
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        rag_query(question)
        print()


if __name__ == "__main__":
    main()

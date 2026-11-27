"""RAG: chunk the IT docs, embed them, store in Chroma, search them.
Run: python -m app.rag  -> builds/updates the index and runs a test search."""
import hashlib
from pathlib import Path

import chromadb

from app.llm import embed

DOCS_DIR = Path(__file__).parent.parent / "data" / "docs"
CHROMA_DIR = Path(__file__).parent.parent / "chroma"  # vectors saved on disk (git-ignored)
MAX_WORDS = 300  # long sections are split, so each chunk stays about one topic
OVERLAP = 50     # repeat last 50 words in the next part, so no sentence is lost at a cut


def split_long(text: str) -> list[str]:
    """Split text into parts of max MAX_WORDS words, with OVERLAP words overlap."""
    words = text.split()
    if len(words) <= MAX_WORDS:
        return [text]
    step = MAX_WORDS - OVERLAP
    return [" ".join(words[i:i + MAX_WORDS]) for i in range(0, len(words) - OVERLAP, step)]


def chunk_markdown(path: Path) -> list[dict]:
    """Split one markdown file into chunks, one per '## ' section.
    Each chunk keeps the doc title, so it still makes sense alone."""
    title, chunks, section, lines = path.stem, [], "Intro", []

    def save():
        text = "\n".join(lines).strip()
        if not text:
            return
        parts = split_long(text)
        for n, part in enumerate(parts, start=1):
            suffix = f" (part {n})" if len(parts) > 1 else ""
            chunks.append({
                "id": f"{path.name}#{section}{suffix}",  # unique id, also our citation
                "source": path.name,
                "text": f"{title} > {section}{suffix}\n{part}",  # title prefix on every part
            })

    for line in path.read_text().splitlines():
        if line.startswith("# "):            # doc title
            title = line[2:].strip()
        elif line.startswith("## "):         # new section -> save the previous one
            save()
            section, lines = line[3:].strip(), []
        else:
            lines.append(line)
    save()
    return chunks


def load_all_chunks() -> list[dict]:
    return [c for p in sorted(DOCS_DIR.glob("*.md")) for c in chunk_markdown(p)]


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection("it_docs", metadata={"hnsw:space": "cosine"})


def fingerprint(text: str) -> str:
    """Short hash of the text: same text -> same hash. Used to skip unchanged chunks."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def build_index() -> None:
    """Embed only new/changed chunks, delete removed ones. Saves API calls."""
    col = get_collection()
    chunks = load_all_chunks()
    stored = col.get(include=["metadatas"])
    old = {i: m["hash"] for i, m in zip(stored["ids"], stored["metadatas"])}

    todo = [c for c in chunks if old.get(c["id"]) != fingerprint(c["text"])]
    removed = set(old) - {c["id"] for c in chunks}
    if removed:
        col.delete(ids=list(removed))
    if todo:
        col.upsert(
            ids=[c["id"] for c in todo],
            documents=[c["text"] for c in todo],
            embeddings=embed([c["text"] for c in todo]),
            metadatas=[{"source": c["source"], "hash": fingerprint(c["text"])} for c in todo],
        )
    print(f"Index: {len(chunks)} chunks, embedded {len(todo)}, removed {len(removed)}")


def search(question: str, k: int = 3) -> list[dict]:
    """Return the k chunks closest in meaning to the question."""
    q = embed([question], task="RETRIEVAL_QUERY")[0]
    res = get_collection().query(query_embeddings=[q], n_results=k)
    return [
        {"id": i, "text": t, "similarity": round(1 - d, 3)}  # Chroma gives distance = 1 - cosine
        for i, t, d in zip(res["ids"][0], res["documents"][0], res["distances"][0])
    ]


if __name__ == "__main__":
    build_index()
    for q in ["I can't reach the file server from home", "how many wrong passwords until lockout?"]:
        print(f"\nQ: {q}")
        for hit in search(q):
            print(f"  {hit['similarity']}  {hit['id']}")

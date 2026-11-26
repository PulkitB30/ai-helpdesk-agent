"""RAG: chunk the IT docs, embed them, store in Chroma, search them.
Step 2 (this part): chunking."""
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "data" / "docs"
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


if __name__ == "__main__":
    chunks = load_all_chunks()
    print(f"{len(chunks)} chunks\n")
    for c in chunks:
        print(f"{c['id']:45} {len(c['text'].split()):4} words")
    print("\nExample chunk:\n" + chunks[-3]["text"])

"""RAG: chunk the IT docs, embed them, store in Chroma, search them.
Step 2 (this part): chunking."""
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "data" / "docs"


def chunk_markdown(path: Path) -> list[dict]:
    """Split one markdown file into chunks, one per '## ' section.
    Each chunk keeps the doc title, so it still makes sense alone."""
    title, chunks, section, lines = path.stem, [], "Intro", []

    def save():
        text = "\n".join(lines).strip()
        if text:
            chunks.append({
                "id": f"{path.name}#{section}",       # unique id, also our citation
                "source": path.name,
                "text": f"{title} > {section}\n{text}",
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

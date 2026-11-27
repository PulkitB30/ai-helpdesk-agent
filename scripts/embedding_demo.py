"""Run: python -m scripts.embedding_demo -> shows that similar meaning = similar vectors."""
import math
from app.llm import embed


def cosine(a, b):
    """Cosine similarity: 1.0 = same meaning direction, ~0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


question = "I can't reach the file server from home"
texts = [
    "VPN setup: install FortiClient and connect to vpn.example.com",
    "Paper jam: open front door A and remove the paper",
    "Mailbox size is 50 GB",
]
q = embed([question], task="RETRIEVAL_QUERY")[0]
docs = embed(texts)
print(f"Vector length: {len(q)} numbers. First 5: {[round(x, 3) for x in q[:5]]}\n")
print(f"Question: {question}")
for text, d in sorted(zip(texts, docs), key=lambda p: -cosine(q, p[1])):
    print(f"  {cosine(q, d):.3f}  {text}")

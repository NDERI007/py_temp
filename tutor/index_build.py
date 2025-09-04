# index_build.py
import json
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pathlib import Path
import re

# ------------------------------
# Config
# ------------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 80   # smaller chunks since HTML docs are short
OVERLAP = 20

MODEL = SentenceTransformer(EMBED_MODEL)


# ------------------------------
# Helpers
# ------------------------------
def clean_text(text: str) -> str:
    """Basic cleanup: collapse whitespace and strip."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split text into overlapping chunks of words."""
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = " ".join(tokens[i:i + chunk_size])
        chunks.append(clean_text(chunk))
        if i + chunk_size >= len(tokens):
            break
        i += chunk_size - overlap
    return chunks


# ------------------------------
# Build index
# ------------------------------
def main():
    docs_path = Path("docs.json")
    if not docs_path.exists():
        raise FileNotFoundError("docs.json not found! Place your knowledge base first.")

    docs = json.load(open(docs_path, "r", encoding="utf-8"))

    texts = []
    meta = []

    for d in docs:
        doc_id = d.get("id") or len(meta)
        title = d.get("title", "")

        if "sections" in d:
            # structured doc
            for sec in d["sections"]:
                heading = sec.get("heading", "")

                # ✅ 1. Index normal text (priority source for hints)
                if "text" in sec and sec["text"].strip():
                    for idx, ch in enumerate(chunk_text(sec["text"])):
                        texts.append(ch)
                        meta.append({
                            "doc_id": doc_id,
                            "title": title,
                            "heading": heading,
                            "chunk_id": idx,
                            "type": "text"   # 👈 tag it as explanation
                        })

                # ✅ 2. Index code separately (retrievable but not prioritized for hint generation)
                if "code" in sec and sec["code"].strip():
                    texts.append(sec["code"])
                    meta.append({
                        "doc_id": doc_id,
                        "title": title,
                        "heading": heading,
                        "chunk_id": 0,
                        "type": "code"   # 👈 tag it as code
                    })

        else:
            # flat doc fallback
            for idx, ch in enumerate(chunk_text(d.get("text", ""))):
                texts.append(ch)
                meta.append({
                    "doc_id": doc_id,
                    "title": title,
                    "chunk_id": idx,
                    "type": "text"
                })

    print(f"📄 Total documents: {len(docs)}")
    print(f"✂️  Total chunks: {len(texts)}")

    # Compute embeddings
    embeddings = MODEL.encode(
        texts, 
        show_progress_bar=True, 
        convert_to_numpy=True, 
        normalize_embeddings=True
    )

    # Build FAISS index (cosine sim)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, "rag_index.faiss")
    with open("rag_meta.pkl", "wb") as f:
        pickle.dump({"texts": texts, "meta": meta}, f)

    print("✅ Index and metadata saved: rag_index.faiss, rag_meta.pkl")


if __name__ == "__main__":
    main()

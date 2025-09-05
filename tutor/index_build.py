import json, pickle, re, hashlib
from pathlib import Path
from typing import List
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

EMBED_MODEL = "all-MiniLM-L6-v2"
MODEL = SentenceTransformer(EMBED_MODEL)
TOKENIZER = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()

def split_by_sentences(text: str) -> list[str]:
    return [p for p in re.split(r'(?<=[.!?])\s+', text.strip()) if p]

def token_len(s: str) -> int:
    return len(TOKENIZER.encode(s, add_special_tokens=False))

def chunk_semantic(text: str, tok_limit=384, tok_overlap=64) -> list[str]:
    sents = split_by_sentences(text)
    chunks, buf, buf_len = [], [], 0
    for s in sents:
        sl = token_len(s)
        if sl > tok_limit:
            words = s.split()
            for i in range(0, len(words), 80):
                chunks.append(" ".join(words[i:i+80]))
            continue
        if buf_len + sl <= tok_limit:
            buf.append(s); buf_len += sl
        else:
            chunks.append(" ".join(buf))
            while buf and buf_len > tok_overlap:
                popped = buf.pop(0); buf_len -= token_len(popped)
            buf.append(s); buf_len += sl
    if buf: chunks.append(" ".join(buf))
    return [clean_text(c) for c in chunks if c.strip()]

def section_id(title:str, heading:str) -> str:
    return hashlib.sha1(f"{title}::{heading}".encode()).hexdigest()[:16]

def main():
    docs_path = Path("docs.json")
    docs = json.loads(docs_path.read_text(encoding="utf-8"))

    texts: List[str] = []
    meta: List[dict] = []
    parents: dict[str, str] = {}  # parent_id -> parent_text

    for d in docs:
        doc_id = d.get("id", 0)
        title = d.get("title", "")
        if "sections" in d:
            for sec in enumerate(d["sections"]):
                heading = sec.get("heading", "")
                pid = section_id(title, heading)

                # Combine title/heading into the parent (improves recall)
                parent_text = clean_text(f"{title} — {heading}. {sec.get('text','')}")
                if parent_text:
                    parents[pid] = parent_text

                # TEXT children
                if sec.get("text", "").strip():
                    for c_idx, ch in enumerate(chunk_semantic(sec["text"])):
                        texts.append(ch)
                        meta.append({
                            "doc_id": doc_id, "title": title, "heading": heading,
                            "parent_id": pid, "child_id": f"{pid}:t{c_idx}",
                            "type": "text"
                        })
                # CODE child (keep whole)
                if sec.get("code", "").strip():
                    texts.append(sec["code"])
                    meta.append({
                        "doc_id": doc_id, "title": title, "heading": heading,
                        "parent_id": pid, "child_id": f"{pid}:c0",
                        "type": "code"
                    })
        else:
            # flat doc
            pid = section_id(title, "")
            body = d.get("text","")
            parents[pid] = clean_text(f"{title}. {body}")
            for c_idx, ch in enumerate(chunk_semantic(body)):
                texts.append(ch)
                meta.append({
                    "doc_id": doc_id, "title": title, "heading": "",
                    "parent_id": pid, "child_id": f"{pid}:t{c_idx}",
                    "type": "text"
                })

    print(f"docs: {len(docs)}  children: {len(texts)}  parents: {len(parents)}")

    # Embed children
    emb = MODEL.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    # HNSW (good default). For IVF/PQ, train first.
    dim = emb.shape[1]
    index = faiss.IndexHNSWFlat(dim, 32)
    index.hnsw.efConstruction = 200
    index.hnsw.efSearch = 100
    # map chunk ids -> index
    id_index = faiss.IndexIDMap2(index)
    ids = np.arange(len(texts), dtype=np.int64)
    id_index.add_with_ids(emb, ids)

    # Save
    faiss.write_index(id_index, "rag_index.faiss")
    with open("rag_meta.pkl", "wb") as f:
        pickle.dump({"texts": texts, "meta": meta, "parents": parents}, f)

    print("saved rag_index.faiss & rag_meta.pkl")

if __name__ == "__main__":
    main()

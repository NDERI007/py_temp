import os
import pickle
import faiss
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# ------------------------------
# Config
# ------------------------------
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "models/starcoderbase-1b.Q4_K_M.gguf")
INDEX_PATH = "rag_index.faiss"
META_PATH = "rag_meta.pkl"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ------------------------------
# Load LLM
# ------------------------------
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=2,
    n_gpu_layers=0
)

# ------------------------------
# Load Retriever
# ------------------------------
embedder = SentenceTransformer(EMBED_MODEL)

if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
    raise RuntimeError("No RAG index found. Run index_build.py first.")

index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "rb") as f:
    meta = pickle.load(f)

texts = meta["texts"]
metadata = meta["meta"]

def retrieve_context(query: str, k: int = 3) -> str:
    """Embed query, search FAISS, return joined text chunks."""
    q_emb = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index.search(q_emb, k)

    retrieved_chunks = [texts[i] for i in indices[0] if i < len(texts)]
    return "\n".join(retrieved_chunks)

def trim_hint(text, max_sentences=2):
    sentences = text.split(". ")
    return ". ".join(sentences[:max_sentences]).strip()

# ------------------------------
# Prompt Template
# ------------------------------
PROMPT_TEMPLATE = """
You are a friendly, humble, and helpful coding tutor.
You are polite, precise, and aim to guide beginners.
You use retrieved context only to help your answer.
You avoid giving false or misleading information.
You NEVER copy text verbatim from your sources.
You give hints in ONE short sentence, without examples or full solutions.
If unsure, you caveat your hint.

Context:
{context}

User question:
{question}

Hint:
"""

# ------------------------------
# FastAPI app
# ------------------------------
app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/query")
def query_endpoint(q: Query):
    if not q.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    # 1. Retrieve context from FAISS
    context = retrieve_context(q.query)

    # 2. Build prompt
    prompt = PROMPT_TEMPLATE.format(context=context, question=q.query)

    try:
        output = llm(
            prompt,
            max_tokens=100,
            temperature=0.3,
        )
        answer = output["choices"][0]["text"].strip()
        answer = trim_hint(answer)
        return {
            "answer": answer or "No hint generated, try rephrasing.",
            "context_used": context
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


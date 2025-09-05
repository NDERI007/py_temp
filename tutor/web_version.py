import os
import pickle
import re
from typing import List, Tuple
import faiss
from flask import Flask, request, jsonify, render_template_string
from llama_cpp import Llama
from dotenv import load_dotenv
import numpy as np
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
    store = pickle.load(f)

texts = store["texts"]
metadata = store["meta"]
parents = store.get("parents", {})  # parent_id -> parent text


# ------------------------------
# MMR utility (diversify retrieval)
# ------------------------------
def mmr(query_vec: np.ndarray, doc_vecs: np.ndarray, k: int = 5, lambda_mult: float = 0.5) -> List[int]:
    """Maximal Marginal Relevance to avoid redundancy in retrieval.
       Balances relevance (similar to query) and diversity (not too redundant). 
       lambda_mult=0.5 controls the tradeoff.
       This avoids returning 8 nearly identical chunks.
       """
    selected = []
    candidates = list(range(len(doc_vecs)))

    while len(selected) < k and candidates:
        if not selected:
            # first pick = most similar
            idx = np.argmax(doc_vecs @ query_vec)
            selected.append(idx)
            candidates.remove(idx)
            continue

        # compute scores
        query_sims = doc_vecs[candidates] @ query_vec
        diversity = np.max(doc_vecs[selected] @ doc_vecs[candidates].T, axis=0)
        mmr_scores = lambda_mult * query_sims - (1 - lambda_mult) * diversity

        idx = candidates[int(np.argmax(mmr_scores))]
        selected.append(idx)
        candidates.remove(idx)

    return selected


# ------------------------------
# Retriever
# ------------------------------
def retrieve_context(
    query: str,
    k_children: int = 8,
    k_final: int = 3,
    prefer_code: bool = False
) -> Tuple[str, List[str]]:
    """
    Robust retrieval:
      - accepts FAISS results in a variety of shapes/types
      - converts indices safely to Python ints
      - does MMR, parent aggregation and returns (context, code_snippets)
    """
    # Encode query -> 1D numpy vector
    q = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]

    # ANN search: returns (distances, indices)
    D, I = index.search(q[np.newaxis, :], max(32, k_children * 4))

    # Normalize indices to a 1-D iterable of raw index entries
    I_arr = np.asarray(I)  # typically shape (1, k) for single query
    if I_arr.ndim == 1:
        raw_indices = I_arr  # already flat
    elif I_arr.ndim == 2:
        # first row corresponds to our single query
        raw_indices = I_arr[0]
    else:
        # fallback: flatten everything
        raw_indices = I_arr.ravel()

    # Collect candidate children (safely casting any nested arrays/scalars)
    candidates = []
    for raw in raw_indices:
        # turn raw into a numpy array so we can inspect size
        raw_np = np.asarray(raw)

        # If raw_np has multiple entries (rare), iterate through them
        if raw_np.size > 1:
            vals = raw_np.ravel()
        else:
            vals = [raw_np.item()]

        for v in vals:
            # attempt safe conversion to int, skip invalid
            try:
                i = int(v)
            except Exception:
                continue
            if i < 0 or i >= len(texts):
                continue

            m = metadata[i]

            # intent boost detection (simple heuristic)
            if prefer_code or re.search(r"<[a-z]|{|\(|</|```", query.lower()):
                score_boost = 0.10 if m.get("type") == "code" else 0.0
            else:
                score_boost = 0.10 if m.get("type") == "text" else 0.0

            candidates.append((i, m, score_boost))

    if not candidates:
        return "", []

    # Compute embeddings for candidate child texts
    cand_texts = [texts[i] for i, _, _ in candidates]
    child_vecs = embedder.encode(cand_texts, convert_to_numpy=True, normalize_embeddings=True)

    # MMR to pick diverse children (re-using your mmr util)
    sel_idx = mmr(q, child_vecs, k=min(k_children, len(candidates)), lambda_mult=0.5)
    picked = [candidates[j] for j in sel_idx]

    # Aggregate by parent
    parents_hit = {}
    for i, m, boost in picked:
        pid = m.get("parent_id", None)
        parents_hit.setdefault(pid, {"parent": parents.get(pid, ""), "children": []})
        parents_hit[pid]["children"].append(texts[i])

    # Rank parents by similarity (re-embedding small concatenations)
    scored = []
    for pid, pack in parents_hit.items():
        child_text = " ".join(pack["children"])
        # get similarity between aggregated child_text and query
        try:
            sim = float(embedder.encode([child_text], convert_to_numpy=True, normalize_embeddings=True)[0] @ q)
        except Exception:
            sim = 0.0
        scored.append((sim, pid, pack))

    scored.sort(reverse=True)
    top = scored[:k_final]

    # Build final context and code snippets
    final_context = []
    code_snips = []
    for _, pid, pack in top:
        if pack["parent"]:
            final_context.append(pack["parent"])
        for snip in pack["children"][:2]:
            final_context.append(snip)
            # heuristic for code-like snippets
            if re.search(r"[<>{}();/=]|^\s*```", snip):
                code_snips.append(snip)

    return "\n\n".join(final_context), code_snips[:5]

# ------------------------------
# Prompt Template
# ------------------------------
PROMPT_TEMPLATE = """
You are a friendly, humble, and helpful coding tutor.
You use retrieved context only to help your answer.
You avoid giving false or misleading information.
You NEVER copy text verbatim from your sources.
Give only ONE short and friendly hint, like how a tutor nudges a beginner.
Do not list or explain everything, just point the learner in the right direction.
If unsure, you caveat your hint.

Context:
{context}

User question:
{question}

Hint (in a short, encouraging tone, not a list):
"""

# ------------------------------
# Flask app
# ------------------------------
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    answer = None
    context_used = None
    query = None
    code_snippets = []

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            context_used, code_snippets = retrieve_context(query, prefer_code=True)
            prompt = PROMPT_TEMPLATE.format(context=context_used, question=query)
            if context_used.strip():
                prompt = PROMPT_TEMPLATE.format(context=context_used, question=query)
                try:
                    output = llm(prompt, max_tokens=100, temperature=0.3)
                    answer = output["choices"][0]["text"].strip()
                    # keep it short
                    answer = answer.split("\n")[0]
                except Exception as e:
                    answer = f"Error: {str(e)}"
            else:
                answer = "I couldn't find anything relevant in the docs."

    return render_template_string("""
        <!DOCTYPE html> 
        <html>
            <head>
            <title>StarCoder Tutor</title>
            <style>
             body { font-family: Arial, sans-serif; margin: 40px; }
             input[type=text] { width: 70%; padding: 8px; }
             button { padding: 8px 16px; }
             .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; }
              .context { font-size: 0.9em; color: #555; margin-top: 10px; white-space: pre-wrap; }
              pre { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 6px; overflow-x: auto; }
              code { font-family: monospace; }
            </style>
         </head>
        <body>
    <h1>StarCoder Tutor</h1>
    <form method="post">
        <input type="text" name="query" placeholder="Ask a coding question..." required value="{{query or ''}}">
        <button type="submit">Ask</button>
    </form>

    {% if answer %}
        <div class="result">
            <h3>Hint:</h3>
            <p>{{ answer }}</p>

            {% if code_snippets %}
                <h3>Code Snippets:</h3>
                {% for snippet in code_snippets %}
                    <pre><code>{{ snippet }}</code></pre>
                {% endfor %}
            {% endif %}

            {% if context_used %}
                <div class="context">
                    <strong>Context used:</strong><br>
                    {{ context_used }}
                </div>
            {% endif %}
        </div>
    {% endif %}
</body>
</html>

    """, answer=answer, context_used=context_used, query=query, code_snippets=code_snippets,)

@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json()
    if not data or not data.get("query", "").strip():
        return jsonify({"error": "Empty query"}), 400

    query = data["query"]
    context, code_snippets = retrieve_context(query)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)

    try:
        output = llm(prompt, max_tokens=100, temperature=0.3)
        answer = output["choices"][0]["text"].strip()
        return jsonify({
            "answer": answer or "No hint generated, try rephrasing.",
            "context_used": context,
            "code_snippets": code_snippets
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------
# Run server
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

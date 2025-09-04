import os
import pickle
import faiss
from flask import Flask, request, jsonify, render_template_string
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



def retrieve_context(query: str, k: int = 3) -> tuple[str, list[str]]:
    """Embed query, search FAISS, return joined text chunks + any related code."""
    q_emb = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index.search(q_emb, k)

    retrieved_texts = []
    retrieved_code = []

    for i in indices[0]:
        if i < len(texts):
            entry = texts[i]
            entry_meta = metadata[i]

            if entry_meta.get("type") == "text":
                retrieved_texts.append(entry)
            elif entry_meta.get("type") == "code":
                retrieved_code.append(entry)

    return "\n".join(retrieved_texts), retrieved_code

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
            context_used, code_snippets = retrieve_context(query)
            prompt = PROMPT_TEMPLATE.format(context=context_used, question=query)
            try:
                output = llm(prompt, max_tokens=100, temperature=0.3)
                answer = output["choices"][0]["text"].strip()
            except Exception as e:
                answer = f"Error: {str(e)}"

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

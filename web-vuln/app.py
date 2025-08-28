import bleach
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

# --- DB config (simple local SQLite for the mini-app) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contact.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(120), nullable = False)
    email = db.Column(db.String(120), nullable= False)

    def __repr__(self):
        return f"<contact {self.name}>"
    
# --- Home page with a simple search form ---
@app.route('/')
def index():
    return  """
    <h1>Web Security Demos</h1>
    <ul>
        <li><a href="/sqli">SQL Injection Demo</a></li>
        <li><a href="/xss">XSS Demo</a></li>
    </ul>
    """

# === SQLVulnerable search route ===
# Intentionally vulnerable to SQL injection: it builds SQL by concatenating user input
@app.route('/search')
def search():
    """
    ❌ Vulnerable: directly interpolates user input into SQL.
    Try: /search_vuln?name=' OR '1'='1
    → This will dump all rows (classic SQL injection).
    """
    # 1) Get the 'name' query parameter from the URL
    name = request.args.get('name', '')

    # 2) VULNERABLE: build SQL using Python f-string interpolation
    #    If `name` contains SQL special characters, an attacker controls the query.
    sql = f"SELECT id, name, email FROM contact WHERE name = '{name}'"

    # 3) Execute raw SQL text. We are using SQLAlchemy's text() helper, but because
    #    the SQL string already contains the untrusted value, this is still unsafe.
    results = db.session.execute(text(sql)).fetchall()

     # 4) Render results. We pass the raw `name` back to the template (for UX),
    #    which we'll treat as plain text here (Jinja auto-escapes by default).
    return render_template('search_results.html', results= results, query=name)

@app.route('/safe_search')
def search_safe():
    """
    ✅ Safe: uses parameterized queries (bound variables).
    Injection attempts are treated as plain strings.
    """
    name = request.args.get('name')
    sql = text('SELECT id, name, email FROM contact WHERE name = :name')
    results = db.session.execute(sql, {"name": name}).fetchall()
    return jsonify([dict(r._mapping) for r in results])

# Helper to create DB and seed it with sample contacts
def init_db():
    with app.app_context():
     db.create_all()
     if not Contact.query.first():
        sample = [
            Contact(name="Alice", email="alice@example.com"),
            Contact(name="Bob", email="bob@example.com"),
            Contact(name="Charlie", email="charlie@example.com"),
        ]
        db.session.add_all(sample)
        db.session.commit()
        print("DB initialized with sample contacts")

@app.route("/xss")
def xss_index():
    return """
    <h2>XSS Demo</h2>
    <ul>
        <li><a href="/board_vuln">❌ Vulnerable Message Board</a></li>
        <li><a href="/board_safe">✅ Safe Message Board</a></li>
    </ul>
    """
messages = []

@app.route('/board_vuln', methods=["GET", "POST"])
def board_vuln():
    """
    ❌ Vulnerable: directly renders user input without escaping.
    Try posting: <script>alert('XSS!')</script>
    """
    if request.method == "POST":
        msg = request.form.get("message","")
        messages.append(msg) # store raw, unsanitized
        print("Stored messages:", messages)
        return render_template("board_vuln.html", messages=messages)
      # For GET requests, just render the page
    return render_template("board_vuln.html", messages=messages)

safe_messages = []
@app.route("/board_safe", methods=["GET", "POST"])
def board_safe():
    """
    ✅ Safe: sanitizes input before rendering.
    Dangerous HTML (like <script>) is stripped.
    """
    if request.method == "POST":
        msg = request.form.get("message","")
        # Clean the message using bleach
        safe_msg = bleach.clean(msg)
        safe_msg.append(msg)
        return render_template("board_safe.html", messages=safe_messages)
    return render_template("board_safe.html", messages=safe_messages)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
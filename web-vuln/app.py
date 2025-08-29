import bleach
from flask import Flask, jsonify, redirect, request, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from passlib.hash import bcrypt


app = Flask(__name__)

login_manager= LoginManager(app)
login_manager.login_view = "login_safe"

# --- DB config (simple local SQLite for the mini-app) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contact.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SEiji@7'

csrf = CSRFProtect(app)

db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(120), nullable = False)
    email = db.Column(db.String(120), nullable= False)

    def __repr__(self):
        return f"<contact {self.name}>"
    
class User(db.Model, UserMixin): # extend with Flask-Login
    id= db.Column(db.Integer, primary_key= True)
    username= db.Column(db.String(200), unique=True, nullable=False)
    password= db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))

    
# --- Home page with a simple search form ---
@app.route('/')
def index():
    return  """
    <h1>Web Security Demos</h1>
    <ul>
        <li><a href="/sqli">SQL Injection Demo</a></li>
        <li><a href="/xss">XSS Demo</a></li>
        <li><a href="/csrf">CSRF demo</a><li>
        <li><a href="/auth">Auth demo</a></li>
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

#Cross-Site Scripting (XSS)
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
        clean_msg = bleach.clean(msg)
        safe_messages.append(clean_msg)
        return render_template("board_safe.html", messages=safe_messages)
    return render_template("board_safe.html", messages=safe_messages)

# === cross-site Request Forgery ===
@app.route("/csrf")
def csrf_index():
    return """
    <h2>CSRF demo</h2>
    <li><a href="/add_cont_vuln">Vulnerable demo</a></li>
    <li><a href="/add_cont_safe">Safe demo</a><li>
    """
contacts=[]
# === CSRF vulnerable add_contact route ===
@app.route("/add_cont_vuln", methods=["GET", "POST"])
def add_cont_vuln():
    """
    ❌ Vulnerable: no CSRF token.
    An attacker could trick the victim into submitting a form to this endpoint.
    """
    if request.method == "POST":
       name= request.form.get("name","")
       email= request.form.get("email","")
       if name and email:
           contacts.append({"name": name, "email": email})
       return render_template("add_cont_vuln.html", contacts=contacts)
    return render_template("add_cont_vuln.html", contacts=contacts)

@app.route("/add_cont_safe", methods=["GET","POST"])
def add_contact():
    if request.method == "POST":
        name= request.form.get("name","")
        email= request.form.get("email","")
        if name and email:
            contacts.append({"name": name, "email":email})
        return render_template("add_cont_safe.html", contacts=contacts)
    return render_template("add_cont_safe.html", contacts=contacts)
# Handle CSRF errors gracefully
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("csrf_error.html", reason=e.description), 400


# === Auth Issues mainly plaintext password storage ===
@app.route("/auth")
def auth_index():
    return"""
    <h2>Auth demo</h2>
    <li><a href="/signup_vuln">(vuln)Sign in</a></li>
    <li><a href="/login_vuln">(vuln)Login</a><li><br />
    <li><a href="/signup_safe">(safe)Sign in</a></li>
    <li><a href="/login_safe">(safe)Login</a><li>
"""
@app.route("/signup_vuln", methods=["GET", "POST"])
def signup_vuln():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")  # ❌ stored as plaintext
        if username and password:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login_vuln"))
    return render_template("signup_vuln.html")


@app.route("/login_vuln", methods=["GET", "POST"])
def login_vuln():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # ❌ direct comparison
            session["user"] = username
            return f"🎉 Welcome {username} (insecure login)"
        return "❌ Invalid credentials"
    return render_template("login_vuln.html")

@app.route("/signup_safe", methods=["GET", "POST"])
def signup_safe():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        hashed_pw = bcrypt.hash(password)   # ✅ store hash
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login_safe"))
    return render_template("signup_safe.html")


@app.route("/login_safe", methods=["GET", "POST"])
def login_safe():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.verify(password, user.password):   # ✅ hash verify
            login_user(user)
            return redirect(url_for("dashboard"))
        return "❌ Invalid credentials"
    return render_template("login_safe.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return f"🛡️ Welcome {current_user.username} (secure)"


@app.route("/dump_users")
def dump_users():
    users = User.query.all()
    return render_template("dump_users.html", users=users)

if __name__ == "__main__":
    init_db() #okay to call cause it setups the db and seeds data into it
    #board_vuln() You don’t call board_vuln() yourself — Flask will call it automatically when someone visits /board_vuln.
    app.run(debug=True)
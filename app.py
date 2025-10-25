"""
AIsosceles - Minimal Flask site for launch
Run: python app.py
"""
import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
import markdown
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # load .env if present

BASE_DIR = Path(__file__).parent.resolve()
CONTENT_DIR = BASE_DIR / "content"
BLOG_DIR = CONTENT_DIR / "blog_posts"
STUDY_DIR = CONTENT_DIR / "study_sessions"
EBOOKS_FILE = CONTENT_DIR / "ebooks.json"
DATA_DIR = BASE_DIR / "data"
SUBSCRIBE_FILE = DATA_DIR / "subscribers.csv"
CONTACTS_FILE = DATA_DIR / "contacts.csv"

# ensure data folders exist
DATA_DIR.mkdir(exist_ok=True)
CONTENT_DIR.mkdir(exist_ok=True)
BLOG_DIR.mkdir(exist_ok=True)
STUDY_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "super-secret-change-me")

# ---- Helper utilities ----

def list_markdown_posts(folder: Path):
    """Return list of markdown files in folder sorted by mtime desc with metadata."""
    posts = []
    for md in folder.glob("*.md"):
        stat = md.stat()
        posts.append({
            "filename": md.name,
            "path": md,
            "title": md.stem.replace("-", " ").title(),
            "mtime": stat.st_mtime
        })
    posts_sorted = sorted(posts, key=lambda p: p["mtime"], reverse=True)
    return posts_sorted

def render_markdown_file(md_path: Path):
    """Read markdown file and convert to HTML."""
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")
    html = markdown.markdown(text, extensions=["fenced_code","codehilite","tables"])
    return html

def append_csv(path: Path, row: list, header: list = None):
    first = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if first and header:
            writer.writerow(header)
        writer.writerow(row)

# ---- Routes ----

@app.route("/")
def index():
    # story_text left as placeholder; you can set it here or replace in template later
    story_text = "This space is the beginning of AIsosceles. (Paste your founder story in the admin text file or edit templates/index.html)"
    latest_blog = list_markdown_posts(BLOG_DIR)[:3]
    latest_study = list_markdown_posts(STUDY_DIR)[:3]
    return render_template("index.html", story_text=story_text,
                           latest_blog=latest_blog, latest_study=latest_study)

@app.route("/study-sessions")
def study_sessions():
    sessions = list_markdown_posts(STUDY_DIR)
    return render_template("study_sessions.html", sessions=sessions)

@app.route("/study-sessions/<post_name>")
def study_session_post(post_name):
    md_file = STUDY_DIR / f"{post_name}.md"
    html = render_markdown_file(md_file)
    if html is None:
        abort(404)
    return render_template("post.html", content=html, title=post_name.replace("-", " ").title())

@app.route("/ebooks")
def ebooks():
    # ebooks.json is optional; if missing we show empty list
    ebooks = []
    if EBOOKS_FILE.exists():
        import json
        ebooks = json.loads(EBOOKS_FILE.read_text(encoding="utf-8"))
    return render_template("ebooks.html", ebooks=ebooks)

@app.route("/books")
def books():
    # simple static page for other books
    return render_template("books.html")

@app.route("/blog")
def blog():
    posts = list_markdown_posts(BLOG_DIR)
    return render_template("blog.html", posts=posts)

@app.route("/blog/<post_name>")
def blog_post(post_name):
    md_file = BLOG_DIR / f"{post_name}.md"
    html = render_markdown_file(md_file)
    if html is None:
        abort(404)
    return render_template("post.html", content=html, title=post_name.replace("-", " ").title())

# Subscribe endpoint (simple email capture)
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    if not email:
        flash("Please enter a valid email.", "danger")
        return redirect(request.referrer or url_for("index"))
    timestamp = datetime.utcnow().isoformat()
    append_csv(SUBSCRIBE_FILE, [email, timestamp], header=["email","utc_time"])
    flash("Thanks — you are now on the list.", "success")
    return redirect(request.referrer or url_for("index"))

# Contact endpoint
@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()
    if not (message and email):
        flash("Please include at least an email and a message.", "danger")
        return redirect(request.referrer or url_for("index"))
    timestamp = datetime.utcnow().isoformat()
    append_csv(CONTACTS_FILE, [timestamp, name, email, message], header=["utc_time","name","email","message"])
    flash("Thanks — your message has been recorded. I will get back to you.", "success")
    return redirect(request.referrer or url_for("index"))

# Serve favicon if present
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static','images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# simple health route
@app.route("/health")
def health():
    return {"status":"ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)

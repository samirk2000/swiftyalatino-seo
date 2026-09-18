"""
Panel de administracion minimo para el bot de blog de SWIFTYALATINO.
- Ver posts publicados (con link en vivo)
- Ver logs de las ultimas corridas
- Disparar una corrida manual ("Generar post ahora" / "Buscar tendencias ahora")

Corre con Flask + gunicorn detras de Nginx (ver automation/dashboard/DEPLOY.md).
"""
import os
import subprocess
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # raiz del repo
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BASE_DIR / ".env")

from automation import config  # noqa: E402

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", "cambia-esta-clave")

DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")

LOGS_DIR = BASE_DIR / "logs"
LOCK_TRENDS = LOGS_DIR / "trends.lock"
LOCK_POST = LOGS_DIR / "write_post.lock"
VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python"


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")
        if user == DASHBOARD_USER and DASHBOARD_PASSWORD_HASH and check_password_hash(DASHBOARD_PASSWORD_HASH, pwd):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Usuario o contraseña incorrectos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def list_posts():
    posts = []
    if config.BLOG_DIR.exists():
        for f in sorted(config.BLOG_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.name == "index.html":
                continue
            title = f.stem.replace("-", " ").title()
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                start = text.find("<title>")
                end = text.find("</title>")
                if start != -1 and end != -1:
                    title = text[start + 7:end].replace(" | SWIFTYALATINO", "")
            except Exception:
                pass
            thumb = config.BASE_DIR / "assets" / "img" / "blog" / f"{f.stem}.jpg"
            posts.append({
                "slug": f.stem,
                "title": title,
                "url": f"{config.SITE_URL}/blog/{f.name}",
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "has_og": thumb.exists(),
                "thumb_url": f"{config.SITE_URL}/assets/img/blog/{f.stem}.jpg" if thumb.exists() else "",
            })
    return posts


def last_run_info(path: Path) -> str:
    if not path.exists():
        return "nunca"
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    hours = int(age.total_seconds() // 3600)
    if hours < 1:
        return "hace menos de 1h"
    if hours < 48:
        return f"hace {hours}h"
    return f"hace {hours // 24}d"

def tail_log(path: Path, n: int = 40) -> str:
    if not path.exists():
        return "(sin registros todavia)"
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-n:])
    except Exception as e:
        return f"(error leyendo log: {e})"


@app.route("/")
@login_required
def dashboard():
    posts = list_posts()
    trends_log = tail_log(LOGS_DIR / "trends.log")
    post_log = tail_log(LOGS_DIR / "write_post.log")
    return render_template(
        "dashboard.html",
        posts=posts,
        trends_log=trends_log,
        post_log=post_log,
        post_running=LOCK_POST.exists(),
        trends_running=LOCK_TRENDS.exists(),
        site_url=config.SITE_URL,
        last_post_run=last_run_info(LOGS_DIR / "write_post.log"),
        last_trends_run=last_run_info(LOGS_DIR / "trends.log"),
        og_ready=sum(1 for p in posts if p.get("has_og")),
    )


def run_in_background(module: str, lock_path: Path, log_path: Path):
    if lock_path.exists():
        return False
    lock_path.write_text(str(datetime.now()))
    log_file = open(log_path, "a")

    def _cleanup_and_run():
        proc = subprocess.Popen(
            [str(VENV_PYTHON), "-m", module],
            cwd=str(BASE_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        proc.wait()
        lock_path.unlink(missing_ok=True)
        log_file.close()

    import threading
    threading.Thread(target=_cleanup_and_run, daemon=True).start()
    return True


@app.route("/run/post", methods=["POST"])
@login_required
def run_post():
    LOGS_DIR.mkdir(exist_ok=True)
    if run_in_background("automation.write_post", LOCK_POST, LOGS_DIR / "write_post.log"):
        flash("Generando post nuevo en segundo plano. Refresca en 30-60s para ver el resultado.")
    else:
        flash("Ya hay una generacion de post en curso.")
    return redirect(url_for("dashboard"))


@app.route("/run/trends", methods=["POST"])
@login_required
def run_trends():
    LOGS_DIR.mkdir(exist_ok=True)
    if run_in_background("automation.trends", LOCK_TRENDS, LOGS_DIR / "trends.log"):
        flash("Buscando tendencias en segundo plano. Refresca en unos segundos.")
    else:
        flash("Ya hay una busqueda de tendencias en curso.")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8899, debug=False)

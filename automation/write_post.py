"""
Se ejecuta MARTES y VIERNES: genera un post de blog nuevo con DeepSeek,
lo publica en blog/, actualiza blog/index.html y sitemap.xml, hace commit+push
directo a main, y despliega directo a Hostinger por FTP. 100% sin intervencion
humana ni PRs.
"""
import json
import re
import time
import traceback
import unicodedata
from datetime import date, datetime, timedelta

import requests

from . import config, git_utils, template, site_updater, ftp_deploy, notify, og_image, indexing
from .deepseek_client import chat

def build_system_prompt(angle: str, existing_posts: list[dict]) -> str:
    if existing_posts:
        links_list = "\n".join(f'- "{p["title"]}" -> {p["url"]}' for p in existing_posts)
        internal_links_rule = (
            "- DEBES incluir 1 o 2 enlaces internos naturales dentro del body_html (etiqueta <a href>) "
            "hacia artículos anteriores relevantes de esta lista (usa la URL completa tal cual, texto ancla natural, "
            "NO fuerces el enlace si ningún tema calza bien):\n" + links_list
        )
    else:
        internal_links_rule = "- No hay posts anteriores todavia, no incluyas enlaces internos a otros posts."

    return f"""Eres un redactor SEO experto en IPTV latino para la marca SWIFTYALATINO.
Escribes en español neutro/mexicano, tono cercano y profesional, sin relleno.

Datos oficiales que DEBES usar (nunca inventes otros precios ni contactos):
{config.PLANS_TEXT}

WhatsApp: {config.WHATSAPP_LINK}
Telefono: {config.PHONE}
Sitio: {config.SITE_URL}

Paises objetivo: {', '.join(config.TARGET_COUNTRIES)} (Mexico es el mercado principal).
Keywords objetivo: {', '.join(config.TARGET_KEYWORDS)}.

ANGULO OBLIGATORIO para este articulo (no te desvies de este enfoque):
{angle}

Reglas estrictas:
- NUNCA incluyas URLs de pago (Stripe, PayPal, checkout), ni links m3u, Xtream, ni panel.
- NUNCA inventes precios distintos a los oficiales de arriba.
- El HTML del cuerpo debe usar <h2>, <h3>, <p>, <ul>/<ol>, <strong>, <a href> (sin <html>/<head>/<body>, sin <h1>, sin CSS inline).
- Incluye tambien al menos 1 enlace interno a la pagina principal ({config.SITE_URL}/#planes o {config.SITE_URL}/#faq) con texto ancla natural.
{internal_links_rule}
- Aproximadamente 1200-1600 palabras.
- Debe mencionar naturalmente varias de las keywords objetivo, y el titulo NO debe repetir literalmente el titulo de ningun post anterior de la lista.
- Responde UNICAMENTE con un JSON valido (sin markdown, sin ```), con esta forma exacta:
{{
  "slug": "slug-corto-en-minusculas-sin-acentos",
  "title": "Titulo con una keyword relevante",
  "meta_description": "Descripcion de 140-160 caracteres",
  "keywords": "keyword1, keyword2, keyword3",
  "summary": "Resumen de 1-2 frases para la tarjeta del listado del blog",
  "body_html": "<h2>...</h2><p>...</p>...",
  "faq": [["Pregunta 1", "Respuesta 1"], ["Pregunta 2", "Respuesta 2"], ["Pregunta 3", "Respuesta 3"], ["Pregunta 4", "Respuesta 4"], ["Pregunta 5", "Respuesta 5"]]
}}
"""


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    return text[:70].strip("-")


def get_trends_context() -> str:
    if not config.TRENDS_NOTES_PATH.exists():
        return ""
    mtime = datetime.fromtimestamp(config.TRENDS_NOTES_PATH.stat().st_mtime)
    if datetime.now() - mtime > timedelta(days=5):
        return ""  # notas viejas, ignorar
    return config.TRENDS_NOTES_PATH.read_text(encoding="utf-8")


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    return json.loads(raw[start : end + 1])


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def validate_post(data: dict, existing_posts: list[dict]) -> list[str]:
    """Devuelve una lista de errores (vacia = post valido). No lanza excepciones."""
    errors = []

    for field in ("slug", "title", "meta_description", "keywords", "summary", "body_html", "faq"):
        if not data.get(field):
            errors.append(f"Falta el campo '{field}' o esta vacio.")
    if errors:
        return errors  # sin estos campos no se puede validar el resto

    word_count = len(strip_html(data["body_html"]).split())
    if word_count < 900:
        errors.append(f"El articulo tiene solo {word_count} palabras (minimo esperado: 900).")

    meta_len = len(data["meta_description"])
    if not (100 <= meta_len <= 175):
        errors.append(f"meta_description tiene {meta_len} caracteres (debe estar entre 100 y 175).")

    if "<a href" not in data["body_html"]:
        errors.append("El body_html no incluye ningun enlace interno (<a href>), es obligatorio.")

    if not isinstance(data["faq"], list) or len(data["faq"]) < 3:
        errors.append("Debe incluir al menos 3 preguntas de FAQ.")
    else:
        for item in data["faq"]:
            if not isinstance(item, list) or len(item) != 2 or not item[0].strip() or not item[1].strip():
                errors.append("Alguna pregunta/respuesta del FAQ esta vacia o mal formada.")
                break

    title_norm = data["title"].strip().lower()
    for p in existing_posts:
        if p["title"].strip().lower() == title_norm:
            errors.append(f"El titulo es identico a un post existente: '{p['title']}'.")

    return errors


def get_existing_posts() -> list[dict]:
    """Lista {title, url} de posts ya publicados, leyendo el <title> de cada HTML."""
    posts = []
    if not config.BLOG_DIR.exists():
        return posts
    for f in sorted(config.BLOG_DIR.glob("*.html")):
        if f.name == "index.html":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            start = text.find("<title>")
            end = text.find("</title>")
            title = text[start + 7 : end].replace(" | SWIFTYALATINO", "") if start != -1 and end != -1 else f.stem
        except Exception:
            title = f.stem
        posts.append({"title": title, "url": f"{config.SITE_URL}/blog/{f.name}"})
    return posts


def pick_angle(post_count: int) -> str:
    return config.CONTENT_ANGLES[post_count % len(config.CONTENT_ANGLES)]


def unique_slug(base_slug: str) -> str:
    slug = base_slug
    n = 2
    while (config.BLOG_DIR / f"{slug}.html").exists():
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


def verify_live(url: str, retries: int = 3, wait_seconds: int = 5) -> bool:
    """Chequea que la URL responda 200. Reintenta unas veces (CDN/propagacion)."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return True
            print(f"Verificacion intento {attempt}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Verificacion intento {attempt} fallo: {e}")
        time.sleep(wait_seconds)
    return False


def run() -> str:
    """Genera y publica un post. Devuelve la URL publicada. Lanza excepcion si algo falla."""
    existing_posts = get_existing_posts()
    angle = pick_angle(len(existing_posts))
    system_prompt = build_system_prompt(angle, existing_posts)
    print(f"Angulo elegido ({len(existing_posts)} posts previos): {angle[:80]}...")

    trends_context = get_trends_context()
    if trends_context:
        user_prompt = (
            "Usa como inspiracion (si aplica) estas tendencias recientes de futbol/entretenimiento "
            "para elegir un tema concreto DENTRO del angulo obligatorio ya definido. Si no son relevantes, "
            "ignoralas y elige un tema evergreen dentro de ese mismo angulo:\n\n" + trends_context
        )
    else:
        user_prompt = (
            "No hay tendencias recientes disponibles. Elige un tema evergreen y original DENTRO del "
            "angulo obligatorio ya definido, que NO se haya cubierto ya de forma obvia por los posts "
            "anteriores listados arriba."
        )

    max_attempts = 3
    data = None
    last_errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        prompt_for_attempt = user_prompt
        if last_errors:
            prompt_for_attempt = (
                user_prompt
                + "\n\nTu intento anterior tuvo estos problemas, corrigelos en esta nueva version:\n- "
                + "\n- ".join(last_errors)
            )
        raw = chat(system_prompt, prompt_for_attempt)
        candidate = extract_json(raw)
        errors = validate_post(candidate, existing_posts)
        if not errors:
            data = candidate
            break
        print(f"Intento {attempt}/{max_attempts} no paso el control de calidad: {errors}")
        last_errors = errors

    if data is None:
        raise RuntimeError(
            f"El post no paso el control de calidad tras {max_attempts} intentos. "
            f"Ultimos errores: {last_errors}"
        )

    slug = unique_slug(slugify(data["slug"]) or slugify(data["title"]))
    published = date.today()

    image_path = og_image.generate(slug, data["title"])
    image_url = f"{config.SITE_URL}/assets/img/blog/{slug}.jpg"

    post_html = template.render_post(
        slug=slug,
        title=data["title"],
        meta_description=data["meta_description"],
        keywords=data["keywords"],
        body_html=data["body_html"],
        faq_items=[tuple(item) for item in data["faq"]],
        published_date=published,
        image_url=image_url,
    )

    config.BLOG_DIR.mkdir(parents=True, exist_ok=True)
    post_path = config.BLOG_DIR / f"{slug}.html"
    post_path.write_text(post_html, encoding="utf-8")
    print(f"Post escrito: {post_path}")

    site_updater.add_post_to_blog_index(slug, data["title"], data["summary"], published)
    site_updater.add_post_to_sitemap(slug, published)

    changed = git_utils.commit_and_push(
        message=f"content: nuevo post de blog {published.isoformat()} - {slug}",
        paths=[
            f"blog/{slug}.html",
            "blog/index.html",
            "sitemap.xml",
            f"assets/img/blog/{slug}.jpg",
            f"{config.INDEXNOW_KEY}.txt",
        ],
    )
    print("Push realizado." if changed else "Sin cambios para pushear (raro).")

    deploy_files = {
        post_path: f"blog/{slug}.html",
        config.BLOG_INDEX_PATH: "blog/index.html",
        config.SITEMAP_PATH: "sitemap.xml",
        image_path: f"assets/img/blog/{slug}.jpg",
        config.BASE_DIR / f"{config.INDEXNOW_KEY}.txt": f"{config.INDEXNOW_KEY}.txt",
    }

    # Deploy directo a Hostinger (no depender del Git Deploy, que ha fallado antes)
    ftp_deploy.deploy(deploy_files)

    live_url = f"{config.SITE_URL}/blog/{slug}.html"
    print(f"Verificando que el post ya este en vivo: {live_url}")
    if not verify_live(live_url):
        print("La verificacion fallo, reintentando el deploy por FTP una vez mas...")
        ftp_deploy.deploy(deploy_files)
        if not verify_live(live_url, retries=2):
            raise RuntimeError(
                f"El post se genero y se hizo push a git, pero no responde 200 en {live_url} "
                "tras reintentar el deploy por FTP. Revisar Hostinger manualmente."
            )

    print(f"Publicado y verificado en vivo: {live_url}")
    index_results = indexing.submit_url(live_url)
    print(f"Indexacion: {index_results}")
    return live_url


def main():
    try:
        live_url = run()
    except Exception:
        error_trace = traceback.format_exc()
        print(error_trace)
        notify.notify_failure(
            "Fallo al generar/publicar el post de blog",
            error_trace[-500:],
        )
        raise
    else:
        notify.notify_success(
            "Nuevo post de blog publicado",
            f"{live_url}",
        )


if __name__ == "__main__":
    main()

"""
Se ejecuta MARTES y VIERNES: genera un post de blog nuevo con DeepSeek,
lo publica en blog/, actualiza blog/index.html y sitemap.xml, hace commit+push
directo a main, y despliega directo a Hostinger por FTP. 100% sin intervencion
humana ni PRs.
"""
import json
import re
import unicodedata
from datetime import date, datetime, timedelta

from . import config, git_utils, template, site_updater, ftp_deploy
from .deepseek_client import chat

SYSTEM_PROMPT = f"""Eres un redactor SEO experto en IPTV latino para la marca SWIFTYALATINO.
Escribes en español neutro/mexicano, tono cercano y profesional, sin relleno.

Datos oficiales que DEBES usar (nunca inventes otros precios ni contactos):
{config.PLANS_TEXT}

WhatsApp: {config.WHATSAPP_LINK}
Telefono: {config.PHONE}
Sitio: {config.SITE_URL}

Paises objetivo: {', '.join(config.TARGET_COUNTRIES)} (Mexico es el mercado principal).
Keywords objetivo: {', '.join(config.TARGET_KEYWORDS)}.

Reglas estrictas:
- NUNCA incluyas URLs de pago (Stripe, PayPal, checkout), ni links m3u, Xtream, ni panel.
- NUNCA inventes precios distintos a los oficiales de arriba.
- El HTML del cuerpo debe usar <h2>, <h3>, <p>, <ul>/<ol>, <strong> (sin <html>/<head>/<body>, sin <h1>, sin CSS inline).
- Aproximadamente 1200-1600 palabras.
- Debe mencionar naturalmente varias de las keywords objetivo.
- Responde UNICAMENTE con un JSON valido (sin markdown, sin ```), con esta forma exacta:
{{
  "slug": "slug-corto-en-minusculas-sin-acentos",
  "title": "Titulo con una keyword relevante",
  "meta_description": "Descripcion de 140-160 caracteres",
  "keywords": "keyword1, keyword2, keyword3",
  "summary": "Resumen de 1-2 frases para la tarjeta del listado del blog",
  "body_html": "<h2>...</h2><p>...</p>...",
  "faq": [["Pregunta 1", "Respuesta 1"], ["Pregunta 2", "Respuesta 2"], ["Pregunta 3", "Respuesta 3"]]
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


def unique_slug(base_slug: str) -> str:
    slug = base_slug
    n = 2
    while (config.BLOG_DIR / f"{slug}.html").exists():
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


def main():
    trends_context = get_trends_context()
    if trends_context:
        user_prompt = (
            "Usa como inspiracion (si aplica) estas tendencias recientes de futbol/entretenimiento "
            "para elegir el angulo del articulo. Si no son relevantes para IPTV, ignoralas y elige "
            "un tema evergreen sobre IPTV latino:\n\n" + trends_context
        )
    else:
        user_prompt = (
            "No hay tendencias recientes disponibles. Elige un tema evergreen y original sobre IPTV "
            "latino, futbol en vivo, comparativas de planes, o guias por pais, que NO se haya cubierto "
            "ya de forma obvia (evita repetir literalmente articulos anteriores de la carpeta blog/)."
        )

    raw = chat(SYSTEM_PROMPT, user_prompt)
    data = extract_json(raw)

    slug = unique_slug(slugify(data["slug"]) or slugify(data["title"]))
    published = date.today()

    post_html = template.render_post(
        slug=slug,
        title=data["title"],
        meta_description=data["meta_description"],
        keywords=data["keywords"],
        body_html=data["body_html"],
        faq_items=[tuple(item) for item in data["faq"]],
        published_date=published,
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
        ],
    )
    print("Push realizado." if changed else "Sin cambios para pushear (raro).")

    # Deploy directo a Hostinger (no depender del Git Deploy, que ha fallado antes)
    ftp_deploy.deploy(
        {
            post_path: f"blog/{slug}.html",
            config.BLOG_INDEX_PATH: "blog/index.html",
            config.SITEMAP_PATH: "sitemap.xml",
        }
    )
    print(f"Publicado en vivo: {config.SITE_URL}/blog/{slug}.html")


if __name__ == "__main__":
    main()

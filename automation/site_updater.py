"""Actualiza blog/index.html y sitemap.xml al publicar un post nuevo."""
import re
from datetime import date
from . import config


def add_post_to_blog_index(slug: str, title: str, summary: str, published_date: date):
    html = config.BLOG_INDEX_PATH.read_text(encoding="utf-8")
    date_str = published_date.strftime("%Y-%m-%d")
    date_human = published_date.strftime("%d de %B de %Y")

    new_card = (
        f'      <article class="card">\n'
        f'        <time class="post-date" datetime="{date_str}">{date_human}</time>\n'
        f'        <h3><a href="/blog/{slug}.html">{title}</a></h3>\n'
        f'        <p>{summary}</p>\n'
        f'      </article>\n'
    )

    placeholder = re.search(
        r'<article class="card">\s*<h3>Pr[oó]ximamente.*?</article>\s*',
        html,
        re.DOTALL,
    )
    if placeholder:
        html = html[: placeholder.start()] + new_card + html[placeholder.end():]
    else:
        marker = '<div id="post-list" class="grid grid-2">\n'
        idx = html.find(marker)
        if idx == -1:
            raise RuntimeError("No se encontro el contenedor #post-list en blog/index.html")
        insert_at = idx + len(marker)
        html = html[:insert_at] + new_card + html[insert_at:]

    config.BLOG_INDEX_PATH.write_text(html, encoding="utf-8")


def add_post_to_sitemap(slug: str, published_date: date):
    xml = config.SITEMAP_PATH.read_text(encoding="utf-8")
    date_str = published_date.strftime("%Y-%m-%d")
    url = f"{config.SITE_URL}/blog/{slug}.html"
    if url in xml:
        return  # ya existe, no duplicar
    entry = (
        f"  <url>\n"
        f"    <loc>{url}</loc>\n"
        f"    <lastmod>{date_str}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n"
        f"    <priority>0.7</priority>\n"
        f"  </url>\n"
    )
    xml = xml.replace("</urlset>", entry + "</urlset>")
    config.SITEMAP_PATH.write_text(xml, encoding="utf-8")

"""
Parchea los posts HTML ya publicados:
- Breadcrumb visible + schema BreadcrumbList
- Bloque "Tambien te puede interesar" con enlaces a los otros posts
No regenera el articulo; solo inyecta SEO interno.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import config

POSTS = [
    {
        "slug": "checklist-elegir-buen-iptv-latino",
        "title": "10 claves para elegir el mejor IPTV latino en 2026",
    },
    {
        "slug": "iptv-latino-partidos-que-no-puedes-perder",
        "title": "IPTV Latino: Guía Definitiva para Ver Fútbol en Vivo sin Perderte Ningún Partido",
    },
    {
        "slug": "mejor-iptv-mexico-2026-ver-futbol-en-vivo",
        "title": "Mejor IPTV México 2026: ver fútbol en vivo y canales latinos",
    },
]


def _breadcrumb_html(title: str) -> str:
    short = title[:48] + ("…" if len(title) > 48 else "")
    return (
        '<nav class="breadcrumbs" aria-label="Breadcrumb">\n'
        '      <a href="/">Inicio</a> / <a href="/blog/">Blog</a> / '
        f"<span>{short}</span>\n"
        "    </nav>\n    "
    )


def _breadcrumb_schema(slug: str, title: str) -> str:
    url = f"{config.SITE_URL}/blog/{slug}.html"
    # Escape quotes in title for JSON
    safe_title = title.replace('"', '\\"')
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Inicio", "item": "{config.SITE_URL}/"}},
    {{"@type": "ListItem", "position": 2, "name": "Blog", "item": "{config.SITE_URL}/blog/"}},
    {{"@type": "ListItem", "position": 3, "name": "{safe_title}", "item": "{url}"}}
  ]
}}
</script>
"""


def _related_html(current_slug: str) -> str:
    items = []
    for p in POSTS:
        if p["slug"] == current_slug:
            continue
        items.append(
            f'      <li><a href="/blog/{p["slug"]}.html">{p["title"]}</a></li>'
        )
    return (
        '<aside class="related-posts">\n'
        "    <h2>También te puede interesar</h2>\n"
        "    <ul>\n"
        + "\n".join(items)
        + "\n    </ul>\n"
        "  </aside>\n\n    "
    )


def patch_post(slug: str, title: str) -> bool:
    path = config.BLOG_DIR / f"{slug}.html"
    if not path.exists():
        print(f"No existe: {path}")
        return False
    html = path.read_text(encoding="utf-8")
    changed = False

    if "BreadcrumbList" not in html:
        schema = _breadcrumb_schema(slug, title)
        html = html.replace("</head>", schema + "</head>", 1)
        changed = True

    if 'class="breadcrumbs"' not in html:
        crumb = _breadcrumb_html(title)
        if 'class="post-hero"' in html:
            html = html.replace(
                '<img class="post-hero"',
                crumb + '<img class="post-hero"',
                1,
            )
        else:
            html = re.sub(r"(<h1[^>]*>)", crumb + r"\1", html, count=1)
        changed = True

    if 'class="related-posts"' not in html:
        related = _related_html(slug)
        if 'class="blog-cta"' in html:
            html = html.replace('<div class="blog-cta">', related + '<div class="blog-cta">', 1)
        else:
            html = html.replace("</article>", related + "</article>", 1)
        changed = True

    if changed:
        path.write_text(html, encoding="utf-8")
        print(f"Parcheado: {path.name}")
    else:
        print(f"Ya estaba al dia: {path.name}")
    return changed


def run() -> list[Path]:
    updated = []
    for p in POSTS:
        if patch_post(p["slug"], p["title"]):
            updated.append(config.BLOG_DIR / f"{p['slug']}.html")
    return updated


if __name__ == "__main__":
    run()

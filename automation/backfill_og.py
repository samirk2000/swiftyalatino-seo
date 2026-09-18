"""
Backfill: genera imagen OG + meta og:image + hero para posts viejos que no la tienen,
los sube por FTP y los notifica a IndexNow.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import config, ftp_deploy, indexing, og_image, notify


def _title_from_html(html: str, fallback: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not m:
        return fallback
    return m.group(1).replace(" | SWIFTYALATINO", "").replace(" | SWIFTYALATINO", "").strip()


def _has_og_image(html: str) -> bool:
    return 'property="og:image"' in html or "property='og:image'" in html


def _inject_og_and_hero(html: str, image_url: str, title: str) -> str:
    # Meta og:image / twitter:image
    if 'property="og:image"' not in html:
        inject = (
            f'<meta property="og:image" content="{image_url}">\n'
            f'<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:image" content="{image_url}">\n'
        )
        if "</head>" in html:
            html = html.replace("</head>", inject + "</head>", 1)

    # Hero image before h1 if missing
    if 'class="post-hero"' not in html and 'class="post-cover"' not in html:
        hero = (
            f'<img class="post-hero" src="{image_url}" alt="{title}" '
            f'width="1200" height="630" loading="eager">\n    '
        )
        html = re.sub(r"(<h1[^>]*>)", hero + r"\1", html, count=1)

    # Schema image field (best-effort)
    if '"image"' not in html and '"@type": "Article"' in html:
        html = html.replace(
            '"@type": "Article"',
            f'"@type": "Article",\n  "image": "{image_url}"',
            1,
        )
    return html


def run(force: bool = False) -> list[str]:
    updated: list[str] = []
    blog_dir = config.BLOG_DIR
    deploy: dict[Path, str] = {}

    for path in sorted(blog_dir.glob("*.html")):
        if path.name == "index.html":
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        if _has_og_image(html) and not force:
            print(f"Skip (ya tiene og:image): {path.name}")
            continue

        slug = path.stem
        title = _title_from_html(html, slug.replace("-", " ").title())
        image_path = og_image.generate(slug, title)
        image_url = f"{config.SITE_URL}/assets/img/blog/{slug}.jpg"
        new_html = _inject_og_and_hero(html, image_url, title)
        path.write_text(new_html, encoding="utf-8")

        deploy[path] = f"blog/{path.name}"
        deploy[image_path] = f"assets/img/blog/{slug}.jpg"
        updated.append(f"{config.SITE_URL}/blog/{path.name}")
        print(f"Actualizado: {path.name}")

    if not deploy:
        print("Nada que backfillear.")
        return []

    # CSS por si el hero necesita estilos nuevos
    css = config.BASE_DIR / "assets" / "css" / "style.css"
    if css.exists():
        deploy[css] = "assets/css/style.css"

    ftp_deploy.deploy(deploy)

    for url in updated:
        indexing.submit_url(url)

    notify.notify_success(
        "Backfill OG + IndexNow listo",
        "\n".join(f"• {u}" for u in updated),
    )
    return updated


if __name__ == "__main__":
    run()

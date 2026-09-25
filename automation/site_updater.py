"""Actualiza blog/index.html y sitemap.xml al publicar un post nuevo."""
import re
import time
from datetime import date

import requests

from . import config
from .sitemap_merge import merge_sitemap_xml, sitemap_locs


def add_post_to_blog_index(slug: str, title: str, summary: str, published_date: date):
    html = config.BLOG_INDEX_PATH.read_text(encoding="utf-8")
    date_str = published_date.strftime("%Y-%m-%d")
    date_human = published_date.strftime("%d de %B de %Y")

    thumb = f'/assets/img/blog/{slug}.jpg'
    new_card = (
        f'      <article class="card">\n'
        f'        <a href="/blog/{slug}.html"><img class="card-thumb" src="{thumb}" alt="{title}" width="600" height="315" loading="lazy"></a>\n'
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


def merge_live_sitemap_into_local() -> bool:
    """Conserva en el sitemap local las URLs que solo estan en el sitemap en vivo.

    Devuelve True si es seguro subir sitemap.xml: la fusion se aplico, o el
    vivo no tenia entradas nuevas. Devuelve False si no se pudo leer o
    fusionar el sitemap en vivo. En ese caso el archivo local no se reemplaza
    y el llamador no debe subirlo por FTP (pisarlo borraria /guias/ y
    cualquier otra URL que no este en el repo).
    """
    local_xml = config.SITEMAP_PATH.read_text(encoding="utf-8")
    url = f"{config.SITE_URL}/sitemap.xml"
    live_xml = _fetch_live_sitemap(url)
    if live_xml is None:
        print(
            "AVISO: no se pudo leer el sitemap en vivo. "
            "No se subira sitemap.xml por FTP para no borrar URLs /guias/ "
            "ni otras entradas que solo existen en el servidor."
        )
        return False
    try:
        merged = merge_sitemap_xml(local_xml, live_xml)
    except Exception as exc:
        print(
            "AVISO: el sitemap en vivo no se pudo fusionar "
            f"({exc}). No se subira sitemap.xml por FTP para no borrar entradas."
        )
        return False
    if merged != local_xml:
        config.SITEMAP_PATH.write_text(merged, encoding="utf-8")
        local_set = set(sitemap_locs(local_xml))
        added = [loc for loc in sitemap_locs(merged) if loc not in local_set]
        guias = [loc for loc in added if "/guias/" in loc]
        print(
            f"Sitemap fusionado: {len(added)} entradas preservadas del vivo "
            f"({len(guias)} de /guias/)."
        )
    else:
        print("Sitemap en vivo sin entradas nuevas; el archivo local no cambio.")
    return True


def _fetch_live_sitemap(url: str):
    """Lee el sitemap publico. None si los 3 intentos fallan o no es un sitemap."""
    last_error = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "SWIFTYALATINO-sitemap-merge",
                    "Accept": "application/xml, text/xml, */*",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            resp.raise_for_status()
            # La declaracion del sitemap es UTF-8. requests puede decodificar
            # application/xml sin charset como latin-1 y corromper el XML.
            text = resp.content.decode("utf-8")
            if "<urlset" not in text or "<loc>" not in text:
                raise ValueError("la respuesta no parece un sitemap XML")
            return text
        except Exception as exc:
            last_error = exc
            print(f"Aviso: intento {attempt}/3 de leer {url} fallo: {last_error}")
            if attempt < 3:
                time.sleep(2)
    return None

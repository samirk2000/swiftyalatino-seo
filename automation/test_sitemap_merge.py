"""Demuestra que publicar un post no borra las URLs que solo estan en el sitemap vivo.

Ejecutar desde la raiz del repo:

    python -m automation.test_sitemap_merge
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from automation.sitemap_merge import merge_sitemap_xml, sitemap_locs

LOCAL = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://swiftyalatino.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <xhtml:link rel="alternate" hreflang="es" href="https://swiftyalatino.com/"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://swiftyalatino.com/en/"/>
  </url>
  <url>
    <loc>https://swiftyalatino.com/blog/post-nuevo.html</loc>
    <lastmod>2026-09-25</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
"""

LIVE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://swiftyalatino.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <xhtml:link rel="alternate" hreflang="es" href="https://swiftyalatino.com/"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://swiftyalatino.com/en/"/>
  </url>
  <url>
    <loc>https://swiftyalatino.com/guias/</loc>
    <lastmod>2026-09-24</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://swiftyalatino.com/guias/iptv-para-roku-en-monterrey/</loc>
    <lastmod>2026-09-24</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://swiftyalatino.com/guias/iptv-para-roku-en-monterrey/</loc>
    <lastmod>2026-09-24</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://swiftyalatino.com/promo-especial/</loc>
    <lastmod>2026-09-24</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
"""

LIVE_WITH_IMAGE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://swiftyalatino.com/guias/con-imagen/</loc>
    <image:image>
      <image:loc>https://swiftyalatino.com/guias/con-imagen/portada.jpg</image:loc>
    </image:image>
  </url>
</urlset>
"""


def _check(name: str, fn) -> None:
    fn()
    print(f"ok  {name}")


def test_preserves_guias_live_only_and_new_post() -> None:
    merged = merge_sitemap_xml(LOCAL, LIVE)
    locs = sitemap_locs(merged)

    assert locs[:2] == [
        "https://swiftyalatino.com/",
        "https://swiftyalatino.com/blog/post-nuevo.html",
    ]
    assert "https://swiftyalatino.com/guias/" in locs
    assert "https://swiftyalatino.com/guias/iptv-para-roku-en-monterrey/" in locs
    assert "https://swiftyalatino.com/promo-especial/" in locs
    assert locs.count("https://swiftyalatino.com/") == 1
    assert locs.count("https://swiftyalatino.com/guias/iptv-para-roku-en-monterrey/") == 1
    assert len(locs) == len(set(locs)) == 5

    assert 'xmlns:xhtml="http://www.w3.org/1999/xhtml"' in merged
    assert '<xhtml:link rel="alternate" hreflang="es" href="https://swiftyalatino.com/"/>' in merged
    assert '<xhtml:link rel="alternate" hreflang="en" href="https://swiftyalatino.com/en/"/>' in merged
    assert "https://swiftyalatino.com/blog/post-nuevo.html" in merged
    assert "  <loc>https://swiftyalatino.com/guias/</loc>" in merged
    ET.fromstring(merged)


def test_unchanged_when_live_has_no_new_urls() -> None:
    assert merge_sitemap_xml(LOCAL, LOCAL) == LOCAL


def test_keeps_extra_namespace_on_live_only_entry() -> None:
    merged = merge_sitemap_xml(LOCAL, LIVE_WITH_IMAGE)
    assert 'xmlns:xhtml="http://www.w3.org/1999/xhtml"' in merged
    assert 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' in merged
    assert "https://swiftyalatino.com/guias/con-imagen/portada.jpg" in merged
    locs = sitemap_locs(merged)
    assert "https://swiftyalatino.com/guias/con-imagen/" in locs
    assert "https://swiftyalatino.com/blog/post-nuevo.html" in locs
    root = ET.fromstring(merged)
    image_ns = "http://www.google.com/schemas/sitemap-image/1.1"
    images = list(root.iter(f"{{{image_ns}}}loc"))
    assert [el.text for el in images] == [
        "https://swiftyalatino.com/guias/con-imagen/portada.jpg"
    ]


def test_rejects_invalid_live_xml() -> None:
    for bad in ("<html>no es un sitemap</html>", "<urlset>", "<<<"):
        try:
            merge_sitemap_xml(LOCAL, bad)
        except (ET.ParseError, ValueError):
            continue
        raise AssertionError(f"un sitemap vivo invalido deberia fallar: {bad!r}")


def main() -> None:
    _check("conserva /guias/, otras URLs vivas y el post nuevo", test_preserves_guias_live_only_and_new_post)
    _check("no reescribe el local si el vivo no aporta URLs", test_unchanged_when_live_has_no_new_urls)
    _check("conserva xmlns extra (image) y hreflang", test_keeps_extra_namespace_on_live_only_entry)
    _check("si el vivo no parsea, la fusion falla", test_rejects_invalid_live_xml)
    print("OK: la fusion no borra /guias/ ni otras entradas que solo estan en el sitemap en vivo.")


if __name__ == "__main__":
    main()

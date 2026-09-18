"""
Indexacion automatica de URLs nuevas.

1) IndexNow (Bing, Yandex, Seznam, Naver, etc.) — gratis, sin OAuth.
2) Ping del sitemap a Google y Bing (senal complementaria).

Nota: Google Search Console Indexing API requiere cuenta de servicio OAuth y
es opcional. IndexNow + sitemap ya acelera bastante el descubrimiento.
"""
from __future__ import annotations

import requests

from . import config

INDEXNOW_ENDPOINTS = (
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
)


def submit_url(url: str) -> dict:
    """Notifica a buscadores que hay una URL nueva/actualizada. No lanza excepciones."""
    results: dict[str, str] = {}
    key = getattr(config, "INDEXNOW_KEY", "") or ""
    if not key:
        print("(indexing) INDEXNOW_KEY no configurada, se omite IndexNow.")
        results["indexnow"] = "skipped"
    else:
        payload = {
            "host": config.SITE_URL.replace("https://", "").replace("http://", "").rstrip("/"),
            "key": key,
            "keyLocation": f"{config.SITE_URL}/{key}.txt",
            "urlList": [url],
        }
        ok_any = False
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                resp = requests.post(endpoint, json=payload, timeout=20)
                results[endpoint] = f"HTTP {resp.status_code}"
                if resp.status_code in (200, 202):
                    ok_any = True
                    print(f"(indexing) IndexNow OK via {endpoint}: {resp.status_code}")
                    break  # uno basta
                print(f"(indexing) IndexNow {endpoint}: {resp.status_code} {resp.text[:120]}")
            except Exception as e:
                results[endpoint] = f"error: {e}"
                print(f"(indexing) Error IndexNow {endpoint}: {e}")
        if not ok_any:
            results["indexnow"] = "failed"

    sitemap_url = f"{config.SITE_URL}/sitemap.xml"
    for name, ping_url in (
        ("google_sitemap", f"https://www.google.com/ping?sitemap={sitemap_url}"),
        ("bing_sitemap", f"https://www.bing.com/ping?sitemap={sitemap_url}"),
    ):
        try:
            resp = requests.get(ping_url, timeout=15)
            results[name] = f"HTTP {resp.status_code}"
            print(f"(indexing) Ping {name}: {resp.status_code}")
        except Exception as e:
            results[name] = f"error: {e}"
            print(f"(indexing) Error ping {name}: {e}")

    return results

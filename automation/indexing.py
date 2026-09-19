"""
Indexacion automatica de URLs nuevas.

1) IndexNow (Bing, Yandex, etc.) — gratis, sin OAuth.
2) Google Indexing API — pide indexacion directa a Google (requiere service account).
3) Ping de sitemap (senal complementaria; Google ya deprecó el endpoint, se intenta igual).

Si no hay credenciales de Google, esa parte se omite en silencio.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from . import config

INDEXNOW_ENDPOINTS = (
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
)

SCOPES = ["https://www.googleapis.com/auth/indexing"]
GOOGLE_INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def _submit_indexnow(url: str, results: dict) -> None:
    key = getattr(config, "INDEXNOW_KEY", "") or ""
    if not key:
        print("(indexing) INDEXNOW_KEY no configurada, se omite IndexNow.")
        results["indexnow"] = "skipped"
        return

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
                break
            print(f"(indexing) IndexNow {endpoint}: {resp.status_code} {resp.text[:120]}")
        except Exception as e:
            results[endpoint] = f"error: {e}"
            print(f"(indexing) Error IndexNow {endpoint}: {e}")
    if not ok_any:
        results["indexnow"] = "failed"


def _google_credentials():
    """Carga la service account desde GOOGLE_SERVICE_ACCOUNT_JSON (ruta al .json)."""
    path = getattr(config, "GOOGLE_SERVICE_ACCOUNT_JSON", "") or ""
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = config.BASE_DIR / p
    if not p.exists():
        print(f"(indexing) No existe el archivo de service account: {p}")
        return None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds = service_account.Credentials.from_service_account_file(str(p), scopes=SCOPES)
        creds.refresh(Request())
        return creds
    except ImportError:
        print("(indexing) Falta google-auth. Instala: pip install google-auth")
        return None
    except Exception as e:
        print(f"(indexing) Error cargando credenciales Google: {e}")
        return None


def _submit_google_indexing(url: str, results: dict) -> None:
    creds = _google_credentials()
    if creds is None:
        results["google_indexing"] = "skipped"
        return
    try:
        resp = requests.post(
            GOOGLE_INDEXING_ENDPOINT,
            headers={
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json",
            },
            data=json.dumps({"url": url, "type": "URL_UPDATED"}),
            timeout=20,
        )
        results["google_indexing"] = f"HTTP {resp.status_code}"
        if resp.status_code in (200, 201):
            print(f"(indexing) Google Indexing API OK: {resp.status_code}")
        else:
            print(f"(indexing) Google Indexing API {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        results["google_indexing"] = f"error: {e}"
        print(f"(indexing) Error Google Indexing API: {e}")


def _ping_sitemaps(results: dict) -> None:
    sitemap_url = f"{config.SITE_URL}/sitemap.xml"
    for name, ping_url in (
        ("google_sitemap", f"https://www.google.com/ping?sitemap={sitemap_url}"),
        ("bing_sitemap", f"https://www.bing.com/ping?sitemap={sitemap_url}"),
    ):
        try:
            resp = requests.get(ping_url, timeout=15)
            results[name] = f"HTTP {resp.status_code}"
            # 404/410 = endpoints deprecados; no es critico
            print(f"(indexing) Ping {name}: {resp.status_code}")
        except Exception as e:
            results[name] = f"error: {e}"
            print(f"(indexing) Error ping {name}: {e}")


def submit_url(url: str) -> dict:
    """Notifica a buscadores que hay una URL nueva/actualizada. No lanza excepciones."""
    results: dict[str, str] = {}
    _submit_indexnow(url, results)
    _submit_google_indexing(url, results)
    _ping_sitemaps(results)
    return results

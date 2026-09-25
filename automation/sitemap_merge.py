"""Fusiona el sitemap del repo con entradas que solo existen en el sitemap en vivo.

El bot escribe posts en sitemap.xml y luego sube ese archivo por FTP. En el
hosting, el mismo sitemap tambien lista /guias/ (y puede listar otras URLs
que no estan en este repo). Subir el archivo local tal cual las borra.

merge_sitemap_xml() conserva cada <url> local y anade las <url> del sitemap
en vivo cuyo <loc> todavia no esta. No duplica, no reescribe las entradas
locales (se mantienen hreflang y xmlns:xhtml) y copia los xmlns que hagan
falta para que el XML siga siendo valido.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# Incluye la sangria previa de <url> para poder reindentar sin descuadrar el cierre.
_URL_BLOCK_RE = re.compile(r"[ \t]*<url\b[^>]*>.*?</url>", re.DOTALL)
_URLSET_RE = re.compile(r"<urlset\b([^>]*)>", re.DOTALL)
_NS_DECL_RE = re.compile(
    r"""xmlns(?::([A-Za-z0-9_.-]+))?\s*=\s*["']([^"']+)["']"""
)


def _local(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _child_urls(root: ET.Element) -> list[ET.Element]:
    return [child for child in list(root) if _local(child.tag) == "url"]


def _loc_text(url_el: ET.Element) -> str:
    for child in list(url_el):
        if _local(child.tag) == "loc" and (child.text or "").strip():
            return (child.text or "").strip()
    return ""


def sitemap_locs(xml_text: str) -> list[str]:
    """Devuelve los <loc> directos de cada <url>, en orden."""
    root = ET.fromstring(xml_text)
    if _local(root.tag) != "urlset":
        raise ValueError("El sitemap no tiene un <urlset> raiz")
    locs = []
    for url_el in _child_urls(root):
        loc = _loc_text(url_el)
        if loc:
            locs.append(loc)
    return locs


def _ns_decls(xml_text: str) -> list[tuple[str, str]]:
    match = _URLSET_RE.search(xml_text)
    if not match:
        return []
    return [(prefix or "", uri) for prefix, uri in _NS_DECL_RE.findall(match.group(1))]


def _open_urlset(decls: list[tuple[str, str]]) -> str:
    parts = []
    for prefix, uri in decls:
        if prefix:
            parts.append(f'xmlns:{prefix}="{uri}"')
        else:
            parts.append(f'xmlns="{uri}"')
    if not parts:
        return "<urlset>"
    return "<urlset " + " ".join(parts) + ">"


def _parse_url_block(block: str, decls: list[tuple[str, str]]) -> ET.Element:
    root = ET.fromstring(_open_urlset(decls) + block + "</urlset>")
    for child in _child_urls(root):
        return child
    raise ValueError("Bloque <url> sin elemento url")


def _normalize_block(block: str) -> str:
    """Reindenta un <url>...</url> a 2 espacios, conservando el anidado relativo."""
    lines = [line.rstrip() for line in block.strip("\n").splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    indents = [len(line) - len(line.lstrip(" ")) for line in lines if line.strip()]
    base = min(indents) if indents else 0
    normalized = []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith(" " * base):
            content = line[base:]
        else:
            content = line.lstrip(" ")
        normalized.append("  " + content)
    return "\n".join(normalized)


def _add_missing_namespaces(local_xml: str, live_xml: str) -> str:
    local_map = {prefix: uri for prefix, uri in _ns_decls(local_xml)}
    missing = []
    for prefix, uri in _ns_decls(live_xml):
        if prefix not in local_map:
            missing.append((prefix, uri))
            local_map[prefix] = uri
    if not missing:
        return local_xml
    match = _URLSET_RE.search(local_xml)
    if not match:
        raise ValueError("El sitemap local no tiene <urlset>")
    extra = "\n" + "\n".join(
        f'        xmlns:{prefix}="{uri}"' if prefix else f'        xmlns="{uri}"'
        for prefix, uri in missing
    )
    insert_at = match.end() - 1
    return local_xml[:insert_at] + extra + local_xml[insert_at:]


def _insert_blocks(xml_text: str, blocks: list[str]) -> str:
    idx = xml_text.rfind("</urlset>")
    if idx == -1:
        raise ValueError("El sitemap local no tiene </urlset>")
    head = xml_text[:idx].rstrip() + "\n"
    tail = xml_text[idx:]
    if not tail.endswith("\n"):
        tail += "\n"
    body = "\n".join(blocks) + "\n"
    return head + body + tail


def _validate_merged(local_xml: str, live_xml: str, merged: str) -> None:
    local_locs = sitemap_locs(local_xml)
    merged_locs = sitemap_locs(merged)
    local_dupes = len(local_locs) - len(set(local_locs))
    merged_dupes = len(merged_locs) - len(set(merged_locs))
    if merged_dupes > local_dupes:
        raise ValueError("La fusion introdujo <loc> duplicados")
    required = set(local_locs) | set(sitemap_locs(live_xml))
    missing = sorted(required - set(merged_locs))
    if missing:
        raise ValueError("La fusion perdio URLs: " + ", ".join(missing[:5]))
    for prefix, uri in _ns_decls(local_xml):
        if uri not in merged or (prefix and f"xmlns:{prefix}" not in merged):
            raise ValueError(f"La fusion perdio el namespace xmlns:{prefix}={uri}")


def merge_sitemap_xml(local_xml: str, live_xml: str) -> str:
    """Une local + entradas solo-vivas. Si no hay nada nuevo, devuelve local_xml intacto."""
    local_root = ET.fromstring(local_xml)
    live_root = ET.fromstring(live_xml)
    if _local(local_root.tag) != "urlset":
        raise ValueError("El sitemap local no tiene un <urlset> raiz")
    # Sin <urlset> o sin <loc> no hay nada fiable que preservar: fallar
    # para que el llamador no suba el sitemap local y borre entradas vivas.
    if _local(live_root.tag) != "urlset" or not sitemap_locs(live_xml):
        raise ValueError("El sitemap en vivo no es un urlset con <loc>")

    seen: set[str] = set()
    for url_el in _child_urls(local_root):
        loc = _loc_text(url_el)
        if loc:
            seen.add(loc)

    decls = _ns_decls(live_xml)
    extras: list[str] = []
    for block in _URL_BLOCK_RE.findall(live_xml):
        loc = _loc_text(_parse_url_block(block, decls))
        if not loc or loc in seen:
            continue
        seen.add(loc)
        normalized = _normalize_block(block)
        if not normalized:
            raise ValueError(f"No se pudo copiar la entrada viva {loc}")
        extras.append(normalized)

    if not extras:
        return local_xml

    merged = _insert_blocks(_add_missing_namespaces(local_xml, live_xml), extras)
    _validate_merged(local_xml, live_xml, merged)
    return merged

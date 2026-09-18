"""
Genera imagen destacada / Open Graph (1200x630) para cada post de blog.
Usa Pillow (sin APIs externas de pago). El resultado se guarda en
assets/img/blog/{slug}.jpg y se sube por FTP junto con el post.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

WIDTH, HEIGHT = 1200, 630
BG = (11, 15, 25)
ACCENT = (37, 211, 102)
TEXT = (244, 246, 251)
MUTED = (169, 178, 195)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/segoeuib.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
        )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate(slug: str, title: str) -> Path:
    """Crea la imagen OG y devuelve la ruta local del JPG."""
    out_dir = config.BASE_DIR / "assets" / "img" / "blog"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.jpg"

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Barra de acento a la izquierda
    draw.rectangle([0, 0, 14, HEIGHT], fill=ACCENT)
    # Franja inferior
    draw.rectangle([0, HEIGHT - 90, WIDTH, HEIGHT], fill=(18, 24, 38))

    brand_font = _load_font(36, bold=True)
    title_font = _load_font(54, bold=True)
    tag_font = _load_font(26, bold=False)

    brand = getattr(config, "BUSINESS_NAME", "SWIFTYALATINO")
    host = config.SITE_URL.replace("https://", "").replace("http://", "").rstrip("/")
    draw.text((56, 40), brand, font=brand_font, fill=ACCENT)
    draw.text((56, HEIGHT - 58), f"Guia IPTV latino  ·  {host}", font=tag_font, fill=MUTED)

    # Titulo envuelto
    wrapped = textwrap.fill(title, width=28)
    lines = wrapped.split("\n")[:4]
    y = 160
    for line in lines:
        draw.text((56, y), line, font=title_font, fill=TEXT)
        y += 70

    # Logo si existe (pequeno, esquina)
    logo_path = config.BASE_DIR / "assets" / "img" / "logo.png"
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((120, 120))
            # pegar sobre fondo oscuro
            pos = (WIDTH - logo.width - 40, 30)
            img.paste(logo, pos, logo)
        except Exception as e:
            print(f"(og_image) No se pudo pegar el logo: {e}")

    img.convert("RGB").save(out_path, "JPEG", quality=85, optimize=True)
    print(f"(og_image) Imagen generada: {out_path}")
    return out_path

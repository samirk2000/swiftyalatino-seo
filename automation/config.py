"""
Configuracion central del bot de blog SEO de SWIFTYALATINO.
Los secretos (API keys, credenciales FTP) SIEMPRE se leen de variables de
entorno / archivo .env (nunca hardcodeados aqui ni commiteados a git).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz del repo swiftyalatino-seo
load_dotenv(BASE_DIR / ".env")

# --- Secretos (desde .env) ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
FTP_HOST = os.getenv("FTP_HOST", "")
FTP_USER = os.getenv("FTP_USER", "")
FTP_PASS = os.getenv("FTP_PASS", "")
FTP_PORT = int(os.getenv("FTP_PORT", "21"))

# --- Datos del negocio (definidos en .cursorrules, no deben cambiar solos) ---
BUSINESS_NAME = "SWIFTYALATINO"
WHATSAPP_LINK = "https://wa.me/message/RUQZ63ESW76VB1"
PHONE = "+52 1 662 268 4690"
PHONE_TEL = "+526622684690"
SITE_URL = "https://swiftyalatino.com"

PLANS_TEXT = """
Plan LATINO PREMIUM: 3000 canales, 12000 peliculas, 5000 series, 3 conexiones.
Precios (MXN): 1 mes $150, 3 meses $390, 6 meses $750, 12 meses $1299.

Plan MEGA TOTAL: 8000 canales, 3 conexiones.
Precios (MXN): 1 mes $160, 4 meses $480, 8 meses $860, 12 meses $1240, 16 meses $1520.

Pagos: en Mexico transferencia bancaria u OXXO. Fuera de Mexico, PayPal o un
link privado de pago enviado SOLO por WhatsApp. NUNCA se publican URLs de pago,
m3u, Xtream ni panel en la web.
"""

TARGET_KEYWORDS = [
    "mejor iptv mexico",
    "iptv mexicanos en usa",
    "mejor iptv españa",
    "iptv colombia",
    "iptv peru",
    "comprar iptv",
    "ver futbol en vivo",
]

TARGET_COUNTRIES = ["Mexico", "Estados Unidos", "Canada", "España", "Colombia", "Peru", "Chile", "Argentina", "Ecuador", "Panama"]

REPO_DIR = BASE_DIR
BLOG_DIR = BASE_DIR / "blog"
TRENDS_NOTES_PATH = BASE_DIR / "seo" / "trends-notes.md"
SITEMAP_PATH = BASE_DIR / "sitemap.xml"
BLOG_INDEX_PATH = BASE_DIR / "blog" / "index.html"
STYLE_CSS_PATH = BASE_DIR / "assets" / "css" / "style.css"

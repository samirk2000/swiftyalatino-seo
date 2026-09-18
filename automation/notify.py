"""
Notificaciones instantaneas al celular del dueno via Telegram (gratis, sin
costo por mensaje, a diferencia de la API de WhatsApp Business).

Configuracion (en .env):
  TELEGRAM_BOT_TOKEN=...   (se obtiene hablando con @BotFather en Telegram)
  TELEGRAM_CHAT_ID=...     (tu ID de chat personal)

Si no estan configuradas, las funciones no hacen nada (fallan en silencio)
para no romper el flujo principal del bot por un problema de notificaciones.
"""
import requests
from . import config

TELEGRAM_BOT_TOKEN = getattr(config, "TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = getattr(config, "TELEGRAM_CHAT_ID", "")


def send(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("(notify) Telegram no configurado, se omite notificacion:", message[:80])
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
    except Exception as e:
        print(f"(notify) Error enviando notificacion a Telegram: {e}")


def notify_success(title: str, details: str) -> None:
    send(f"✅ <b>{title}</b>\n{details}")


def notify_failure(title: str, error: str) -> None:
    send(f"🚨 <b>{title}</b>\n{error}\n\nRevisa el panel: https://bot.swiftyalatino.com")

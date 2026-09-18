"""
Watchdog del cron: avisa por Telegram si el bot no publico cuando debia.

- Martes y viernes: espera ver actividad reciente en logs/write_post.log
- Lunes: espera ver actividad en logs/trends.log

Se agenda diario (cron) a las 12:00 — da margen de 3h tras la corrida de las 9am.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from . import config, notify

LOGS_DIR = config.BASE_DIR / "logs"  # noqa: keep aligned with config.BASE_DIR
POST_LOG = LOGS_DIR / "write_post.log"
TRENDS_LOG = LOGS_DIR / "trends.log"


def _recently_updated(path: Path, within_hours: float = 6) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime <= timedelta(hours=within_hours)


def run() -> None:
    today = datetime.now()
    weekday = today.weekday()  # 0=lunes ... 6=domingo
    messages = []

    if weekday == 0:  # lunes → trends
        if not _recently_updated(TRENDS_LOG, within_hours=8):
            messages.append(
                "Hoy es lunes y no hay actividad reciente en trends.log. "
                "El cron de tendencias (8am) probablemente no corrio."
            )
    elif weekday in (1, 4):  # martes / viernes → post
        if not _recently_updated(POST_LOG, within_hours=6):
            day_name = "martes" if weekday == 1 else "viernes"
            messages.append(
                f"Hoy es {day_name} y no hay actividad reciente en write_post.log. "
                "El cron de posts (9am) probablemente no corrio o fallo antes de escribir log."
            )

    if messages:
        notify.notify_failure("Watchdog del bot SEO", "\n".join(messages))
        print("ALERTA:", messages)
    else:
        print(f"Watchdog OK ({today.strftime('%A %Y-%m-%d %H:%M')}). Nada que reportar.")


if __name__ == "__main__":
    run()

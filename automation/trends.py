"""
Se ejecuta los LUNES: obtiene tendencias reales de Google Trends (futbol /
entretenimiento) para Mexico, España y USA usando pytrends (gratis, sin API
key), y guarda un resumen en seo/trends-notes.md para que write_post.py lo
use como inspiracion el martes/viernes.
"""
from datetime import date, datetime
from pytrends.request import TrendReq

from . import config, git_utils

SEED_TERMS = ["futbol", "liga mx", "champions league", "iptv", "ver futbol en vivo"]
GEOS = {"MX": "Mexico", "ES": "España", "US": "Estados Unidos (hispanos)"}


def fetch_trends_for_geo(pytrends: TrendReq, geo: str) -> list[str]:
    try:
        pytrends.build_payload(SEED_TERMS, timeframe="now 7-d", geo=geo)
        related = pytrends.related_queries()
        topics = []
        for term, data in related.items():
            if data and data.get("top") is not None:
                topics.extend(data["top"]["query"].head(5).tolist())
        # tambien trending searches generales del dia (si esta disponible para el geo)
        return list(dict.fromkeys(topics))[:10]  # unicos, max 10
    except Exception as e:
        print(f"Aviso: no se pudieron obtener trends para {geo}: {e}")
        return []


def main():
    pytrends = TrendReq(hl="es-419", tz=360)
    lines = [f"# Notas de tendencias — semana del {date.today().isoformat()}", ""]

    any_data = False
    for geo_code, geo_name in GEOS.items():
        topics = fetch_trends_for_geo(pytrends, geo_code)
        lines.append(f"## {geo_name}")
        if topics:
            any_data = True
            for t in topics:
                lines.append(f"- {t}")
        else:
            lines.append("- (sin datos suficientes esta semana, usar tema evergreen)")
        lines.append("")

    lines.append(f"_Generado automaticamente el {datetime.now().isoformat(timespec='seconds')}_")

    config.TRENDS_NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.TRENDS_NOTES_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Trends guardadas en {config.TRENDS_NOTES_PATH} (datos reales: {any_data})")

    changed = git_utils.commit_and_push(
        message=f"chore: trends notes {date.today().isoformat()}",
        paths=["seo/trends-notes.md"],
    )
    print("Push realizado." if changed else "Sin cambios para pushear.")


if __name__ == "__main__":
    main()

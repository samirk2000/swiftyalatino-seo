"""Despliegue directo a Hostinger por FTP (respaldo al Git Deploy, que ha fallado antes)."""
from ftplib import FTP
from pathlib import Path
from . import config


def upload_file(local_path: Path, remote_path: str, ftp: FTP):
    # Crea subdirectorios remotos si hacen falta
    parts = remote_path.split("/")
    if len(parts) > 1:
        current = ""
        for part in parts[:-1]:
            current += part + "/"
            try:
                ftp.mkd(current)
            except Exception:
                pass  # ya existe
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)
    print(f"Subido: {remote_path}")


def deploy(paths: dict[Path, str]):
    """paths: {ruta_local: ruta_remota_relativa_a_public_html}"""
    if not config.FTP_HOST:
        print("Sin credenciales FTP configuradas, se omite el deploy directo.")
        return
    ftp = FTP()
    ftp.connect(config.FTP_HOST, config.FTP_PORT, timeout=30)
    ftp.login(config.FTP_USER, config.FTP_PASS)
    try:
        for local_path, remote_path in paths.items():
            upload_file(local_path, remote_path, ftp)
    finally:
        ftp.quit()

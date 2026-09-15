"""Utilidades para commitear y pushear cambios directo a main (sin PR)."""
import subprocess
from . import config


def run(cmd, check=True):
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(config.REPO_DIR), capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Comando fallo: {' '.join(cmd)}")
    return result


def commit_and_push(message: str, paths: list[str]) -> bool:
    """Agrega, commitea y hace push de los paths indicados. Devuelve True si hubo cambios."""
    run(["git", "add", *paths])
    status = run(["git", "diff", "--cached", "--quiet"], check=False)
    if status.returncode == 0:
        print("Sin cambios que commitear.")
        return False
    run(["git", "commit", "-m", message])
    run(["git", "push", "origin", "main"])
    return True

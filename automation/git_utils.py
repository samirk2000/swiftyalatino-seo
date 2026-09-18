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
    """Agrega, commitea y hace push de los paths indicados. Devuelve True si hubo cambios.

    Es tolerante a que 'origin/main' haya avanzado mientras tanto (ej. cambios hechos
    a mano desde otra maquina): si el push normal es rechazado, hace fetch + rebase
    sobre origin/main y reintenta antes de rendirse.
    """
    run(["git", "add", *paths])
    status = run(["git", "diff", "--cached", "--quiet"], check=False)
    if status.returncode == 0:
        print("Sin cambios que commitear.")
        return False
    run(["git", "commit", "-m", message])

    push_result = run(["git", "push", "origin", "main"], check=False)
    if push_result.returncode == 0:
        return True

    print("Push rechazado (probablemente origin/main avanzo). Reintentando con fetch + rebase...")
    run(["git", "fetch", "origin"])
    rebase_result = run(["git", "rebase", "origin/main"], check=False)
    if rebase_result.returncode != 0:
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError(
            "No se pudo rebasear automaticamente sobre origin/main (posible conflicto real). "
            "Revisar manualmente en el servidor."
        )

    run(["git", "push", "origin", "main"])
    return True

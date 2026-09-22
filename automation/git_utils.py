"""Utilidades para commitear y pushear cambios directo a main (sin PR).

Disenado para correr solo en el servidor del bot: tolera que origin/main
avance mientras genera el post, y limpia cambios locales sueltos que
bloquean el rebase (la causa tipica de 'cannot rebase: You have unstaged
changes').
"""
from __future__ import annotations

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


def _existing_paths(paths: list[str]) -> list[str]:
    """Filtra paths que realmente existen en el repo (evita fallar el git add)."""
    existing = []
    for p in paths:
        full = config.REPO_DIR / p
        if full.exists():
            existing.append(p)
        else:
            print(f"Aviso: se omite path inexistente para git add: {p}")
    return existing


def _stash_dirty(message: str = "bot-auto-stash") -> bool:
    """Guarda cambios locales no commiteados para no bloquear rebase/pull.

    Devuelve True si se creo un stash.
    """
    porcelain = run(["git", "status", "--porcelain"], check=False)
    if not (porcelain.stdout or "").strip():
        return False
    print("Hay cambios locales sueltos. Guardando en stash temporal...")
    print(porcelain.stdout)
    result = run(
        ["git", "stash", "push", "-u", "-m", message],
        check=False,
    )
    return result.returncode == 0


def _drop_bot_stashes() -> None:
    """Tira stashes creados por el bot. No los reaplicamos: suelen ser basura
    (logs, .pyc, ediciones a medias) que no deben volver a ensuciar el tree.
    """
    list_result = run(["git", "stash", "list"], check=False)
    stash_out = list_result.stdout or ""
    # Droppea de arriba hacia abajo mientras haya stashes del bot
    while "bot-auto-stash" in stash_out:
        run(["git", "stash", "drop"], check=False)
        list_result = run(["git", "stash", "list"], check=False)
        stash_out = list_result.stdout or ""


def commit_and_push(message: str, paths: list[str]) -> bool:
    """Agrega, commitea y hace push de los paths indicados. Devuelve True si hubo cambios.

    Flujo robusto (no destruye los archivos recien escritos del post):
    1. git add solo de paths existentes.
    2. stash --keep-index -u de cualquier otra suciedad local.
    3. commit.
    4. push; si se rechaza: stash residual + fetch + rebase + push.
    5. tira stashes del bot (no reaplicar basura).
    """
    existing = _existing_paths(paths)
    if not existing:
        print("Sin paths existentes que commitear.")
        return False

    run(["git", "add", "--", *existing])

    # Aparta todo lo que NO esta en el index (suciedad ajena al commit)
    unstaged = run(["git", "diff", "--quiet"], check=False)
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], check=False)
    if unstaged.returncode != 0 or (untracked.stdout or "").strip():
        print("Apartando cambios locales ajenos al commit (stash --keep-index -u)...")
        run(
            ["git", "stash", "push", "--keep-index", "-u", "-m", "bot-auto-stash"],
            check=False,
        )

    cached = run(["git", "diff", "--cached", "--quiet"], check=False)
    if cached.returncode == 0:
        print("Sin cambios que commitear.")
        _drop_bot_stashes()
        return False

    run(["git", "commit", "-m", message])

    push_result = run(["git", "push", "origin", "main"], check=False)
    if push_result.returncode == 0:
        _drop_bot_stashes()
        return True

    print("Push rechazado (origin/main avanzo). Reintentando con fetch + rebase...")
    run(["git", "fetch", "origin"])

    # Cualquier suciedad residual bloquearia el rebase (el bug original del log)
    _stash_dirty("bot-auto-stash-before-rebase")

    rebase_result = run(["git", "rebase", "origin/main"], check=False)
    if rebase_result.returncode != 0:
        run(["git", "rebase", "--abort"], check=False)
        raise RuntimeError(
            "No se pudo rebasear automaticamente sobre origin/main (posible conflicto real). "
            "Revisar manualmente en el servidor."
        )

    push2 = run(["git", "push", "origin", "main"], check=False)
    if push2.returncode != 0:
        raise RuntimeError(
            "Rebase OK pero el push final fallo. Revisar permisos/remote en el servidor."
        )

    _drop_bot_stashes()
    return True


def clean_working_tree() -> None:
    """Mantenimiento: deja el repo del bot limpio sobre origin/main.

    Usar desde SSH o el dashboard cuando el working tree quede sucio
    y bloquee las corridas automaticas.
    """
    run(["git", "fetch", "origin"])
    _stash_dirty("bot-auto-stash-before-clean")
    run(["git", "checkout", "main"], check=False)
    run(["git", "reset", "--hard", "origin/main"])
    run(["git", "clean", "-fd"], check=False)
    _drop_bot_stashes()
    print("Working tree limpio sobre origin/main.")

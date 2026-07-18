"""Entry point and CLI.

    tuistore                     launch the store
    tuistore installed           list what tuistore installed
    tuistore update              update tuistore itself
    tuistore update installed    update every tool tuistore installed
    tuistore refetch catalog     pull the latest catalog
    tuistore --doctor            show what your machine looks like
    tuistore --version
"""

from __future__ import annotations

import shutil
import subprocess
import sys


def _run(cmd: str) -> int:
    """Run a shell command, streaming its output to the terminal."""
    print(f"$ {cmd}")
    return subprocess.run(["/bin/sh", "-lc", cmd]).returncode


def _update_self() -> int:
    if shutil.which("uv"):
        code = _run("uv tool upgrade tuistore")
        if code == 0:
            return 0
        # maybe installed straight from git — force a fresh pull
        return _run("uv tool install --force git+https://github.com/Gheat1/tuistore")
    if shutil.which("pipx"):
        return _run("pipx upgrade tuistore")
    print("couldn't find uv or pipx — reinstall with:\n"
          "  uv tool install --force git+https://github.com/Gheat1/tuistore")
    return 1


def _update_installed() -> int:
    from .installed import load_ledger, update_command
    ledger = load_ledger()
    if not ledger:
        print("nothing installed through tuistore yet.")
        return 0
    updatable = [(r["name"], update_command(r)) for r in ledger.values()]
    updatable = [(n, c) for n, c in updatable if c]
    if not updatable:
        print("none of the installed tools have a known update command.")
        return 0
    print(f"updating {len(updatable)} tool(s)…\n")
    failed = 0
    for name, cmd in updatable:
        print(f"── {name} ──")
        if _run(cmd) != 0:
            failed += 1
        print()
    print(f"done — {len(updatable) - failed} ok, {failed} failed")
    return 1 if failed else 0


def _refetch_catalog() -> int:
    from . import catalog
    print("fetching latest catalog…")
    ok, msg = catalog.refetch()
    print(("✓ " if ok else "✗ ") + msg)
    return 0 if ok else 1


def _list_installed() -> int:
    from .installed import load_ledger
    ledger = load_ledger()
    if not ledger:
        print("nothing installed through tuistore yet.")
        return 0
    print(f"{len(ledger)} tool(s) installed via tuistore:\n")
    for slug, r in sorted(ledger.items(), key=lambda kv: kv[1]["name"].lower()):
        print(f"  {r['name']:<22} {r.get('kind',''):<8} {r.get('at','')}  ({slug})")
    return 0


def main() -> None:
    argv = sys.argv[1:]

    if not argv:
        from .app import main as run
        run()
        return

    a0 = argv[0].lower()
    a1 = argv[1].lower() if len(argv) > 1 else ""

    if a0 in ("--version", "-v"):
        from . import __version__
        print(f"tuistore {__version__}")
    elif a0 == "--doctor":
        from .platform import detect
        e = detect()
        print(f"tuistore doctor — {e.label}")
        print(f"  package managers: {' '.join(sorted(e.tools)) or '(none found)'}")
    elif a0 in ("update", "upgrade"):
        if a1 in ("installed", "tools", "all"):
            sys.exit(_update_installed())
        if a0 == "upgrade":                 # `tuistore upgrade` == installed
            sys.exit(_update_installed())
        sys.exit(_update_self())            # `tuistore update` == the app itself
    elif a0 in ("update-installed", "update_installed"):
        sys.exit(_update_installed())
    elif a0 in ("refetch", "refresh", "catalog", "refetch-catalog"):
        sys.exit(_refetch_catalog())
    elif a0 in ("installed", "list", "ls"):
        sys.exit(_list_installed())
    elif a0 in ("-h", "--help", "help"):
        print(__doc__)
    else:
        print(f"tuistore: unknown command '{argv[0]}'\n")
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

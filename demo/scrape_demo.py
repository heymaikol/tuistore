"""Demo: what extract_methods() scrapes from a README as 'install methods'.

Feeds real README excerpts (yq, Backlog.md) to the scraper and prints the
methods it would offer as verified installers. Junk — container usage
examples, prose-prefixed lines, ungated arch wrappers — is flagged in red.
Run against the buggy and fixed trees to see the difference.
"""
import sys

from tuistore.scrape import extract_methods

R = "\033[31m"  # red
G = "\033[32m"  # green
D = "\033[2m"   # dim
Z = "\033[0m"

# real excerpts from the projects' READMEs
YQ = """
# yq
```bash
brew install yq
snap install yq
docker run --rm -v "${PWD}":/workdir mikefarah/yq '.a.b[0].c' file.yaml
podman run --rm -v "${PWD}":/workdir mikefarah/yq '.a.b[0].c' file.yaml
arch -arm64 brew install yq
```
"""

BACKLOG = """
# Backlog.md
```bash
npm i -g backlog.md
or: bun add -g backlog.md
```
"""

CASES = [
    ("yq  ·  github.com/mikefarah/yq", "https://github.com/mikefarah/yq", YQ),
    ("Backlog.md  ·  github.com/MrLesk/Backlog.md",
     "https://github.com/MrLesk/Backlog.md", BACKLOG),
]


def is_junk(m) -> bool:
    """A method that does NOT persistently install the tool on this machine."""
    if m.kind in ("docker", "podman"):
        return True  # `run`/`pull` — usage, not install
    first = (m.command.split() or [""])[0].rstrip(":,").lower()
    if first in ("or", "alias", "e.g.", "note", "alternatively"):
        return True  # prose, not a command
    if m.command.lstrip().startswith("arch -") and not m.os:
        return True  # macOS-only wrapper offered everywhere
    return False


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else ""
    print(f"\n  {label}\n")
    bad = 0
    for title, url, readme in CASES:
        print(f"  {D}{title}{Z}")
        for m in extract_methods(readme, url):
            if is_junk(m):
                bad += 1
                print(f"    {R}✗ {m.command}{Z}  {R}← not an install{Z}")
            else:
                gate = f"  {D}[{','.join(m.os)}]{Z}" if m.os else ""
                print(f"    {G}✓ {m.command}{Z}{gate}")
        print()
    verdict = (f"{R}{bad} usage/prose lines shipped as installers{Z}" if bad
               else f"{G}0 junk methods — only real installers{Z}")
    print(f"  => {verdict}\n")


if __name__ == "__main__":
    main()

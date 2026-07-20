"""Guards against the AUR PKGBUILD silently depending on network access.

package() vendors tuistore into a private venv via `uv pip install`. If that
install isn't pinned to files already listed in source[]/sha256sums[] (via
--no-index/--find-links), makepkg's integrity/offline guarantees are a lie:
the build reaches out to PyPI for tuistore's Python dependencies (textual,
httpx, ricekit, and their transitive closure) at package-build time, which
hard-fails in a clean chroot build or any network-isolated CI/build host.

These tests parse the PKGBUILD text directly (no bash execution, no
makepkg/network needed) so they run anywhere `unittest discover` does.
"""

import re
import unittest
from pathlib import Path

PKGBUILD_PATH = Path(__file__).resolve().parent.parent / "packaging" / "aur" / "PKGBUILD"


def _read_pkgbuild() -> str:
    return PKGBUILD_PATH.read_text()


def _strip_comments(text: str) -> str:
    """Drop `# ...` comment text so it can't hide a stray `(`/`)` from the
    array-boundary scan below. None of this PKGBUILD's quoted values (source
    URLs, filenames, the pkgdesc string) contain a literal '#', so a plain
    per-line truncation at the first '#' is safe here.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _bash_array(text: str, name: str) -> list[str]:
    """Pull the raw entries out of a `name=(...)` bash array in PKGBUILD text.

    Handles both the single-line form (`name=("foo")`) and the multi-line
    form (`name=(\n    "foo"\n    "bar"\n)`) — entries here never contain a
    literal `)`, so stopping at the first closing paren is safe either way,
    as long as comments (which can legitimately contain parens) are removed
    first.
    """
    text = _strip_comments(text)
    match = re.search(rf"^{re.escape(name)}=\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError(f"could not find {name}=(...) array in PKGBUILD")
    body = match.group(1)
    # entries are quoted strings, one (or more) per line
    return re.findall(r"""(['"])(.*?)\1""", body, re.DOTALL)


def _package_function(text: str) -> str:
    match = re.search(r"^package\(\)\s*\{(.*)\}\s*$", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError("could not find package() function in PKGBUILD")
    return match.group(1)


class PkgbuildOfflineIntegrityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _read_pkgbuild()

    def test_source_and_sha256sums_arrays_are_equal_length(self) -> None:
        sources = _bash_array(self.text, "source")
        sums = _bash_array(self.text, "sha256sums")
        self.assertEqual(
            len(sources),
            len(sums),
            "source[] and sha256sums[] must have one checksum per source entry",
        )
        self.assertGreater(len(sources), 0)

    def test_python_runtime_dependencies_are_vendored_as_pinned_sources(self) -> None:
        # tuistore's direct PyPI dependencies (see pyproject.toml) plus enough
        # of their transitive closure to prove this isn't just the app's own
        # tarball. If package() ever goes back to resolving these from PyPI
        # at build time, this list won't appear in source[] and this fails.
        required_deps = {
            "textual",
            "httpx",
            "ricekit",
            "rich",
            "anyio",
            "certifi",
            "httpcore",
            "idna",
        }
        sources = [entry for _, entry in _bash_array(self.text, "source")]
        source_blob = "\n".join(sources).lower()

        missing = {dep for dep in required_deps if dep.replace("-", "_") not in source_blob.replace("-", "_")}
        self.assertFalse(
            missing,
            f"these runtime dependencies have no pinned source[] entry: {sorted(missing)}",
        )

    def test_package_function_never_installs_from_network(self) -> None:
        package_body = _package_function(self.text)

        install_lines = [
            line
            for line in package_body.splitlines()
            if re.search(r"\buv\s+pip\s+install\b", line)
        ]
        self.assertTrue(install_lines, "package() should install the app via `uv pip install`")

        for line in install_lines:
            self.assertIn(
                "--no-index",
                line,
                f"`uv pip install` in package() must pass --no-index so it can "
                f"never silently reach PyPI at build time, got: {line!r}",
            )
            self.assertIn(
                "--find-links",
                line,
                f"`uv pip install` in package() must pass --find-links pointing "
                f"at the pinned sources, got: {line!r}",
            )


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import platform
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, override

ROOT = Path(__file__).resolve().parent.parent

from sdd1 import environment  # noqa: E402

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdd1 import decoder, errors, models  # noqa: E402
from sdd1.version import VERSION  # noqa: E402

CORPORA = (
    ("vectors", ROOT / "conformance" / "vectors.json"),
    ("corpus", ROOT / "conformance" / "corpus.json"),
)

OLDEST_PYTHON = (3, 12)


class Finding:
    def __init__(self, name: str, ok: bool, detail: str, advice: str | None = None) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.advice = advice

    @property
    def line(self) -> str:
        return f"  {'ok  ' if self.ok else '   !'}  {self.name}: {self.detail}"

    @property
    def report(self) -> str:
        if self.ok or not self.advice:
            return self.line
        return f"{self.line}\n         {self.advice}"

    @override
    def __repr__(self) -> str:
        return f"<Finding {self.name} {'ok' if self.ok else 'not ok'}>"


def _python() -> "Finding":
    return Finding(
        "python",
        sys.version_info[:2] >= OLDEST_PYTHON,
        f"{platform.python_version()} on {platform.system()} {platform.machine()}",
        f"this package needs {OLDEST_PYTHON[0]}.{OLDEST_PYTHON[1]} or newer",
    )


def _package() -> "Finding":
    return Finding("snes-sdd1-python", True, f"version {VERSION}")


def _default_build(name: str) -> Any:
    return models.lookup(name).build()


def _part(name: str, build: Callable[[str], Any]) -> "Finding":
    try:
        chip = build(name)
        chip.reset()
    except Exception as trouble:
        return Finding(
            name,
            False,
            f"{type(trouble).__name__}: {trouble}",
            "this is the part failing to build rather than anything to do with a"
            " corpus; the line above is what it said",
        )
    described = models.lookup(name)
    return Finding(
        name,
        True,
        f"up to {described.planes} bit planes, {described.contexts} contexts,"
        f" model {getattr(chip, 'model', name)},"
        " resets and carries nothing across it",
    )


def _decoder(decompress: Callable[..., Any]) -> "Finding":
    try:
        found = decompress(b"", 0, 8)
    except errors.TruncatedStream:
        return Finding("decoder", True, "refuses a stream that is not there")
    except Exception as trouble:
        return Finding(
            "decoder",
            False,
            f"{type(trouble).__name__}: {trouble}",
            "an empty stream should raise TruncatedStream; this raised something"
            " else, and the line above is what it said",
        )
    return Finding(
        "decoder",
        False,
        f"returned {len(found)} bytes for an empty stream",
        "bytes that came from nowhere are worse than an error, because nothing"
        " downstream can tell them from real ones",
    )


def _corpus(label: str, where: Path | str) -> "Finding":
    try:
        raw = Path(where).read_bytes()
    except OSError as trouble:
        return Finding(
            label,
            False,
            f"could not be read: {trouble}",
            "the recorded cases this package is settled against are missing from conformance/",
        )
    digest = hashlib.sha256(raw).hexdigest()
    try:
        held = json.loads(raw)
    except ValueError as trouble:
        return Finding(
            label,
            False,
            f"is not readable as JSON: {trouble}, sha256 {digest}",
            "the file is here and damaged, which is worse than absent",
        )
    cases = held.get("cases", [])
    source = held.get("reference", "not stated")
    return Finding(label, bool(cases), f"{len(cases)} cases from {source}, sha256 {digest}")


def examine(
    build: Callable[[str], Any] = _default_build,
    corpora: Sequence[tuple[str, Path]] = CORPORA,
    decompress: Callable[..., Any] = decoder.decompress,
) -> list["Finding"]:
    found = [_python(), _package()]
    found.extend(_part(name, build) for name in sorted(models.MODELS))
    found.append(_decoder(decompress))
    found.extend(_corpus(label, where) for label, where in corpora)
    return found


def report(found: list["Finding"]) -> list[str]:
    unwell = [one for one in found if not one.ok]
    lines = [f"sdd1 {VERSION} on {platform.python_version()}, {platform.system()}", ""]
    lines.append("  the machine")
    lines.extend(environment.lines(ROOT))
    lines.append("")
    lines.append("  this package")
    lines.extend(one.report for one in found)
    lines.append("")
    if unwell:
        lines.append(f"  {len(unwell)} of {len(found)} checks did not pass")
    else:
        lines.append(f"  {len(found)} checks, nothing to report")
    return lines


def main(
    argv: Sequence[str] = (),
    examine: Callable[..., list["Finding"]] = examine,
    say: Callable[[str], None] = print,
) -> int:
    found = examine()
    for line in report(found):
        say(line)
    return 1 if any(not one.ok for one in found) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

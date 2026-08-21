"""Look at this machine and say what is actually here, so a report can be believed.

What goes wrong with this package is rarely a defect in it. It is a corpus that
is not the corpus everybody else has, a Python too old to run it, or a stream
that is not the stream the reporter thinks it is. All of those look the same from
outside: the bytes disagree.

So this looks, and prints what it found in a form that can be pasted into an
issue as it stands.

Two rules shape it, and they are the whole point.

Nothing is hidden. A check that fails says what it saw, and a check that itself
throws is caught and reported as what it threw, named by its type. Swallowing
either would leave a report that says everything is fine on a machine where
something is not, which is worse than no report.

Nothing is inferred. Every line is something looked at on this machine just now:
the version installed, the digest of the file present, whether the decoder
actually refused what it should refuse.
"""

import hashlib
import json
import platform
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, override

from . import decoder, models
from .version import VERSION

ROOT = Path(__file__).resolve().parent.parent

CORPORA = (
    ("vectors", ROOT / "conformance" / "vectors.json"),
    ("corpus", ROOT / "conformance" / "corpus.json"),
)

OLDEST_PYTHON = (3, 12)


class Finding:
    """One thing that was looked at, and what was there."""

    def __init__(self, name: str, ok: bool, detail: str, advice: str | None = None) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.advice = advice

    @property
    def line(self) -> str:
        """The one-line form, which is what a reader scans."""
        return f"  {'ok  ' if self.ok else '   !'}  {self.name}: {self.detail}"

    @property
    def report(self) -> str:
        """The same, with what to do about it when there is something to do."""
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
    """The project, named after the repository rather than the import.

    The part this covers is also called sdd1, and two lines with one name in a
    report is a line somebody misreads.
    """
    return Finding("snes-sdd1-python", True, f"version {VERSION}")


def _default_build(name: str) -> Any:
    return models.describe(name).build()


def _part(name: str, build: Callable[[str], Any]) -> "Finding":
    """Whether that part builds, saying exactly what stopped it if not."""
    try:
        chip = build(name)
    except Exception as trouble:
        return Finding(
            name,
            False,
            f"{type(trouble).__name__}: {trouble}",
            "this is the part failing to build rather than anything to do with a"
            " corpus; the line above is what it said",
        )
    described = models.describe(name)
    return Finding(
        name,
        True,
        f"up to {described.planes} bit planes, {described.contexts} contexts,"
        f" model {getattr(chip, 'model', name)}",
    )


def _decoder(decompress: Callable[..., Any]) -> "Finding":
    """That the decoder refuses what it must refuse, rather than inventing bytes.

    A decompressor that returns something for every input is the failure mode
    that hurts, because nothing downstream can tell invented bytes from real
    ones. Asking for eight bytes out of an empty stream is the cheapest way to
    see which kind is installed here, and it needs nobody's artwork to do it.
    """
    try:
        found = decompress(b"", 0, 8)
    except decoder.TruncatedStream:
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
    """One corpus that is here, which is what settles a disagreement about bytes.

    Two people running the same part against different corpora will disagree
    forever and neither will be wrong. The digest ends that in one glance rather
    than after a round trip.
    """
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
    """Everything worth looking at on this machine, in the order a reader wants it."""
    found = [_python(), _package()]
    found.extend(_part(name, build) for name in sorted(models.MODELS))
    found.append(_decoder(decompress))
    found.extend(_corpus(label, where) for label, where in corpora)
    return found


def report(found: list["Finding"]) -> list[str]:
    """The lines a person pastes into an issue."""
    unwell = [one for one in found if not one.ok]
    lines = [f"sdd1 {VERSION} on {platform.python_version()}, {platform.system()}", ""]
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

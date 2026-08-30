"""The one seam: a single entry point whose subcommands write JSON to stdout.

Each subcommand composes the packages that do the work. The ones not built yet
are registered here and refuse at the point of use — the surface is the
contract, and it was fixed before the implementations arrived.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field

from brotato_coaching.savefile import SaveUnavailable, read_progress


@dataclass(frozen=True)
class _Flag:
    name: str
    help: str


@dataclass(frozen=True)
class _Subcommand:
    help: str
    flags: tuple[_Flag, ...] = field(default_factory=tuple)


_SUBCOMMANDS: dict[str, _Subcommand] = {
    "extract": _Subcommand(
        help="extract character modifiers, weapon stats and item effects from the installed game",
    ),
    "progress": _Subcommand(
        help="report progress per character, deaths, purchases and lifetime totals from the save data",
    ),
    "runs": _Subcommand(
        help="read the snapshots captured for a run",
    ),
    "watch": _Subcommand(
        help="capture snapshots of live run state while a run is in progress",
        flags=(
            _Flag(
                name="--once",
                help="take at most one snapshot and exit, rather than watching",
            ),
        ),
    ),
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brotato-coaching",
        description="Read what Brotato writes to disk: save data, game data, and captured runs.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    for name, subcommand in _SUBCOMMANDS.items():
        subparser = subparsers.add_parser(
            name, help=subcommand.help, description=subcommand.help
        )
        subparser.set_defaults(subcommand=name)
        for flag in subcommand.flags:
            subparser.add_argument(flag.name, action="store_true", help=flag.help)
    return parser


def _progress() -> int:
    """Report the save as JSON.

    The ids in `deaths` and `purchases` come out raw. Resolving them to names
    is the join between `savefile` and `gamedata`, and it belongs here — but
    `gamedata` does not exist yet, so for now raw is all there is.
    """
    try:
        report = read_progress()
    except SaveUnavailable as unavailable:
        print(f"brotato-coaching: {unavailable}", file=sys.stderr)
        return 1
    print(json.dumps(report.as_json_object(), indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    if arguments.subcommand == "progress":
        return _progress()
    print(
        f"brotato-coaching: {arguments.subcommand} is not implemented yet",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

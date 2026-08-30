"""The one seam: a single entry point whose subcommands write JSON to stdout.

Each subcommand composes the packages that do the work. The ones not built yet
are registered here and refuse at the point of use — the surface is the
contract, and it is fixed before the implementations arrive.
"""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from brotato_coaching.gamedata import (
    UNKNOWN_VERSION,
    InstallNotFound,
    extract,
    find_install,
)

DEFAULT_DATA_DIRECTORY = Path("data")


@dataclass(frozen=True)
class _Flag:
    name: str
    help: str
    takes_value: bool = False
    metavar: str | None = None
    default: str | None = None


@dataclass(frozen=True)
class _Subcommand:
    help: str
    flags: tuple[_Flag, ...] = field(default_factory=tuple)


_SUBCOMMANDS: dict[str, _Subcommand] = {
    "extract": _Subcommand(
        help="extract character modifiers, weapon stats and item effects from the installed game",
        flags=(
            _Flag(
                name="--destination",
                help="directory to write the JSON into",
                takes_value=True,
                metavar="DIRECTORY",
                default=str(DEFAULT_DATA_DIRECTORY),
            ),
        ),
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
            if not flag.takes_value:
                subparser.add_argument(flag.name, action="store_true", help=flag.help)
            else:
                subparser.add_argument(
                    flag.name,
                    metavar=flag.metavar,
                    default=flag.default,
                    help=flag.help,
                )
    return parser


def _extract(arguments: argparse.Namespace) -> int:
    try:
        install = find_install()
    except InstallNotFound as error:
        print(f"brotato-coaching: {error}", file=sys.stderr)
        return 1
    extraction = extract(install, Path(arguments.destination))
    if extraction.version == UNKNOWN_VERSION:
        print(
            "brotato-coaching: the install would not say which patch it is; "
            "the extracted data is not patch-stamped",
            file=sys.stderr,
        )
    print(
        json.dumps(
            {
                "game_version": extraction.version,
                "directory": str(extraction.directory),
                "files": [file.name for file in extraction.files],
                "counts": extraction.counts,
                "sources": list(extraction.sources),
            },
            indent=2,
        )
    )
    return 0


_HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {"extract": _extract}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    handler = _HANDLERS.get(arguments.subcommand)
    if handler is None:
        print(
            f"brotato-coaching: {arguments.subcommand} is not implemented yet",
            file=sys.stderr,
        )
        return 1
    return handler(arguments)


if __name__ == "__main__":
    sys.exit(main())

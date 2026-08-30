"""The one seam: a single entry point whose subcommands write JSON to stdout.

Each subcommand composes the packages that do the work. None is built yet, so
each one is registered here and refuses at the point of use — the surface is
the contract, and it is fixed before the implementations arrive.
"""

import argparse
import sys
from collections.abc import Sequence

_SUBCOMMANDS: dict[str, str] = {
    "extract": "extract character modifiers, weapon stats and item effects from the installed game",
    "progress": "report progress per character, deaths, purchases and lifetime totals from the save data",
    "runs": "read the snapshots captured for a run",
    "watch": "capture snapshots of live run state while a run is in progress",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brotato-coaching",
        description="Read what Brotato writes to disk: save data, game data, and captured runs.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    for name, help_text in _SUBCOMMANDS.items():
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
        subparser.set_defaults(subcommand=name)
        if name == "watch":
            subparser.add_argument(
                "--once",
                action="store_true",
                help="take at most one snapshot and exit, rather than watching",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    raise SystemExit(f"brotato-coaching: {arguments.subcommand} is not implemented yet")


if __name__ == "__main__":
    sys.exit(main())

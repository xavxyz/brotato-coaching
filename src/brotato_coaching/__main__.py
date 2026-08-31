"""The one seam: a single entry point whose subcommands write JSON to stdout.

Each subcommand composes the packages that do the work. Any not built yet are
registered here and refuse at the point of use — the surface is the contract,
and it was fixed before the implementations arrived.

A subcommand exits non-zero only when it could not do what it was asked. States
worth reporting — no run in progress, nothing captured, no watcher running — are
JSON on stdout and an exit code of zero, because reporting them *is* the job.
"""

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brotato_coaching.gamedata import (
    UNKNOWN_VERSION,
    InstallNotFound,
    extract,
    find_install,
    read_names,
)
from brotato_coaching.savefile import SaveUnavailable, read_progress

from . import _paths
from .runlog import AlreadyWatching, RunLog, UnknownRun



@dataclass(frozen=True)
class _Argument:
    name: str
    help: str
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _Subcommand:
    help: str
    handler: Callable[[argparse.Namespace], int] | None = None
    arguments: tuple[_Argument, ...] = field(default_factory=tuple)
    exclusive: bool = False


def _run_log() -> RunLog:
    return RunLog(
        live_state_path=_paths.live_run_state_path(),
        runs_directory=_paths.runs_directory(),
        poll_interval=_paths.poll_interval(),
    )


def _emit(payload: object, *, streaming: bool = False) -> int:
    print(json.dumps(payload, indent=None if streaming else 2), flush=True)
    return 0


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


def _progress(_arguments: argparse.Namespace) -> int:
    """Report the save as JSON, with ids named where the game data can name them.

    This is the join: `savefile` supplies the ids, `gamedata` owns the hash that
    turns them back into names, and neither knows about the other. When nothing
    has been extracted the book is empty and the ids stay raw — a report of
    integers still answers most of the questions asked of it.
    """
    try:
        report = read_progress()
    except SaveUnavailable as unavailable:
        print(f"brotato-coaching: {unavailable}", file=sys.stderr)
        return 1
    names = read_names(_paths.data_directory())
    if not names:
        print(
            "brotato-coaching: no extracted game data, so ids are reported raw; "
            "`brotato-coaching extract` gives them names",
            file=sys.stderr,
        )
    print(json.dumps(report.as_json_object(names.name_for), indent=2))
    return 0


def _watch(arguments: argparse.Namespace) -> int:
    """No flag means watch until stopped; each flag names one `RunLog` method."""
    run_log = _run_log()
    one_shot = {
        "once": run_log.capture_once,
        "start": run_log.start_watcher,
        "stop": run_log.stop_watcher,
        "status": run_log.watcher_status,
    }
    for flag, action in one_shot.items():
        if getattr(arguments, flag):
            return _emit(action())
    try:
        for event in run_log.watch():
            _emit(event, streaming=True)
    except AlreadyWatching as already_watching:
        return _emit(
            {
                "watching": False,
                "reason": "already-running",
                "pid": already_watching.pid,
            }
        )
    return 0


def _runs(arguments: argparse.Namespace) -> int:
    run_log = _run_log()
    if arguments.run_id is None:
        return _emit(run_log.runs())
    try:
        return _emit(run_log.snapshots(arguments.run_id))
    except UnknownRun:
        print(
            f"brotato-coaching: no run captured with id {arguments.run_id!r}; "
            "`brotato-coaching runs` lists the ones there are",
            file=sys.stderr,
        )
        return 1


_SUBCOMMANDS: dict[str, _Subcommand] = {
    "extract": _Subcommand(
        help="extract character modifiers, weapon stats and item effects from the installed game",
        handler=_extract,
        arguments=(
            _Argument(
                name="--destination",
                help="directory to write the JSON into",
                options={
                    "metavar": "DIRECTORY",
                    # The same directory `progress` resolves names from, so
                    # extracting and reading cannot drift apart.
                    "default": str(_paths.data_directory()),
                },
            ),
        ),
    ),
    "progress": _Subcommand(
        help="report progress per character, deaths, purchases and lifetime totals from the save data",
        handler=_progress,
    ),
    "runs": _Subcommand(
        help="list captured runs, or read the snapshots captured for one run",
        handler=_runs,
        arguments=(
            _Argument(
                name="run_id",
                help="a run id from `runs`; omit to list every captured run",
                options={"nargs": "?", "default": None},
            ),
        ),
    ),
    "watch": _Subcommand(
        help="capture snapshots of live run state while a run is in progress",
        handler=_watch,
        exclusive=True,
        arguments=(
            _Argument(
                name="--once",
                help="make a single capture decision and exit, rather than watching",
                options={"action": "store_true"},
            ),
            _Argument(
                name="--start",
                help="start the watcher in the background and return",
                options={"action": "store_true"},
            ),
            _Argument(
                name="--stop",
                help="stop the background watcher and report the session it captured",
                options={"action": "store_true"},
            ),
            _Argument(
                name="--status",
                help="report whether the watcher is running and what it has captured",
                options={"action": "store_true"},
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
        subparser.set_defaults(subcommand=name, handler=subcommand.handler)
        target = (
            subparser.add_mutually_exclusive_group()
            if subcommand.exclusive
            else subparser
        )
        for argument in subcommand.arguments:
            target.add_argument(argument.name, help=argument.help, **argument.options)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    if arguments.handler is None:
        print(
            f"brotato-coaching: {arguments.subcommand} is not implemented yet",
            file=sys.stderr,
        )
        return 1
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())

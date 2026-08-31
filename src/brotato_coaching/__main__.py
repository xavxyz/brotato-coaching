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
    read_catalog,
    read_names,
)
from brotato_coaching.prep import PrepDrills, PrepRefused
from brotato_coaching.savefile import (
    SaveDirectoryUnavailable,
    SaveUnavailable,
    read_progress,
    save_directory,
    save_file,
)

from . import _settings
from .runlog import AlreadyWatching, RunLog, UnknownRun


@dataclass(frozen=True)
class _Argument:
    """One flag or positional, and whether it rules the other modes out.

    `exclusive` is per-argument rather than per-subcommand because `prep` mixes
    the two: `--reveal` and `--history` are modes and cannot be combined, while
    `--primary-stat` is a value one of those modes takes.
    """

    name: str
    help: str
    options: Mapping[str, Any] = field(default_factory=dict)
    exclusive: bool = False


@dataclass(frozen=True)
class _Subcommand:
    help: str
    handler: Callable[[argparse.Namespace], int] | None = None
    arguments: tuple[_Argument, ...] = field(default_factory=tuple)


def _run_log() -> RunLog:
    """The one way to build a `RunLog`: `runs/` and how often to look at it.

    Nothing here asks where the game keeps its files. That question is asked
    later, and only by the commands whose job needs the answer.
    """
    return RunLog(
        runs_directory=_settings.runs_directory(),
        poll_interval=_settings.poll_interval(),
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
        report = read_progress(save_file())
    except SaveUnavailable as unavailable:
        print(f"brotato-coaching: {unavailable}", file=sys.stderr)
        return 1
    names = read_names(_settings.data_directory())
    if not names:
        print(
            "brotato-coaching: no extracted game data, so ids are reported raw; "
            "`brotato-coaching extract` gives them names",
            file=sys.stderr,
        )
    print(json.dumps(report.as_json_object(names.name_for), indent=2))
    return 0


def _watch(arguments: argparse.Namespace) -> int:
    """No flag means watch until stopped; each flag names one `RunLog` method.

    Where the player's files are is resolved lazily, and only for the commands
    that read them. `--stop` and `--status` speak about a watcher and `runs/`,
    never about the game, so an unmounted or moved save root must not be able to
    strand a running watcher beyond inspecting or stopping it.

    Not finding the directory is reported, not raised: the watcher has nothing to
    say yet, which is a state and not a failure to do the job asked.
    """
    run_log = _run_log()
    if arguments.stop:
        return _emit(run_log.stop_watcher())
    if arguments.status:
        return _emit(run_log.watcher_status())
    try:
        # `--start` does not strictly need the path — the detached child runs
        # discovery for itself — but resolving it here is a deliberate pre-flight,
        # so a misconfigured save root reads as the real message rather than as a
        # child that never claimed the session and a handshake timeout.
        directory = save_directory()
    except SaveDirectoryUnavailable as unavailable:
        # `reason` stays a token, as everywhere else in this document; the
        # sentence written for the player travels beside it.
        return _emit(
            {
                "watching": False,
                "reason": "no-save-directory",
                "detail": str(unavailable),
            }
        )
    if arguments.once:
        return _emit(run_log.capture_once(directory))
    if arguments.start:
        return _emit(run_log.start_watcher())
    try:
        for event in run_log.watch(directory):
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


def _prep(arguments: argparse.Namespace) -> int:
    """The drill's five modes, all of them one `PrepDrills` away.

    The join this handler performs is the same one `progress` performs, for the
    same reason: the save names the characters the player has cleared, the
    extracted data describes them, and neither package knows about the other.
    """
    drills = PrepDrills(_settings.drills_directory())
    try:
        mode = _mode(arguments)
        _nothing_ignored(arguments, mode)
        if mode == "history":
            return _emit(drills.history())
        if mode == "commit":
            return _emit(drills.commit(arguments.commit, **_predictions(arguments)))
        if mode == "reveal":
            return _emit(drills.reveal(arguments.reveal))
        if mode == "settle":
            if arguments.actual_wave is None:
                raise PrepRefused(
                    "--settle needs --actual-wave: the wave the run actually broke at"
                )
            return _emit(
                drills.settle(arguments.settle, actual_wave=arguments.actual_wave)
            )
        catalog = read_catalog(_settings.data_directory())
        # The save is read only when it has something to decide. Naming a
        # character is always allowed to work, including where there is no save.
        history = {} if arguments.character else _player()
        return _emit(
            drills.open_drill(
                catalog, character_id=arguments.character, **history
            )
        )
    except PrepRefused as refused:
        print(f"brotato-coaching: {refused}", file=sys.stderr)
        return 1


# Which values each mode of `prep` reads. Anything supplied that its mode does
# not read is refused rather than dropped: `prep character_mage --history`
# quietly printing history and forgetting the character is exactly the sort of
# confidently wrong answer this command exists not to give.
_MODE_VALUES = {
    "open": ("character",),
    "commit": ("primary_stat", "secondary_stat", "weapon_class", "weakest_wave"),
    "reveal": (),
    "settle": ("actual_wave",),
    "history": (),
}


def _mode(arguments: argparse.Namespace) -> str:
    """Which of `prep`'s modes was asked for. No flag means opening a drill."""
    return next(
        (name for name in _MODE_VALUES if name != "open" and getattr(arguments, name)),
        "open",
    )


def _nothing_ignored(arguments: argparse.Namespace, mode: str) -> None:
    supplied = {
        name
        for names in _MODE_VALUES.values()
        for name in names
        if getattr(arguments, name) is not None
    }
    ignored = sorted(supplied - set(_MODE_VALUES[mode]))
    if ignored:
        named = ", ".join(
            "a character" if name == "character" else f"--{name.replace('_', '-')}"
            for name in ignored
        )
        doing = "opening a drill" if mode == "open" else f"--{mode}"
        raise PrepRefused(f"{doing} does not read {named}, so it will not ignore it")


def _predictions(arguments: argparse.Namespace) -> dict[str, Any]:
    """The four predictions, or a refusal naming the ones that are missing.

    All four or none: a drill that let three through would be a drill the player
    could hedge on by leaving the one they are least sure of until after the
    reveal, which is the exact habit it exists to break.
    """
    committed = {
        "primary_stat": arguments.primary_stat,
        "secondary_stat": arguments.secondary_stat,
        "weapon_class": arguments.weapon_class,
        "weakest_wave": arguments.weakest_wave,
    }
    missing = [name for name, value in committed.items() if value is None]
    if missing:
        flags = ", ".join(f"--{name.replace('_', '-')}" for name in missing)
        raise PrepRefused(
            f"all four predictions are committed together; still missing: {flags}"
        )
    return committed


def _player() -> dict[str, Any]:
    """What the save says about who the player has already reasoned about.

    A save that cannot be read is not a reason to refuse a drill: without one
    every character is a candidate, which is the right answer on a machine that
    has the game but not this player's progress on it.
    """
    try:
        progress = read_progress(save_file())
    except (SaveUnavailable, SaveDirectoryUnavailable):
        return {}
    names = read_names(_settings.data_directory())
    return {
        "unlocked": {
            name
            for name in (
                names.name_for(identifier)
                for identifier in progress.unlocked_characters
            )
            if name
        },
        "cleared": progress.cleared_characters,
    }


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
                    "default": str(_settings.data_directory()),
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
        arguments=(
            _Argument(
                name="--once",
                help="make a single capture decision and exit, rather than watching",
                options={"action": "store_true"},
                exclusive=True,
            ),
            _Argument(
                name="--start",
                help="start the watcher in the background and return",
                options={"action": "store_true"},
                exclusive=True,
            ),
            _Argument(
                name="--stop",
                help="stop the background watcher and report the session it captured",
                options={"action": "store_true"},
                exclusive=True,
            ),
            _Argument(
                name="--status",
                help="report whether the watcher is running and what it has captured",
                options={"action": "store_true"},
                exclusive=True,
            ),
        ),
    ),
    "prep": _Subcommand(
        help="run the derivation drill: predict a character's plan before being told who it is",
        handler=_prep,
        arguments=(
            _Argument(
                name="character",
                help="a character id such as `character_mage`; omit to be proposed one",
                options={"nargs": "?", "default": None},
            ),
            _Argument(
                name="--commit",
                help="record all four predictions for a drill id, before any reveal",
                options={"metavar": "DRILL_ID", "default": None},
                exclusive=True,
            ),
            _Argument(
                name="--reveal",
                help="name the character and score each committed prediction",
                options={"metavar": "DRILL_ID", "default": None},
                exclusive=True,
            ),
            _Argument(
                name="--settle",
                help="score the wave prediction against the wave a run actually broke at",
                options={"metavar": "DRILL_ID", "default": None},
                exclusive=True,
            ),
            _Argument(
                name="--history",
                help="report the prediction hit rate per dimension across every drill",
                options={"action": "store_true"},
                exclusive=True,
            ),
            # The four predictions, spelled out rather than generated: they are
            # the drill's whole contract, and `PrepDrills.commit` names the same
            # four in its signature, so a fifth cannot be added in one place only.
            _Argument(
                name="--primary-stat",
                help="with --commit: the stat predicted to matter most",
                options={"metavar": "STAT", "default": None},
            ),
            _Argument(
                name="--secondary-stat",
                help="with --commit: the stat predicted to matter next",
                options={"metavar": "STAT", "default": None},
            ),
            _Argument(
                name="--weapon-class",
                help="with --commit: the weapon class predicted to be right",
                options={"metavar": "CLASS", "default": None},
            ),
            _Argument(
                name="--weakest-wave",
                help="with --commit: the wave the build is predicted to be weakest at",
                options={"metavar": "WAVE", "type": int, "default": None},
            ),
            _Argument(
                name="--actual-wave",
                help="with --settle: the wave the run actually broke at",
                options={"metavar": "WAVE", "type": int, "default": None},
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
        modes = None
        for argument in subcommand.arguments:
            if argument.exclusive and modes is None:
                modes = subparser.add_mutually_exclusive_group()
            target = modes if argument.exclusive else subparser
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

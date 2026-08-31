"""Captured runs: taking snapshots of live run state, and reading them back.

The game keeps one run's state in `run_v3_0.json` and erases it when the run
ends. This package copies that state into `runs/` whenever it changes, so a run
outlives the death that ended it. It hides how the change is noticed (polling,
because `fswatch` is not available), how repeats are discarded, where snapshots
are written, and how the background watcher is started, stopped and inspected.

Give `RunLog` the `runs/` to fill. The two methods that read the game,
`capture_once` and `watch`, are handed the player's save directory when they are
called, and compose `run_v3_0.json` onto it themselves; the rest answer from
`runs/` alone, so a run can be reviewed, and a watcher inspected or stopped, on a
machine where no Brotato install can be found. Every method returns the JSON
document the matching CLI subcommand prints.
"""

from ._internal._runlog import RunLog
from ._internal._store import UnknownRun
from ._internal._watcher import AlreadyWatching

__all__ = ["AlreadyWatching", "RunLog", "UnknownRun"]

"""Captured runs: taking snapshots of live run state, and reading them back.

The game keeps one run's state in `run_v3_0.json` and erases it when the run
ends. This package copies that state into `runs/` whenever it changes, so a run
outlives the death that ended it. It hides how the change is noticed (polling,
because `fswatch` is not available), how repeats are discarded, where snapshots
are written, and how the background watcher is started, stopped and inspected.

Give `RunLog` the two paths it works between; every method returns the JSON
document the matching CLI subcommand prints.
"""

from ._internal._runlog import RunLog
from ._internal._store import UnknownRun
from ._internal._watcher import AlreadyWatching

__all__ = ["AlreadyWatching", "RunLog", "UnknownRun"]

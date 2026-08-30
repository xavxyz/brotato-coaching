# Fixtures

## `save/00000000000000000/save_v3_0.json`

A real save, copied verbatim from a real Brotato install, under a **placeholder
Steam ID**. It is the highest-value fixture here: real data, with real edge
cases — 64 characters of which four have ever been cleared, a 15-entry death
histogram, 260 purchase counts.

The redaction is the directory name and nothing else. The save's contents carry
no Steam ID: every string in it is either a `character_*` id or a schema key,
and every id is an integer hash. `tests/test_no_steam_id.py` holds that line,
failing if anything shaped like a Steam ID ever appears in a tracked file.

The directory name matters because save-directory discovery globs for it — a
fixture flat on disk would not exercise the code that finds the save.

"""Turning parsed resources into the three catalogues worth learning from.

The game stores one resource per thing and points between them: a character
names its effects, a weapon names its stats and its upgrade, an effect names its
arguments. Reading a `.tres` gives you one node of that graph; a catalogue is
the graph walked and flattened, so that a character's modifiers are readable
without chasing five files.

Which kind a resource is comes from the GDScript behind it — `character_data.gd`,
`weapon_data.gd`, `item_data.gd` — rather than from where it sits on disk, so
the DLC's characters classify exactly like the base game's.

Names are left as the game's translation keys (`CHARACTER_APPRENTICE`). They are
the stable identifier; resolving them to English is a separate concern, and the
mechanical numbers are what the catalogues exist for.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ._container import Container
from ._tres import Constructed, MalformedResource, Resource, parse_resource

CHARACTER_SCRIPT = "character_data.gd"
WEAPON_SCRIPT = "weapon_data.gd"
ITEM_SCRIPT = "item_data.gd"
SET_SCRIPT = "set_data.gd"

_MAX_EFFECT_DEPTH = 3

# Properties carrying presentation rather than mechanics: textures, scenes,
# sounds, and the cosmetic overlays a character wears.
_NOISE = frozenset(
    {
        "icon",
        "scene",
        "script",
        "item_appearances",
        "shooting_sounds",
        "sounds",
        "hit_sounds",
        "sprite",
        "sprites",
        "particles",
        "sound_db_mod",
    }
)


@dataclass(frozen=True)
class Catalog:
    """Every extracted entity, keyed by the file it will be written to."""

    characters: list[dict[str, Any]]
    weapons: list[dict[str, Any]]
    items: list[dict[str, Any]]


class _Library:
    """Every resource across every container, parsed once and remembered.

    Later containers win on a path collision, which is how the DLC overriding a
    base-game resource behaves in the game itself.
    """

    def __init__(self, containers: dict[str, Container]) -> None:
        self._source_of: dict[str, str] = {}
        self._containers = containers
        self._parsed: dict[str, Resource | None] = {}
        for source, container in containers.items():
            for path in container.paths_ending_with(".tres"):
                self._source_of[path] = source

    def resources(self) -> Iterator[tuple[str, str, Resource]]:
        for path in sorted(self._source_of):
            resource = self.get(path)
            if resource is not None:
                yield path, self._source_of[path], resource

    def source_of(self, path: str) -> str:
        return self._source_of.get(path, "unknown")

    def get(self, path: str) -> Resource | None:
        if path not in self._parsed:
            self._parsed[path] = self._parse(path)
        return self._parsed[path]

    def _parse(self, path: str) -> Resource | None:
        source = self._source_of.get(path)
        if source is None:
            return None
        try:
            return parse_resource(self._containers[source].read_text(path))
        except (MalformedResource, UnicodeDecodeError):
            return None


def build_catalog(containers: dict[str, Container]) -> Catalog:
    """Read every resource in `containers` and sort it into the catalogues."""
    library = _Library(containers)
    characters: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for path, source, resource in library.resources():
        script = resource.script_name
        identifier = resource.properties.get("my_id")
        if not isinstance(identifier, str) or not identifier:
            continue
        if script == CHARACTER_SCRIPT:
            characters.append(_character(identifier, path, source, resource, library))
        elif script == WEAPON_SCRIPT:
            weapons.append(_weapon(identifier, path, source, resource, library))
        elif script == ITEM_SCRIPT and identifier.startswith("item_"):
            items.append(_item(identifier, path, source, resource, library))

    return Catalog(
        characters=sorted(characters, key=_by_id),
        weapons=sorted(weapons, key=_by_id),
        items=sorted(items, key=_by_id),
    )


def _by_id(entity: dict[str, Any]) -> str:
    return str(entity["id"])


def _character(
    identifier: str, path: str, source: str, resource: Resource, library: _Library
) -> dict[str, Any]:
    properties = resource.properties
    return {
        "id": identifier,
        "name_key": properties.get("name"),
        "source": source,
        "resource": path,
        "unlocked_by_default": properties.get("unlocked_by_default"),
        "modifiers": _effects(properties.get("effects"), resource, library),
        "starting_weapons": _referenced_ids(
            properties.get("starting_weapons"), resource, library
        ),
        "starting_items": _referenced_ids(
            properties.get("starting_items"), resource, library
        ),
        "tags": _plain(properties.get("tags")),
        "wanted_tags": _plain(properties.get("wanted_tags")),
        "banned_items": _referenced_ids(
            properties.get("banned_items"), resource, library
        ),
    }


def _weapon(
    identifier: str, path: str, source: str, resource: Resource, library: _Library
) -> dict[str, Any]:
    properties = resource.properties
    stats_resource = _referenced_resource(properties.get("stats"), resource, library)
    return {
        "id": identifier,
        "weapon_id": properties.get("weapon_id"),
        "name_key": properties.get("name"),
        "source": source,
        "resource": path,
        "tier": properties.get("tier"),
        "value": properties.get("value"),
        "class": _weapon_class(stats_resource),
        "sets": _referenced_ids(properties.get("sets"), resource, library),
        "upgrades_into": _first(
            _referenced_ids([properties.get("upgrades_into")], resource, library)
        ),
        "stats": _stats(stats_resource),
        "effects": _effects(properties.get("effects"), resource, library),
    }


def _item(
    identifier: str, path: str, source: str, resource: Resource, library: _Library
) -> dict[str, Any]:
    properties = resource.properties
    return {
        "id": identifier,
        "name_key": properties.get("name"),
        "source": source,
        "resource": path,
        "tier": properties.get("tier"),
        "value": properties.get("value"),
        "max_nb": properties.get("max_nb"),
        "is_cursed": properties.get("is_cursed"),
        "tags": _plain(properties.get("tags")),
        "sets": _referenced_ids(properties.get("sets"), resource, library),
        "effects": _effects(properties.get("effects"), resource, library),
    }


def _weapon_class(stats: Resource | None) -> str | None:
    """`melee_weapon_stats.gd` -> "melee"; the script names the class."""
    if stats is None or stats.script_name is None:
        return None
    name = stats.script_name.removesuffix(".gd").removesuffix("weapon_stats")
    return name.rstrip("_") or "generic"


def _stats(stats: Resource | None) -> dict[str, Any]:
    if stats is None:
        return {}
    return {
        name: _plain(value)
        for name, value in stats.properties.items()
        if name not in _NOISE and _is_plain(value)
    }


def _effects(
    value: Any, resource: Resource, library: _Library, depth: int = 0
) -> list[dict[str, Any]]:
    """Expand a list of effect references into the effects themselves."""
    if not isinstance(value, list) or depth > _MAX_EFFECT_DEPTH:
        return []
    effects: list[dict[str, Any]] = []
    for item in value:
        referenced = _referenced_resource(item, resource, library)
        if referenced is None:
            continue
        effects.append(_effect(referenced, library, depth))
    return effects


def _effect(effect: Resource, library: _Library, depth: int) -> dict[str, Any]:
    kind = (effect.script_name or "").removesuffix(".gd") or None
    described: dict[str, Any] = {"kind": kind}
    for name, value in effect.properties.items():
        if name in _NOISE:
            continue
        if _is_plain(value):
            described[name] = _plain(value)
        elif isinstance(value, list) and depth < _MAX_EFFECT_DEPTH:
            nested = _effects(value, effect, library, depth + 1)
            if nested:
                described[name] = nested
    return described


def _referenced_resource(
    value: Any, resource: Resource, library: _Library
) -> Resource | None:
    path = _referenced_path(value, resource)
    return library.get(path) if path else None


def _referenced_path(value: Any, resource: Resource) -> str | None:
    if not isinstance(value, Constructed) or value.name != "ExtResource":
        return None
    reference = resource.external.get(str(value.arguments[0]))
    return reference.path if reference else None


def _referenced_ids(value: Any, resource: Resource, library: _Library) -> list[str]:
    """Resolve references to the `my_id` of what they point at."""
    if not isinstance(value, list):
        return []
    identifiers: list[str] = []
    for item in value:
        referenced = _referenced_resource(item, resource, library)
        if referenced is None:
            continue
        identifier = referenced.properties.get("my_id")
        if isinstance(identifier, str) and identifier:
            identifiers.append(identifier)
    return identifiers


def _first(identifiers: list[str]) -> str | None:
    return identifiers[0] if identifiers else None


def _is_plain(value: Any) -> bool:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_plain(item) for item in value)
    return False


def _plain(value: Any) -> Any:
    if isinstance(value, list):
        return [_plain(item) for item in value if _is_plain(item)]
    return value if _is_plain(value) else None

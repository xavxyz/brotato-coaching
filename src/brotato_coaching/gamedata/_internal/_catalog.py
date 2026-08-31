"""Turning parsed resources into the three catalogues worth learning from.

The game stores one resource per thing and points between them: a character
names its effects, a weapon names its stats and its upgrade, an effect names its
arguments. Reading a `.tres` gives you one node of that graph; a catalogue is
the graph walked and flattened, so that a character's modifiers are readable
without chasing five files.

Which kind a resource is comes from the GDScript behind it — `character_data.gd`,
`weapon_data.gd`, `item_data.gd` — rather than from where it sits on disk, so
the Abyssal Terrors characters classify exactly like the base game's.

Names are left as the game's translation keys (`CHARACTER_APPRENTICE`). They are
the stable identifier; resolving them to English is a separate concern, and the
mechanical numbers are what the catalogues exist for.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ._container import Container
from ._tres import Constructed, MalformedResource, Resource, parse_resource

CHARACTER_SCRIPT = "character_data.gd"
WEAPON_SCRIPT = "weapon_data.gd"
ITEM_SCRIPT = "item_data.gd"
# An enemy is described twice over: the codex entry the player unlocks carries
# its name and whether it is elite, while `enemy_data.gd` covers the bosses and
# elites the codex has no entry for. The two sets of ids do not overlap.
ENEMY_ITEM_SCRIPT = "ItemEnemy.gd"
ENEMY_SCRIPT = "enemy_data.gd"

_MAX_EFFECT_DEPTH = 3

# Properties carrying presentation rather than mechanics: textures, scenes,
# sounds, and the cosmetic overlays a character wears.
_PRESENTATION = frozenset(
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
    enemies: list[dict[str, Any]]


@dataclass(frozen=True)
class _Node:
    """One resource, with where it came from and the means to follow it on.

    A resource's references are ids that only mean anything alongside the
    resource holding them and the library they resolve against, so the three
    travel together rather than being passed around as a loose trio.
    """

    path: str
    source: str
    resource: Resource
    library: _Library

    @property
    def script(self) -> str | None:
        return self.resource.script_name

    @property
    def identifier(self) -> str | None:
        identifier = self.resource.properties.get("my_id")
        return identifier if isinstance(identifier, str) and identifier else None

    def value(self, name: str) -> Any:
        return self.resource.properties.get(name)

    def follow(self, name: str) -> _Node | None:
        """The resource one property points at, if it points at one."""
        return self._resolve(self.value(name))

    def follow_all(self, name: str) -> list[_Node]:
        """The resources a property's list of references points at."""
        references = self.value(name)
        if not isinstance(references, list):
            return []
        followed = (self._resolve(reference) for reference in references)
        return [node for node in followed if node is not None]

    def identifiers(self, name: str) -> list[str]:
        """Resolve a property's references to the `my_id` of what they name."""
        return [
            node.identifier for node in self.follow_all(name) if node.identifier
        ]

    def effects(self, name: str = "effects", depth: int = 0) -> list[dict[str, Any]]:
        """A property's effect references, expanded into the effects themselves."""
        if depth > _MAX_EFFECT_DEPTH:
            return []
        return [node.as_effect(depth) for node in self.follow_all(name)]

    def as_effect(self, depth: int = 0) -> dict[str, Any]:
        """This resource read as an effect: its kind, then its own values."""
        described: dict[str, Any] = {
            "kind": (self.script or "").removesuffix(".gd") or None
        }
        for name, value in self.resource.properties.items():
            if name in _PRESENTATION:
                continue
            if _is_json_ready(value):
                described[name] = value
            elif isinstance(value, list) and depth < _MAX_EFFECT_DEPTH:
                nested = self.effects(name, depth + 1)
                if nested:
                    described[name] = nested
        return described

    def mechanics(self) -> dict[str, Any]:
        """Every plain value this resource holds, presentation left out."""
        return {
            name: value
            for name, value in self.resource.properties.items()
            if name not in _PRESENTATION and _is_json_ready(value)
        }

    def _resolve(self, reference: Any) -> _Node | None:
        if not isinstance(reference, Constructed) or reference.name != "ExtResource":
            return None
        external = self.resource.external.get(str(reference.arguments[0]))
        return self.library.node(external.path) if external else None


class _Library:
    """Every resource across every container, parsed once and remembered.

    Later containers win on a path collision, so an install's containers are
    read in the order the install lists them.
    """

    def __init__(self, containers: dict[str, Container]) -> None:
        self._containers = containers
        self._source_of: dict[str, str] = {
            path: source
            for source, container in containers.items()
            for path in container.paths_ending_with(".tres")
        }
        self._nodes: dict[str, _Node | None] = {}

    def nodes(self) -> Iterator[_Node]:
        for path in sorted(self._source_of):
            node = self.node(path)
            if node is not None:
                yield node

    def node(self, path: str) -> _Node | None:
        if path not in self._nodes:
            self._nodes[path] = self._read(path)
        return self._nodes[path]

    def _read(self, path: str) -> _Node | None:
        source = self._source_of.get(path)
        if source is None:
            return None
        try:
            resource = parse_resource(self._containers[source].read_text(path))
        except (MalformedResource, UnicodeDecodeError):
            return None
        return _Node(path=path, source=source, resource=resource, library=self)


def build_catalog(containers: dict[str, Container]) -> Catalog:
    """Read every resource in `containers` and sort it into the catalogues."""
    characters: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    enemies: list[dict[str, Any]] = []

    for node in _Library(containers).nodes():
        identifier = node.identifier
        if identifier is None:
            continue
        if node.script == CHARACTER_SCRIPT:
            characters.append(_character(node))
        elif node.script == WEAPON_SCRIPT:
            weapons.append(_weapon(node))
        elif node.script == ITEM_SCRIPT and identifier.startswith("item_"):
            items.append(_item(node))
        elif node.script in (ENEMY_ITEM_SCRIPT, ENEMY_SCRIPT):
            enemies.append(_enemy(node))

    return Catalog(
        characters=sorted(characters, key=_by_id),
        weapons=sorted(weapons, key=_by_id),
        items=sorted(items, key=_by_id),
        enemies=sorted(enemies, key=_by_id),
    )


def _by_id(entity: dict[str, Any]) -> str:
    return str(entity["id"])


def _character(node: _Node) -> dict[str, Any]:
    return {
        **_shared(node),
        "unlocked_by_default": node.value("unlocked_by_default"),
        "modifiers": node.effects(),
        "starting_weapons": node.identifiers("starting_weapons"),
        "starting_items": node.identifiers("starting_items"),
        "tags": _json_ready(node.value("tags")),
        "wanted_tags": _json_ready(node.value("wanted_tags")),
        "banned_items": node.identifiers("banned_items"),
    }


def _weapon(node: _Node) -> dict[str, Any]:
    stats = node.follow("stats")
    upgrade = node.follow("upgrades_into")
    return {
        **_shared(node),
        "weapon_id": node.value("weapon_id"),
        "tier": node.value("tier"),
        "value": node.value("value"),
        "class": _weapon_class(stats),
        "sets": node.identifiers("sets"),
        "upgrades_into": upgrade.identifier if upgrade else None,
        "stats": stats.mechanics() if stats else {},
        "effects": node.effects(),
    }


def _item(node: _Node) -> dict[str, Any]:
    return {
        **_shared(node),
        "tier": node.value("tier"),
        "value": node.value("value"),
        "max_nb": node.value("max_nb"),
        "is_cursed": node.value("is_cursed"),
        "tags": _json_ready(node.value("tags")),
        "sets": node.identifiers("sets"),
        "effects": node.effects(),
    }


def _enemy(node: _Node) -> dict[str, Any]:
    """What kills the player, said plainly enough to read a death histogram by.

    A boss's resource carries only its id and zone, so most fields here come
    back `None` for one. That is the game's own asymmetry, not a gap.
    """
    return {
        **_shared(node),
        "is_boss": node.value("is_boss"),
        "is_elite": node.value("is_elite"),
        "zone_id": node.value("zone_id"),
        "tier": node.value("tier"),
    }


def _shared(node: _Node) -> dict[str, Any]:
    return {
        "id": node.identifier,
        "name_key": node.value("name"),
        "source": node.source,
        "resource": node.path,
    }


def _weapon_class(stats: _Node | None) -> str | None:
    """`melee_weapon_stats.gd` -> "melee"; the script names the class."""
    if stats is None or stats.script is None:
        return None
    name = stats.script.removesuffix(".gd").removesuffix("weapon_stats")
    return name.rstrip("_") or "generic"


def _is_json_ready(value: Any) -> bool:
    """True for what JSON can hold: everything but unresolved references."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_json_ready(item) for item in value)
    return False


def _json_ready(value: Any) -> Any:
    if isinstance(value, list):
        return [item for item in value if _is_json_ready(item)]
    return value if _is_json_ready(value) else None

"""Decoding Godot's text resource format (`.tres`).

Every resource that carries game data in Brotato is text, so this reader covers
the whole of it. A file is a sequence of bracketed sections, each followed by
`key = value` lines:

    [gd_resource type="Resource" load_steps=34 format=2]

    [ext_resource path="res://items/global/effect.gd" type="Script" id=1]

    [resource]
    key = "stat_melee_damage"
    value = 2
    custom_args = [  ]

Values are Godot literals: numbers, strings, booleans, `null`, arrays, dicts,
and constructor calls such as `ExtResource( 1 )` or `Vector2( 0, 1 )`. They are
decoded into plain Python; a constructor becomes a `Constructed`, and it is the
caller's job to decide what an `ExtResource` reference means.
"""

import re
from dataclasses import dataclass
from typing import Any

_SECTION = re.compile(
    r"^\[(?P<kind>gd_resource|ext_resource|sub_resource|resource)(?P<attributes>[^\n]*)\]$",
    re.MULTILINE,
)
_ATTRIBUTE = re.compile(r'(\w+)=("[^"]*"|[^\s\]]+)')
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_/]*")
_NUMBER = re.compile(r"[-+]?(?:\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+|\d+(?:[eE][-+]?\d+)?)")
_PROPERTY = re.compile(r"^(?P<name>[\w/]+) = ", re.MULTILINE)


class MalformedResource(Exception):
    """The text is not a resource this reader understands."""


@dataclass(frozen=True)
class Constructed:
    """A Godot constructor call, kept as its name and its arguments."""

    name: str
    arguments: tuple[Any, ...]


@dataclass(frozen=True)
class ExternalResource:
    """A `[ext_resource]` line: another file this resource points at."""

    id: str
    path: str
    type: str


@dataclass(frozen=True)
class Resource:
    """One parsed `.tres`.

    `properties` are the `[resource]` block's own values. `external` maps an
    `ExtResource` id to the file it names; `script_path` is the `res://` path of
    the GDScript behind the resource, which is how a resource's kind is known —
    `character_data.gd`, `weapon_data.gd`, `effect.gd`, and so on.
    """

    properties: dict[str, Any]
    external: dict[str, ExternalResource]

    @property
    def script_path(self) -> str | None:
        script = self.properties.get("script")
        if isinstance(script, Constructed) and script.name == "ExtResource":
            reference = self.external.get(str(script.arguments[0]))
            return reference.path if reference else None
        return None

    @property
    def script_name(self) -> str | None:
        path = self.script_path
        return path.rsplit("/", 1)[-1] if path else None


def parse_resource(text: str) -> Resource:
    """Parse the text of a `.tres` file. Raises `MalformedResource`."""
    sections = list(_SECTION.finditer(text))
    if not sections:
        raise MalformedResource("no [gd_resource] or [resource] section found")

    properties: dict[str, Any] = {}
    external: dict[str, ExternalResource] = {}

    for index, section in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[section.end() : end]
        attributes = dict(_ATTRIBUTE.findall(section["attributes"]))
        kind = section["kind"]
        if kind == "ext_resource":
            external[_unquote(attributes.get("id", ""))] = ExternalResource(
                id=_unquote(attributes.get("id", "")),
                path=_unquote(attributes.get("path", "")),
                type=_unquote(attributes.get("type", "")),
            )
        elif kind == "resource":
            properties = _parse_body(body)
        # A [sub_resource] section only delimits the one that follows it: its
        # properties belong to the sub-resource, not to the resource itself.

    return Resource(properties=properties, external=external)


def _unquote(value: str) -> str:
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value


def _parse_body(body: str) -> dict[str, Any]:
    """Read `name = value` pairs, where a value may span several lines."""
    properties: dict[str, Any] = {}
    for match in _PROPERTY.finditer(body):
        value, _ = _parse_value(body, match.end())
        properties[match["name"]] = value
    return properties


def _parse_value(text: str, position: int) -> tuple[Any, int]:
    position = _skip_space(text, position)
    if position >= len(text):
        raise MalformedResource("value expected, found end of file")

    character = text[position]
    if character == '"':
        return _parse_string(text, position)
    if character == "[":
        return _parse_sequence(text, position, closing="]")
    if character == "{":
        return _parse_dictionary(text, position)
    for literal, value in (("true", True), ("false", False), ("null", None)):
        if text.startswith(literal, position) and not _continues_word(
            text, position + len(literal)
        ):
            return value, position + len(literal)

    identifier = _IDENTIFIER.match(text, position)
    if identifier and text[identifier.end() :].lstrip().startswith("("):
        opening = text.index("(", identifier.end())
        arguments, end = _parse_sequence(text, opening, closing=")")
        return Constructed(identifier.group(), tuple(arguments)), end

    number = _NUMBER.match(text, position)
    if number:
        raw = number.group()
        is_float = any(character in raw for character in ".eE")
        return (float(raw) if is_float else int(raw)), number.end()

    raise MalformedResource(f"unreadable value at {text[position : position + 40]!r}")


def _parse_string(text: str, position: int) -> tuple[str, int]:
    characters: list[str] = []
    position += 1
    while position < len(text):
        character = text[position]
        if character == "\\":
            characters.append(_ESCAPES.get(text[position + 1], text[position + 1]))
            position += 2
            continue
        if character == '"':
            return "".join(characters), position + 1
        characters.append(character)
        position += 1
    raise MalformedResource("string is never closed")


_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


def _parse_sequence(text: str, position: int, closing: str) -> tuple[list[Any], int]:
    items: list[Any] = []
    position = _skip_space(text, position + 1)
    while position < len(text) and text[position] != closing:
        value, position = _parse_value(text, position)
        items.append(value)
        position = _skip_space(text, position)
        if position < len(text) and text[position] == ",":
            position = _skip_space(text, position + 1)
    if position >= len(text):
        raise MalformedResource(f"sequence is never closed with {closing!r}")
    return items, position + 1


def _parse_dictionary(text: str, position: int) -> tuple[dict[str, Any], int]:
    entries: dict[str, Any] = {}
    position = _skip_space(text, position + 1)
    while position < len(text) and text[position] != "}":
        key, position = _parse_value(text, position)
        position = _skip_space(text, position)
        if position < len(text) and text[position] == ":":
            position = _skip_space(text, position + 1)
        value, position = _parse_value(text, position)
        entries[str(key)] = value
        position = _skip_space(text, position)
        if position < len(text) and text[position] == ",":
            position = _skip_space(text, position + 1)
    if position >= len(text):
        raise MalformedResource("dictionary is never closed")
    return entries, position + 1


def _skip_space(text: str, position: int) -> int:
    while position < len(text) and text[position] in " \t\r\n":
        position += 1
    return position


def _continues_word(text: str, position: int) -> bool:
    return position < len(text) and (text[position].isalnum() or text[position] == "_")

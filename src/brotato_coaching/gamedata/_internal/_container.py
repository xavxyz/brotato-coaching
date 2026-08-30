"""Reading a Godot GDPC container — the `.pck` files the game ships.

The format is a header, a flat index, then the bytes. Every entry is stored
uncompressed and unencrypted in Brotato's containers, so reading a file is a
seek and a read; there is no decompression step to get wrong.

Layout, format 1 (the one Brotato ships, from Godot 3.7):

    magic       4 bytes, b"GDPC"
    format      u32, 1
    version     3 x u32, the engine's major/minor/patch
    reserved    16 x u32
    file count  u32
    entries     file count x (path length u32, path bytes, offset u64,
                              size u64, md5 16 bytes)

Format 2 adds a per-entry flags field and a base offset; it is rejected rather
than guessed at, because a wrong guess reads plausible-looking garbage.
"""

import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

_MAGIC = b"GDPC"
_SUPPORTED_FORMAT = 1
_HEADER = struct.Struct("<4I")
_RESERVED_BYTES = 16 * 4
_ENTRY_TAIL = struct.Struct("<QQ16s")


class MalformedContainer(Exception):
    """The file is not a container this reader understands."""


@dataclass(frozen=True)
class _Entry:
    offset: int
    size: int


class Container:
    """One `.pck`, indexed and ready to read from.

    The whole index is held in memory — 7416 entries is nothing — but file bytes
    are read on demand.
    """

    def __init__(self, path: Path, entries: dict[str, _Entry]) -> None:
        self.path = path
        self._entries = entries

    def read_text(self, resource_path: str) -> str:
        """The bytes of one `res://` path, decoded. Raises `KeyError`."""
        entry = self._entries.get(resource_path)
        if entry is None:
            raise KeyError(f"{resource_path} is not in {self.path.name}")
        with self.path.open("rb") as handle:
            handle.seek(entry.offset)
            return handle.read(entry.size).decode("utf-8")

    def paths_ending_with(self, suffix: str) -> Iterator[str]:
        for resource_path in self._entries:
            if resource_path.endswith(suffix):
                yield resource_path


def open_container(path: Path) -> Container:
    """Read a container's header and index. Raises `MalformedContainer`."""
    with path.open("rb") as handle:
        if handle.read(4) != _MAGIC:
            raise MalformedContainer(f"{path} does not start with GDPC")
        try:
            container_format = _HEADER.unpack(_exactly(handle, 16))[0]
            if container_format != _SUPPORTED_FORMAT:
                raise MalformedContainer(
                    f"{path} is GDPC format {container_format}; only format "
                    f"{_SUPPORTED_FORMAT} is understood"
                )
            _exactly(handle, _RESERVED_BYTES)
            (file_count,) = struct.unpack("<I", _exactly(handle, 4))
            entries = dict(_read_index(handle, file_count))
        except struct.error as error:
            raise MalformedContainer(f"{path} ends mid-header: {error}") from error
    return Container(path=path, entries=entries)


def _read_index(handle: BinaryIO, file_count: int) -> Iterator[tuple[str, _Entry]]:
    for _ in range(file_count):
        (path_length,) = struct.unpack("<I", _exactly(handle, 4))
        # Paths are null-padded to a 4-byte boundary in some writers, so the
        # declared length can exceed the string it holds.
        raw_path = _exactly(handle, path_length).rstrip(b"\0")
        offset, size, _md5 = _ENTRY_TAIL.unpack(_exactly(handle, _ENTRY_TAIL.size))
        yield raw_path.decode("utf-8"), _Entry(offset=offset, size=size)


def _exactly(handle: BinaryIO, count: int) -> bytes:
    data = handle.read(count)
    if len(data) != count:
        raise MalformedContainer(
            f"wanted {count} bytes of index, got {len(data)}: the file is truncated"
        )
    return data

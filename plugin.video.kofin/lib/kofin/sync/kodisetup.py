"""Kodi's shipped node trees, seeded into the profile before kofin writes
its own folder there (``sync/dynamic.py``).
"""

import codecs
import os
import re
import xml.etree.ElementTree as etree

import xbmcvfs

from kofin.core.log import Logger

LOG = Logger(__name__)

# Kodi reads a node file with TinyXML (CLibraryDirectory::LoadXML), once it
# has the text in UTF-8 and has escaped every "&" that starts no reference
# it knows (CXBMCTinyXML::InternalParse). TinyXML skips whitespace before
# the declaration and takes the first element for the document.
_BARE_AMPERSAND = re.compile(
    r"&(?!(?:amp|lt|gt|quot|apos|#x[a-fA-F0-9]{1,4}|#[0-9]{1,5});)"
)
_MARKS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


class _FirstElement:
    """A parser target that notes when the document's first element ends."""

    def __init__(self) -> None:
        self.depth = 0
        self.closed = False

    def start(self, tag: str, attrib: dict[str, str]) -> None:
        self.depth += 1

    def end(self, tag: str) -> None:
        self.depth -= 1
        self.closed = self.closed or not self.depth

    def close(self) -> bool:
        return self.closed


def _text(data: bytes) -> str:
    """A node file's text, by its byte order mark, else as UTF-8, else in a
    charset that takes any byte: Kodi reads a file that is not UTF-8 in the
    GUI's charset."""
    for mark, codec in _MARKS:
        if data.startswith(mark):
            return data.decode(codec, "replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _readable(path: str) -> bool:
    """Whether Kodi can read the node file at ``path``."""
    with open(path, "rb") as handle:
        text = _BARE_AMPERSAND.sub("&amp;", _text(handle.read())).lstrip()
    first = _FirstElement()
    try:
        etree.XMLParser(target=first).feed(text)
    except etree.ParseError:
        pass
    return first.closed


def seed_default_nodes(kind: str) -> None:
    """Copy Kodi's shipped ``kind`` node tree into the profile.

    Missing files only: a node the user has edited is theirs, and the copy
    is what makes the profile tree a superset of the shipped one rather
    than a replacement for it. A file Kodi cannot read is recovered from
    the default, since Kodi drops it silently otherwise.
    """
    source_base_path = xbmcvfs.translatePath("special://xbmc/system/library/%s" % kind)
    dest_base_path = xbmcvfs.translatePath("special://profile/library/%s" % kind)

    if not os.path.exists(source_base_path):
        LOG.error("XMLs source path `%s` not found.", source_base_path)
        return

    for source_path, _dirs, files in os.walk(source_base_path):
        relative_path = os.path.relpath(source_path, source_base_path)
        dest_path = os.path.join(dest_base_path, relative_path)

        if not os.path.exists(dest_path):
            os.makedirs(os.path.normpath(dest_path))

        for file_name in files:
            dest_file = os.path.join(dest_path, file_name)
            copy = False

            if not os.path.exists(dest_file):
                copy = True
            elif os.path.splitext(file_name)[1].lower() == ".xml":
                if not _readable(dest_file):
                    LOG.warning(
                        "Unable to read `%s`, recovering from default.", dest_file
                    )
                    copy = True

            if copy:
                source_file = os.path.join(source_path, file_name)
                LOG.debug("Copying `%s` -> `%s`", source_file, dest_file)
                xbmcvfs.copy(source_file, dest_file)

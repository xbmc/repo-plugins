import json
import re
from typing import Any, Dict, Optional, Set, List, Union

from resources.lib.chn_class import PreProcessorResult
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger


class RSCHelper:
    """
    Helper for converting React Server Components (Next.js RSC wire format)
    into resolved JSON by dereferencing $Lx and $@x references.
    """

    def __init__(self, content: str) -> None:
        self._records: Dict[str, Any] = {}
        self._root: Optional[Any] = None
        self._content: str = content

    def convert_to_json(self) -> Union[List, Dict]:
        """
        Convert RSC wire-format content into resolved JSON.
        """
        self._records.clear()
        self._root = None

        self._parse_stream()

        if self._root is None:
            raise ValueError("No root record (0:) found in RSC content")

        return self._resolve(self._root)

    def _parse_stream(self) -> None:
        # Flight records normally end at a newline. However, T records contain
        # raw UTF-8 text whose length is specified in bytes, not characters.
        # That text may contain newlines and may be followed immediately by
        # another record, so splitting the entire response into lines is unsafe.
        stream = self._content.encode("utf-8").replace(b"\r\n", b"\n")
        position = 0

        while position < len(stream):
            # Skip CR/LF separators between records. Byte 10 is '\n' and
            # byte 13 is '\r'. Newlines inside T payloads are never skipped,
            # because those payloads are consumed using their explicit length.
            while position < len(stream) and stream[position] in (10, 13):
                position += 1
            if position >= len(stream):
                break

            # Detect a length-prefixed text record, e.g. "4c:T458,...".
            # Both the record ID and the byte length are hexadecimal.
            match = re.match(rb"([0-9a-fA-F]+):T([0-9a-fA-F]+),", stream[position:])
            if match:
                key = match.group(1).decode("ascii")
                length = int(match.group(2), 16)

                # The content begins just after "<id>:T<length>,". Read
                # exactly 'length' bytes, even if they contain line breaks.
                start = position + match.end()
                end = start + length
                if end > len(stream):
                    raise ValueError(f"Incomplete Flight text record {key}")
                self._records[key] = stream[start:end].decode("utf-8")

                # Resume at the very next byte, which may be the beginning of
                # another record without any newline in between.
                position = end
                continue

            # Other record types are newline-delimited JSON or import/control
            # records; let _parse_line() interpret their contents.
            end = stream.find(b"\n", position)
            if end < 0:
                end = len(stream)
            self._parse_line(stream[position:end].decode("utf-8").strip())
            position = end + 1

    def _parse_line(self, line: str) -> None:
        if not line or ":" not in line:
            return

        key, raw = line.split(":", 1)
        raw = raw.strip()

        try:
            # Module reference: I[...]
            if raw.startswith("I["):
                self._records[key] = {
                    "__module__": json.loads(raw[1:])
                }
                return

            if raw.startswith("T"):
                # string with length
                hex_length, raw = raw[1:].split(",", 1)
                length = int(hex_length, 16)

                raw_bytes = raw.encode("utf-8")
                text_value = raw_bytes[:length].decode("utf-8")
                remainder = raw_bytes[length:].decode("utf-8")

                self._records[key] = text_value

                if remainder:
                    self._parse_line(remainder)
                return

            parsed = json.loads(raw)
            self._records[key] = parsed

            if key == "0":
                self._root = parsed

        except json.JSONDecodeError:
            # Ignore non-JSON lines
            pass

    def _resolve(self, value: Any, seen: Optional[Set[str]] = None) -> Any:
        if seen is None:
            seen = set()

        if isinstance(value, str):
            if value == "$":
                return "$"

            if value == "$undefined":
                return None

            if value.startswith("$S"):
                return {"__symbol__": value[2:]}

            if value.startswith("$Q"):
                key = value[2:]
                if key in seen:
                    return "[Circular]"
                return {
                    "__map__": self._resolve(
                        self._records.get(key),
                        seen | {key}
                    )
                }

            if value.startswith("$@"):
                key = value[2:]
                if key in seen:
                    return "[Circular]"
                return {
                    "__promise__": self._resolve(
                        self._records.get(key),
                        seen | {key}
                    )
                }

            if value.startswith("$L"):
                key = value[2:]
            elif value.startswith("$"):
                key = value[1:]
            else:
                return value

            if key in seen:
                return "[Circular]"

            return self._resolve(
                self._records.get(key),
                seen | {key}
            )

        if isinstance(value, list):
            return [self._resolve(v, seen.copy()) for v in value]

        if isinstance(value, dict):
            return {
                k: self._resolve(v, seen.copy())
                for k, v in value.items()
            }

        return value


class NextJsParser:
    def __init__(self, key: str = "", value: str = "", return_parent: bool = False, skip: int = 0) -> None:
        self._key = key
        self._value = value
        self._skip = skip
        self._return_parent = return_parent

    def __call__(self, data: str) -> PreProcessorResult:
        helper = RSCHelper(data)
        result_data = helper.convert_to_json()
        if result_data:
            Logger.debug("Found NextJs data: %s", JsonHelper.dump(result_data, pretty_print=False))

        if self._key and self._value:
            result_data = JsonHelper.find_dict_by_key_value_from(
                result_data, self._key, self._value, skip=[self._skip])
        elif self._key:
            result_data = JsonHelper.find_dict_by_key_from(
                result_data, self._key, self._return_parent, skip=[self._skip])

        if result_data and isinstance(result_data, str):
            return result_data, []
        elif result_data:
            return JsonHelper(result_data), []

        Logger.warning("Could not find NextJs data for key: %s, value: %s", self._key, self._value)
        return "", []

    def __str__(self):
        return f"NextJsParser(key={self._key}, value={self._value})"

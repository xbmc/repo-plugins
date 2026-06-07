import json
from typing import Any, Dict, Optional, Set, List, Union

from resources.lib.helpers.jsonhelper import JsonHelper


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

        for line in self._content.splitlines():
            self._parse_line(line.strip())

        if self._root is None:
            raise ValueError("No root record (0:) found in RSC content")

        return self._resolve(self._root)

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

            parsed = json.loads(raw)
            self._records[key] = parsed

            if key == "0":
                self._root = parsed

        except json.JSONDecodeError:
            # Ignore non-JSON lines
            pass

    def _normalize(self, value: Any) -> Any:
        if value == "$undefined":
            return None

        if isinstance(value, str) and value.startswith("$S"):
            return {"__symbol__": value[2:]}

        return value

    def _resolve(self, value: Any, seen: Optional[Set[str]] = None) -> Any:
        if seen is None:
            seen = set()

        if isinstance(value, str):
            if value.startswith("$L"):
                key = value[2:]
                if key in seen:
                    return "[Circular]"
                seen.add(key)
                return self._resolve(self._records.get(key), seen)

            if value.startswith("$@"):
                return {
                    "__promise__": self._resolve(value[2:], seen)
                }

            return self._normalize(value)

        if isinstance(value, list):
            return [self._resolve(v, seen.copy()) for v in value]

        if isinstance(value, dict):
            return {k: self._resolve(v, seen.copy()) for k, v in value.items()}

        return value

# if __name__ == "__main__":
#     with open("nextjs.rsc.txt", "r") as f:
#         content = f.read()
#
#     helper = RSCHelper(content)
#     json_data = JsonHelper(helper.convert_to_json())
#     tv_guide_data = json_data.find_dict_by_key_value("id", "tvguide-list")
#
#     print(JsonHelper.dump(tv_guide_data, pretty_print=True))

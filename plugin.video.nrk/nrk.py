from enum import Enum
from typing import Any, override


from requests.models import Response


from requests import Session

session = Session()
session.headers["User-Agent"] = "kodi.tv"


class Base(object):
    def __init__(
        self,
        id: str | None,
        title: str | None,
        type: Enum,
        is_playable: bool,
        manifest_url: str | None,
    ):
        self.__id: str | None = id
        self.__title: str | None = title
        self.__type: Enum = type
        self.__is_playable: bool = is_playable
        self.__manifest_url: str | None = manifest_url  # must be an absolute path
        self.__children: list[Base] = []
        self.__media_url: str | None = None
        self.thumb: str | None = None
        self.fanart: str | None = None

    def __str__(self):
        return f"{self.__class__.__name__}: { {str(self.__id)}, {str(self.__title)} }"

    @property
    def id(self) -> str | None:
        return self.__id

    @property
    def title(self) -> str:
        return self.__title or "Ingen tittel"

    @property
    def manifest_url(self) -> str | None:
        return self.__manifest_url

    def append_child(self, child: "Base") -> None:
        self.__children.append(child)

    @property
    def children(self) -> list["Base"]:
        return self.__children

    @property
    def is_playable(self) -> bool:
        return self.__is_playable

    @property
    def type(self) -> str:
        return self.__type.value

    @property
    def media_url(self) -> str | None:
        if self.__is_playable:
            return self.__media_url
        return None

    @media_url.setter
    def media_url(self, value: str | None) -> None:
        self.__media_url = value

    def add_images(self, images) -> None:
        self.thumb = deep_get_str(images, 0, "url")
        self.fanart = deep_get_str(images, -1, "url")


class BasePage(Base):
    @override
    def add_images(self, images) -> None:
        self.thumb = deep_get_str(images, 0, "uri")
        self.fanart = deep_get_str(images, -1, "uri")


def get(path: str, params: str = "") -> Any:
    api_key = "d1381d92278a47c09066460f2522a67d"
    if len(params) > 0 and params[0] != "&":
        raise ValueError("params must start with &")
    r: Response = session.get(
        "https://psapi.nrk.no{}?apiKey={}{}".format(path, api_key, params)
    )
    r.raise_for_status()
    return r.json()


def deep_get(obj: Any, *keys: int | str) -> Any | None:
    if len(keys) == 0:
        return None

    key: int | str = keys[0]

    if isinstance(key, str) and isinstance(obj, dict):
        value: Any | None = obj.get(key)

    elif isinstance(key, int) and isinstance(obj, list):
        if len(obj) <= key or key < -len(obj):
            return None
        value: Any | None = obj[key]
    else:
        return None

    if len(keys) >= 2:
        return deep_get(value, *keys[1:])
    else:
        return value


def deep_get_str(obj: Any, *keys: int | str) -> str | None:
    value: Any | None = deep_get(obj, *keys)
    if isinstance(value, str):
        return value
    else:
        return None


def deep_get_dict(obj: Any, *keys: int | str) -> dict[Any, Any]:
    value: Any | None = deep_get(obj, *keys)
    if isinstance(value, dict):
        return value
    else:
        return {}


def deep_get_list(obj: Any, *keys: int | str) -> list[Any]:
    value: Any | None = deep_get(obj, *keys)
    if isinstance(value, list):
        return value
    else:
        return []

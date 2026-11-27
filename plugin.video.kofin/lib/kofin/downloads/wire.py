"""The downloads IPC wire format.

The ``DownloadAdd``/``DownloadRemove`` payload contract between their
senders and the manager.
"""

from typing import Any, NamedTuple

from kofin.downloads import store as downloads_store

JsonDict = dict[str, Any]


class Add(NamedTuple):
    """One ``DownloadAdd`` request, parsed."""

    ids: list[str]
    origin: str
    media_types: list[str]
    # The item selected by the user and what to call it. Empty for automatic
    # paths and older plugin clients.
    request_id: str = ""
    request_name: str = ""


def parse_add(payload: JsonDict) -> Add:
    """The ids, origin, types and request a ``DownloadAdd`` payload names.

    The optional Origin marks automatic downloads for the retention sweep;
    anything unrecognized is a user download — the label that is never
    auto-deleted. Types is optional and positional against Ids: the sender
    holds each item's DTO type, and passing it here is what lets the queue
    split by media kind without an item fetch per row. Paired before the
    empty ids are dropped, so a blank in the middle cannot shift the rest by
    one; a short or absent list just leaves kinds unknown, which the video
    pool claims.

    Request/RequestName are optional for older plugin processes and automatic
    downloads; a row without a request gets the per-item or per-album toast.
    """
    origin = str(payload.get("Origin") or downloads_store.ORIGIN_USER)
    if origin != downloads_store.ORIGIN_USER and not downloads_store.is_auto_origin(
        origin
    ):
        origin = downloads_store.ORIGIN_USER
    raw_ids = [str(one) for one in (payload.get("Ids") or [])]
    raw_types = [str(one) for one in (payload.get("Types") or [])]
    pairs = [
        (item_id, raw_types[index] if index < len(raw_types) else "")
        for index, item_id in enumerate(raw_ids)
        if item_id
    ]
    return Add(
        [item_id for item_id, _ in pairs],
        origin,
        [dto_type for _, dto_type in pairs],
        str(payload.get("Request") or ""),
        str(payload.get("RequestName") or ""),
    )


def item_id(payload: JsonDict) -> str:
    """The one id a ``DownloadCancel`` names."""
    return str(payload.get("Id") or "")


def item_ids(payload: JsonDict) -> list[str]:
    """The ids a ``DownloadRemove`` names.

    A list, because the sender expands a season or an album before it sends.
    A bare ``Id`` is still read: a plugin process left over from before an
    add-on update sends that shape.
    """
    raw = payload.get("Ids")
    if raw is None:
        single = item_id(payload)
        return [single] if single else []
    return [str(one) for one in raw if one]

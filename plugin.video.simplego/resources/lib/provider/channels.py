"""The channel lists: the subscription's, the whole channel map, the favourites."""

import time

from resources.lib.provider import core
from resources.lib.provider import errors

# Non-subscribed channels of the map ("all") list but do not play.
SCOPES = {
    "subscribed": ("/epg/channel/subscriptions", "EPG", "SUBSCRIBED_CHANNELS"),
    "all": ("/epg/channel", "START_UP", "EPG_CHANNEL"),
    "favourite": ("/epg/channel/favourite", "EPG", "FAVOURITE_CHANNELS"),
}


class Channels:
    """The channel lists, kept in the state.

    :param state: the client's statefile.State
    :param api: the client's core.Api (the public list)
    :param auth: the client's auth.Auth (the account's lists)
    """

    def __init__(self, state, api, auth):
        self._state = state
        self._api = api
        self._auth = auth

    def list(self, scope="all", kind="all"):
        """Return the channels of the subscriber's channel map (the public one in guest mode), with their MediaKind ids.

        Cached: the raw answer is close to 1 MB, too slow to fetch per menu on a TV box.

        :param scope: "subscribed" / "all" / "favourite"
        :param kind: "tv" / "radio" / "all"
        """
        if not self._auth.authed:
            scope = "guest"
        acc = self._auth.valid_account() if self._auth.authed else {}
        cache = self._state.setdefault("channels_cache", {})
        entry = cache.get(scope)
        ttl = core.CHANNELS_TTL if scope == "favourite" else core.LINEUP_TTL
        if not entry or entry["at"] + ttl < time.time() or entry["map"] != acc.get("channelMap_id"):
            entry = cache[scope] = {"at": time.time(), "map": acc.get("channelMap_id"), "list": self._fetch_channels(scope)}
            self._state.save()
        return [c for c in entry["list"] if kind == "all" or c["radio"] == (kind == "radio")]

    def forget(self, scope):
        """Drop a kept channel list (it changed on the account): the next ask fetches it again."""
        self._state.get("channels_cache", {}).pop(scope, None)

    def channel_of(self, channel_id):
        """Return a channel's entry from the kept channel lists; None if not there."""
        for entry in (self._state.get("channels_cache") or {}).values():
            for c in entry.get("list") or []:
                if c.get("id") == channel_id:
                    return c
        return None

    def station_of(self, channel_id):
        """Return a channel's station id (the guide's key) from the kept lists; None if not there."""
        return (self.channel_of(channel_id) or {}).get("station_id")

    def subscribed_ids(self, fetch=True):
        """Return the ids of the subscribed channels; None without a login or if unknown.

        :param fetch: False uses the kept list however old (None if none); for a channel
            start, where the server refuses an unsubscribed channel anyway (3097)
        """
        if not self._auth.authed:
            return None
        if not fetch:
            entry = (self._state.get("channels_cache") or {}).get("subscribed")
            return {c["id"] for c in entry["list"]} if entry else None
        try:
            return {c["id"] for c in self.list("subscribed")}
        except errors.ApiError:
            return None  # unknown: let the server decide

    def _fetch_channels(self, scope):
        if scope == "guest":
            data = self._api.call("/epg/channel", "START_UP", "EPG_CHANNEL", params={"includeVirtualChannels": "false"})
        else:
            path, flow, step = SCOPES[scope]
            params = {"channelMap_id": self._auth.channel_map(), "includeVirtualChannels": "false"}
            data = self._auth.call(path, flow, step, params=params)
        collections = data.get("serviceCollection_service_map") or {}
        services = data.get("services_map") or {}
        out = []
        for c in data.get("channels", []):
            radio = bool(c.get("is_audio"))
            coll = collections.get(str(c.get("service_collection_id"))) or {}
            media_ids = [
                services[s]["media_id"] for s in coll.get("service_ids", []) if s in services and services[s].get("media_id")
            ]
            if not media_ids:
                continue
            out.append(
                {
                    "id": str(c.get("service_collection_id")),
                    "station_id": str(c.get("station_id")),
                    "name": c.get("title", ""),
                    "number": c.get("channel_number"),
                    "logo": c.get("channel_logo", ""),
                    "media_id": media_ids[0],
                    "catchup": bool(c.get("is_catchup_enabled")),
                    "adult": bool(c.get("is_adult")),
                    "radio": radio,
                    "genres": [
                        g.get("localised_name") or g.get("name")
                        for g in c.get("genres") or []
                        if g.get("localised_name") or g.get("name")
                    ],
                }
            )
        out.sort(key=lambda c: c["number"] or 9999)
        return out

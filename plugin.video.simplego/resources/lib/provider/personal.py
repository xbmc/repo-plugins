"""The account's own lists and settings: favourites, channel order, positions, parental lock."""

import time
from urllib.parse import quote

from resources.lib.provider import core
from resources.lib.provider import errors
from resources.lib.provider import rsaoaep

# Only these airing fields are kept: every plugin call reads the state file, and a season's
# episodes with their plots were most of it.
AIRING_FIELDS = ("program_id", "start_utc", "end_utc", "station_id", "channel_number", "entitlements", "ratings")
# What the web sends of each position it removes (see delete_bookmarks).
DELETE_FIELDS = ("id", "runtime_seconds", "program_id", "bookmark_type", "subject_id")


def _slim(actions):
    """Return {"catchup_schedules", "schedules"} with AIRING_FIELDS only."""
    return {
        part: [{k: a[k] for k in AIRING_FIELDS if k in a} for a in (actions or {}).get(part) or []]
        for part in ("catchup_schedules", "schedules")
    }


class Personal:
    """The account's own lists and settings, some kept in the state a few minutes.

    :param state: the client's statefile.State
    :param api: the client's core.Api (the startup page's PIN key)
    :param auth: the client's auth.Auth
    :param channels: the client's channels.Channels (a favourite changes its list)
    """

    def __init__(self, state, api, auth, channels):
        self._state = state
        self._api = api
        self._auth = auth
        self._channels = channels

    def parental_lock_enabled(self):
        """Return whether the account has a parental lock (a PIN).

        Only the PIN is the account's; the age limit is per app and each app enforces
        it itself, so does this add-on (see parental).
        """
        st = self._state
        if st.get("parental_at", 0) + core.ACCOUNT_TTL < time.time():
            data = self._auth.call("/setting/account/v2", "SETTINGS", "ACCOUNT_SETTINGS")
            st["parental"] = bool(data.get("parental_control_enabled"))
            st["parental_at"] = time.time()
            self._state.save()
        return st["parental"]

    def verify_pin(self, pin):
        """Return whether `pin` is the account's parental lock PIN (checked by the provider)."""
        if not self._state.get("pin_key"):
            self._api.bootstrap(force=True)
        passcode = rsaoaep.encrypt(self._state["pin_key"], pin.encode("ascii"))
        try:
            path = "/setting/passcode/verify/v2"
            data = self._auth.call(path, "SETTINGS", "PASSCODE_VERIFY", method="POST", body={"passcode": passcode})
        except errors.ApiError as e:
            if getattr(e, "status", None) in (400, 403, 422):
                return False
            raise
        return bool(data.get("status"))

    def set_favourite_channel(self, number, on):
        """Add a channel to the account's favourites or remove it, by its number."""
        body = {"add_keys": [int(number)]} if on else {"delete_keys": [int(number)]}
        self._auth.call("/epg/channel/favourite", "MY_CHANNELS", "SET_FAVOURITE", method="POST", body=body)
        self._channels.forget("favourite")
        self._state.save()

    def watchlist(self):
        """Return the account's favourite programmes, each with its next airing."""
        return self._kept(
            "watchlist",
            core.LIST_TTL,
            lambda: self._auth.call("/watchlist/v2/items", "MY_WATCHLIST", "GET_WATCHLIST").get("items") or [],
        )

    def _kept(self, key, ttl, fetch):
        """Return fetch()'s answer, kept in the state for ttl seconds.

        Browsing reopens the same lists, and each plugin call is a fresh interpreter that would
        otherwise import the HTTP stack (see net.transport for its cost) and ask again.
        Own changes drop the answer (see _forget).
        """
        kept = self._state.setdefault("kept", {})
        entry = kept.get(key)
        if entry and entry["at"] + ttl > time.time():
            return entry["data"]
        data = fetch()
        now = time.time()
        # An hour is more than any ttl.
        self._state["kept"] = {k: v for k, v in kept.items() if v["at"] + 3600 > now}
        self._state["kept"][key] = {"at": now, "data": data}
        self._state.save()
        return data

    def _forget(self, prefix):
        """Drop the kept answers whose key starts with prefix (see _kept)."""
        kept = self._state.get("kept") or {}
        if any(k.startswith(prefix) for k in kept):
            self._state["kept"] = {k: v for k, v in kept.items() if not k.startswith(prefix)}
            self._state.save()

    def channel_order(self):
        """Return the account's own channel order as channel ids; empty if not set."""
        st = self._state
        if st.get("channel_order_at", 0) + core.CHANNELS_TTL < time.time():
            data = self._auth.call("/epg/channel/order", "MY_CHANNELS", "GET_CHANNEL_ORDER")
            st["channel_order"] = [str(i) for i in data.get("channel_order") or []]
            st["channel_order_at"] = time.time()
            self._state.save()
        return st["channel_order"]

    def set_channel_order(self, channel_ids):
        """Save the account's own channel order; empty resets it."""
        body = {"channel_order": [int(i) for i in channel_ids]}
        self._auth.call("/epg/channel/order", "MY_CHANNELS", "SET_CHANNEL_ORDER", method="POST", body=body)
        self._state["channel_order"] = [str(i) for i in channel_ids]
        self._state["channel_order_at"] = time.time()
        self._state.save()

    def bookmarks(self, details=False):
        """Return the catch-up resume positions.

        Each has id ("<station>_<start>_<end>"), time_seconds and runtime_seconds.

        :param details: also title, thumbnail and bookmark_type
        """
        params = {"type": "" if details else "CATCHUP"}
        step = "BOOKMARK_ALL" if details else "BOOKMARK_CATCHUP"
        listed = (self._state.get("kept") or {}).get("bookmarks:")
        if not details and listed and listed["at"] + core.POSITIONS_TTL > time.time():
            # The "Continue watching" list just shown has them.
            return [b for b in listed["data"] if b.get("bookmark_type", "Catchup") == "Catchup"]
        return self._kept(
            "bookmarks:%s" % params["type"],
            core.POSITIONS_TTL,
            lambda: self._auth.call("/details/bookmarks/v3", "START_UP", step, params=params).get("bookmarks") or [],
        )

    def set_bookmark(self, info, seconds, runtime):
        """Save a catch-up programme's resume position.

        :param info: id, program_id, media_id, start_time, end_time and station_id (see streamsession.bookmark_info)
        :return: the provider's answer
        """
        body = dict(info, time_seconds=round(seconds, 3), runtime_seconds=int(runtime))
        answer = self._auth.call("/details/bookmarks/CATCHUP/v3", "PLAYER", "SET_BOOKMARK", method="PUT", body=body)
        self._forget("bookmarks:")
        return answer

    def delete_bookmarks(self, bookmarks):
        """Remove positions from the account's Continue watching.

        The account's own positions only, with the request the web player's edit mode sends.

        :param bookmarks: items of bookmarks(details=True)
        :return: the provider's answer
        """
        body = {"bookmarks": [{k: b.get(k) for k in DELETE_FIELDS} for b in bookmarks]}
        answer = self._auth.call("/delete/bookmarks/v2", "START_UP", "DELETE_BOOKMARKS", method="POST", body=body)
        self._forget("bookmarks:")
        return answer

    def set_watchlist(self, item_id, on, kind="series"):
        """Add a series or a programme to the favourite programmes or remove it.

        :param kind: "series" or "program"
        """
        key = "add_action" if on else "delete_action"
        body = {key: [{"id": item_id, "type": kind}]}
        self._auth.call("/watchlist/items", "MY_WATCHLIST", "UPDATE_WATCHLIST", method="POST", body=body)
        self._forget("watchlist")

    def season(self, series_id, season_id, number):
        """Return a season's episodes: id (the programme's), number, name (its title), actions (see _slim)."""
        path = "/details/series/%s/season/%s/v2" % (quote(series_id, safe=""), quote(season_id, safe=""))
        params = {"interacted_with_nPVR": "false", "season_number": str(number)}
        return self._kept(
            "season:%s" % season_id,
            core.LIST_TTL,
            lambda: [
                {"id": e.get("id"), "number": e.get("number"), "name": e.get("name"), "actions": _slim(e.get("actions"))}
                for e in self._auth.call(path, "SERIES_DETAIL", "SEASON_DETAIL", params=params).get("episodes") or []
            ],
        )

    def offers(self, program_id):
        """Return the offers that would make a programme's channel play, if it is outside the subscription.

        Each has package_name, price and currency ("Telekom TV M csomag", 6990, "HUF"); none if the
        channel plays already. The channel list does not say: only a programme's actions do.
        """
        path = "/details/program/%s/actions/v2" % quote(program_id, safe="")
        actions = self._auth.call(path, "SINGLE_PROGRAM_DETAIL", "PROGRAM_WATCH_ACTION").get("actions") or {}
        return [offer for channel in actions.get("channel_subscribe") or [] for offer in channel.get("channel_subscribe") or []]

    def airings(self, item_id, kind="series"):
        """Return (catch-up, upcoming) airings of a series or a programme, each with AIRING_FIELDS.

        entitlements are the guide's content flags.
        """
        path = "/details/%s/%s/actions/v2" % (kind, quote(item_id, safe=""))
        if kind == "series":
            flow, step = "SERIES_DETAIL", "SERIES_WATCH_ACTION"
        else:
            flow, step = "SINGLE_PROGRAM_DETAIL", "PROGRAM_WATCH_ACTION"
        actions = self._kept(
            "airings:%s:%s" % (kind, item_id),
            core.LIST_TTL,
            lambda: _slim(self._auth.call(path, flow, step).get("actions")),
        )
        return actions.get("catchup_schedules") or [], actions.get("schedules") or []

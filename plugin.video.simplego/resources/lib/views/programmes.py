"""Favourite programmes: the list, a series' seasons, and the picker of an item's airings."""

import collections

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib.data import channellist
from resources.lib.data import guidedata
from resources.lib.util import isotime
from resources.lib.util import localtime
from resources.lib.views import listing
from resources.lib.views import rows

_s = kodiutil.string
_log = kodiutil.log
# One of a favourite's airings in the picker (see pick_rows).
PickRow = collections.namedtuple("PickRow", "airing channel on_now can_play")


class ProgrammeViews:
    """The favourite programmes (see views.routes).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_watchlist(self):
        """List the favourite programmes (the web's "Kedvenc tartalmak").

        A click picks one of its airings to play, or shows when it is on next (see do_pick).
        """
        items = self._call.client.watchlist()
        self._call.laps("list")  # timed apart from the pages, for the log
        kinds = ["series" if item.get("show_type") == "Series" else "program" for item in items]
        # The provider's list has no plots (its "description" is empty): the info pages have them,
        # fetched in one go with the cast if a cast setting wants it.
        cast_kinds = kodiutil.cast_kinds()
        keys = [(kind, item["id"]) for kind, item in zip(kinds, items, strict=True) if cast_kinds or not item.get("description")]
        pages = listing.pages(self._call, keys, full=bool(cast_kinds))
        plots = {key: page.get("plot") or "" for key, page in pages.items()}
        cast = rows.cast_of(pages, cast_kinds)
        for kind, item in zip(kinds, items, strict=True):
            year = guidedata.year(item)
            li = xbmcgui.ListItem(rows.film_title(item.get("name") or "?", year if kind == "program" else None))
            picture = item.get("image_url") or ""
            # The row shows its icon (Kodi's own, by type: no thumb, which the row would show instead);
            # the side panel the poster.
            icon = "DefaultTVShows.png" if kind == "series" else "DefaultMovies.png"
            rows.set_art(li, {"icon": icon, "fanart": picture, "poster": guidedata.poster(kind, item["id"])})
            tag = li.getVideoInfoTag()
            tag.setTitle(item.get("name") or "")
            tag.setPlot(item.get("description") or plots.get((kind, item["id"])) or "")
            # A type Kodi has an "Information" page for.
            tag.setMediaType("tvshow" if kind == "series" else "movie")
            rows.set_credits(tag, cast.get((kind, item["id"])))
            if year:
                tag.setYear(year)
            rows.set_mpaa(tag, item.get("ratings"))
            # Kodi's own favourites item off, its words on this one: no channel row here to mix them up with.
            rows.hide_kodi_favourites(li)
            unwatch = (
                kodiutil.kodi_string(14077),
                "RunPlugin(%s)" % self._call.url(action="watch", id=item["id"], kind=kind, on=0),
            )
            # An action, not a playable item: a picker left with "Back" is then no failed playback for Kodi.
            # Its next airing as the list has it, for when the airings say none (see do_pick).
            known = {"start": item["start_utc"], "end": item["end_utc"]} if item.get("start_utc") and item.get("end_utc") else {}
            if kind == "series":  # its seasons, as its web page's "Évadok" (see do_seasons)
                li.addContextMenuItems([unwatch])
                seasons = self._call.url(action="seasons", id=item["id"], **known)
                xbmcplugin.addDirectoryItem(self._call.handle, seasons, li, isFolder=True)
            else:
                pick = self._call.url(action="pick", id=item["id"], kind=kind, **known)
                li.addContextMenuItems([unwatch])
                xbmcplugin.addDirectoryItem(self._call.handle, pick, li, isFolder=False)
        # No content type: Estuary's wide list then shows each row's icon (with "videos", a status icon only).
        # Nothing on the right: when it is on, the airings picked from say.
        rows.hide_right_labels(self._call.handle)
        xbmcplugin.endOfDirectory(self._call.handle)

    def do_watch(self):
        """Put a series or a programme onto the favourite programmes or off them (context menus).

        Said done only once the list says so: the provider takes an add it then leaves out (a film with
        no airing left, seen 2026-11-02) without a word.
        """
        client, item_id = self._call.client, self._call.params["id"]
        on = self._call.params.get("on") == "1"
        client.set_watchlist(item_id, on, self._call.params.get("kind") or "series")
        listed = item_id in {item.get("id") for item in client.watchlist()}  # asked again: the change forgot the kept one
        if listed == on:
            xbmcgui.Dialog().notification(kodiutil.name(), _s(30172 if on else 30173))
        else:
            _log("favourite %s %s, but the list says otherwise" % (item_id, "added" if on else "removed"), xbmc.LOGWARNING)
            xbmcgui.Dialog().notification(kodiutil.name(), _s(30261 if on else 30262), xbmcgui.NOTIFICATION_WARNING)
        xbmc.executebuiltin("Container.Refresh")

    def do_seasons(self):
        """List a favourite series' seasons, as its web page's "Évadok": a click picks one of its airings.

        Without seasons (some series have none), its own airings are picked from at once.
        """
        series = self._call.client.details("series", self._call.params["id"])
        seasons = sorted(series.get("seasons") or [], key=lambda s: s.get("number") or 0)
        if not seasons:
            xbmcplugin.endOfDirectory(self._call.handle, succeeded=False)
            return self.do_pick()
        name = series.get("name") or ""
        if name:
            xbmcplugin.setPluginCategory(self._call.handle, "%s / %s" % (_s(30168), name))
        poster = guidedata.poster("series", self._call.params["id"])
        for season in seasons:
            label = season.get("display_name") or season.get("name") or "?"
            if season.get("episodes_count"):
                label += " %s" % rows.greyed("(%s)" % (_s(30229) % season["episodes_count"]))
            li = xbmcgui.ListItem(label)
            # The row shows its icon (no content type, see below); the side panel the poster.
            icon = "DefaultVideoPlaylists.png"
            rows.set_art(li, {"icon": icon, "poster": poster, "fanart": series.get("poster_image_url")})
            tag = li.getVideoInfoTag()
            rows.hide_kodi_favourites(li)
            tag.setMediaType("season")
            tag.setTvShowTitle(name)
            tag.setSeason(season.get("number") or 0)
            tag.setPlot((series.get("details") or {}).get("description") or "")
            # An action, as in do_watchlist.
            number = season.get("number") or 0
            pick = self._call.url(action="pick", id=self._call.params["id"], kind="series", season=season["id"], number=number)
            xbmcplugin.addDirectoryItem(self._call.handle, pick, li, isFolder=False)
        # No content type: Estuary's wide list then shows each row's icon (with "seasons", a status icon only).
        rows.hide_right_labels(self._call.handle)
        xbmcplugin.endOfDirectory(self._call.handle)

    def _season_airings(self):
        """Return a season's (watched back, coming) airings with episode titles, and {programme id: (season, episode)}."""
        number = int(self._call.params.get("number") or 0)
        episodes = self._call.client.season(self._call.params["id"], self._call.params["season"], number)
        back, coming, numbers = [], [], {}
        for episode in episodes:
            actions = episode.get("actions") or {}
            title = {"episode_name": episode.get("name") or ""}  # the airings' own "name" is the series'
            back += [dict(a, **title) for a in actions.get("catchup_schedules") or []]
            coming += [dict(a, **title) for a in actions.get("schedules") or []]
            if number and str(episode.get("number") or "").isdigit():
                numbers[episode.get("id")] = (number, int(episode["number"]))
        return back, coming, numbers

    def do_pick(self):
        """Pick one of a favourite programme's airings to play, as on the web player's "Lejátszás" popup.

        Playable ones resume where they were left off without asking again (the picker was the
        question); coming ones, grey, only say when they are on.

        A click follows Kodi's "Default select action", which Kodi itself applies to playable rows only:
        "Choose" opens the context menu, "Show information" the info page. A click runs this with no
        handle (-1); Kodi's own "Play" (context menu, info page) plays it with one: at once, no picker.
        """
        if self._call.params.get("action") == "pick" and self._call.handle < 0:
            if listing.opened_by_select_action():
                return None
        elif self._call.params.get("action") == "pick":
            return self._play_at_once()
        picks, numbers = self._airings_to_pick()
        index = self._picked(picks, numbers)
        if index is None:
            return None
        picked = picks[index]
        if not picked.can_play:
            xbmcgui.Dialog().notification(kodiutil.name(), _s(30228))
            return None
        # Through PlayMedia, so the play service handles it as any click (see default).
        xbmc.executebuiltin("PlayMedia(%s)" % self._call.url(**continued_play(picked)))
        return None

    def _play_at_once(self):
        """Play the airing the picker would preselect, as Kodi's own "Play" asks (context menu, info page).

        Kodi waits for the stream: a picker would keep it waiting, and one closed after Kodi's playlist
        timeout (20 s) made it say "Playback failed". Nothing to play: why, at once, and no stream.
        """
        picks, _ = self._airings_to_pick()
        playable = [pick for pick in picks if pick.can_play]
        if not playable:
            coming = next(iter(picks), None)
            text = _s(30223)
            if coming:
                text = "%s: %s" % (_s(30222), localtime.local_time(coming.airing["start_utc"]))
                text += " · %s" % coming.channel["name"] if coming.channel.get("name") else ""
            xbmcgui.Dialog().notification(kodiutil.name(), text)
            xbmcplugin.setResolvedUrl(self._call.handle, False, xbmcgui.ListItem())
            return None
        from resources.lib.views import play

        play.resolve(self._call, continued_play(playable[-1]))
        return None

    def _airings_to_pick(self):
        """Return the favourite's airings as picker rows (see pick_rows) and {programme id: (season, episode)}."""
        from resources.lib.data import infopages

        kind = self._call.params.get("kind") or "series"
        numbers = {}
        if self._call.params.get("season"):  # a season's (see do_seasons): its episodes' airings, with their numbers
            back, coming, numbers = self._season_airings()
        else:
            back, coming = self._call.client.airings(self._call.params["id"], kind)
        channels = channellist.by_station(self._call.client)
        now = isotime.iso()
        picks = pick_rows(back, coming, channels, now)
        if kind == "series" and picks and not numbers:  # the airings have no episode numbers; their info pages have
            ids = [pick.airing.get("program_id") for pick in picks]
            numbers = infopages.episode_numbers(lambda: self._call.client, ids, kodiutil.PROFILE)
        self._call.laps("airings")
        if not picks and self._call.params.get("start", "") > now:
            # Some series have no airings of their own (on the web either), but the favourites list knows the next one.
            next_one = {"start_utc": self._call.params["start"], "end_utc": self._call.params["end"]}
            picks = [PickRow(next_one, {"name": ""}, False, False)]
        return picks, numbers

    def _picked(self, picks, numbers):
        """Return the index of the row picked to play; None if cancelled or nothing can play.

        With nothing playable, the coming ones are shown read-only (the web's "További időpontok").
        """
        if not picks:
            xbmcgui.Dialog().notification(kodiutil.name(), _s(30223))
            return None
        items = [pick_row(*pick, numbers=numbers.get(pick.airing.get("program_id"))) for pick in picks]
        playable = [i for i, pick in enumerate(picks) if pick.can_play]
        if not playable:
            if xbmcgui.Dialog().select(_s(30222), items, useDetails=True) >= 0:
                xbmcgui.Dialog().notification(kodiutil.name(), _s(30228))  # as a coming one picked below
            return None
        if len(picks) == 1:
            return 0
        index = xbmcgui.Dialog().select(kodiutil.kodi_string(208), items, preselect=playable[-1], useDetails=True)
        return index if index >= 0 else None


def continued_play(pick):
    """Return the play URL's parameters of a picked airing (see PickRow), resuming without asking where it was left off."""
    params = airing_play(pick.airing, pick.channel, pick.on_now)
    if "programme" in params:
        params["programme"] = guidedata.continued(params["programme"])
    return params


def airing_play(airing, channel, on_now=False):
    """Return the play URL's parameters of a favourite's airing: from its beginning, else live."""
    params = {"action": "play", "id": channel["id"], "media": channel["media_id"]}
    flags = airing.get("entitlements") or []
    if not (on_now and guidedata.NO_RESTART_FLAG in flags):  # on now without a restart: live
        programme = {
            "start_time": airing["start_utc"],
            "end_time": airing["end_utc"],
            "content_flags": flags,
            "ratings": airing.get("ratings"),
        }
        params["programme"] = guidedata.param(programme, known_age="ratings" in airing)
    return params


def pick_rows(back, coming, channels, now):
    """Return a favourite's airings for the picker as PickRows, oldest first.

    Each once, on subscribed channels only: the provider lists some twice, and one on both a
    channel's HD and SD versions is kept as the HD one's.
    """
    picks, at = [], {}
    for airing in sorted(back + coming, key=lambda a: a.get("start_utc", "")):
        channel = channels.get(str(airing.get("station_id")))
        if not channel or not airing.get("start_utc") or not airing.get("end_utc"):
            continue
        mark = (airing.get("program_id") or airing.get("station_id"), airing["start_utc"])
        on_now = airing["start_utc"] <= now < airing["end_utc"]
        pick = PickRow(airing, channel, on_now, airing in back or on_now)
        if mark not in at:
            at[mark] = len(picks)
            picks.append(pick)
        elif _is_hd(channel) and not _is_hd(picks[at[mark]].channel):
            picks[at[mark]] = pick
    return picks


def _is_hd(channel):
    return (channel.get("name") or "").upper().endswith(" HD")


def pick_row(airing, channel, on_now, can_play=True, numbers=None):
    """Return an airing's row in the picker (see ProgrammeViews.do_pick): the channel, and below it when and which episode.

    "2026.10.27. 23:30 | S1E10: Episode title" (Kodi's short date and the start; on now: "Now"),
    the parts it has; a coming one grey. With no channel known, that alone.
    """
    episode = {"episode_name": airing.get("episode_name")}
    if numbers:
        episode.update(season_number=numbers[0], episode_number=numbers[1])
    when = _s(30190) if on_now else localtime.local_time(airing["start_utc"])
    lines = [channel["name"], rows.with_episode(when, episode)] if channel.get("name") else [rows.with_episode(when, episode), ""]
    li = xbmcgui.ListItem(lines[0] if can_play else rows.greyed(lines[0]))
    li.setLabel2(lines[1])
    li.setArt({"icon": channel.get("logo") or "", "thumb": channel.get("logo") or ""})
    return li

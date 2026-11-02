"""Continue watching: where watching back was left off, here or in the provider's apps."""

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.data import channellist
from resources.lib.data import continuelist
from resources.lib.data import guidedata
from resources.lib.views import listing
from resources.lib.views import rows

_s = kodiutil.string
_log = kodiutil.log


class ContinueViews:
    """Continue watching (see plugin.ROUTES).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_continue(self):
        """List where watching back was left off, here or in the provider's apps (the web's "Lejátszás folytatása").

        Those watched to their end or reset here stay greyed out below the others until they leave
        catch-up (see continuelist). No row says until when: the provider does not say (see continuelist.on_catchup).
        """
        channels = channellist.by_station(self._call.client)
        marks = []
        for mark, state in continuelist.rows(continuelist.catchup(self._call.client.bookmarks(details=True))):
            marked = guidedata.from_bookmark_id(mark["id"])
            channel = channels.get(marked[0])
            if channel:
                marks.append((mark, marked, channel, state))
        self._call.laps("lists")  # timed apart from the pages, for the log
        self._log_catchup([(mark, state) for mark, _, _, state in marks])
        # The provider's list has no plots, types or years: the info pages have them.
        pages = listing.pages(self._call, [("program", mark.get("program_id")) for mark, _, _, _ in marks])
        plots = {key: page.get("plot") or "" for key, page in pages.items()}
        cast = rows.cast_of(pages, kodiutil.cast_kinds())
        for mark, marked, channel, state in marks:
            _, start, end = marked
            page = pages.get(("program", mark.get("program_id"))) or {}
            year = page.get("year") if page.get("type") == "movie" else None
            label = rows.with_episode(rows.film_title(mark.get("title") or "?", year), mark)
            active = state == continuelist.ACTIVE
            li = xbmcgui.ListItem(label if active else rows.greyed(label))
            # The rows show a resume icon, the side panel the 2:3 poster, the background the 16:9 picture.
            # No thumb: Estuary's info page would put the poster over itself for a video or an episode.
            poster = guidedata.poster("program", mark.get("program_id"))
            art = {"fanart": guidedata.fanart(mark) or mark.get("thumbnail"), "poster": poster}
            rows.set_art(li, art)
            tag = li.getVideoInfoTag()
            tag.setTitle(mark.get("title") or "")
            if year:  # Estuary's info page puts it after the title
                tag.setYear(year)
            tag.setPlot(plots.get(("program", mark.get("program_id"))) or "")
            tag.setStudios([channel["name"]])
            rows.set_credits(tag, cast.get(("program", mark.get("program_id"))))
            numbers = guidedata.season_episode(mark)
            if numbers:  # an episode: the info page says "season x episode"
                tag.setMediaType("episode")
                tag.setSeason(numbers[0])
                tag.setEpisode(numbers[1])
            elif page.get("type") == "movie":
                tag.setMediaType("movie")
            rows.set_mpaa(tag, mark.get("ratings"))
            # The row's icon: resume (from the position, whether or not the row plays itself); a greyed
            # one has no position: Kodi's tick if watched to its end, none if reset here.
            if active:
                tag.setResumePoint(float(mark.get("time_seconds") or 0), float(mark.get("runtime_seconds") or 0))
            else:
                tag.setPlaycount(1 if state == continuelist.WATCHED else 0)
            rows.set_length(tag, int(mark.get("runtime_seconds") or 0))
            # An action, as the favourites' pickers: a click opens the picker (see do_continue_pick).
            li.setProperty("IsPlayable", "false")
            li.addContextMenuItems(self._menu(mark, active))
            rows.hide_kodi_favourites(li)
            programme = {"start_time": start, "end_time": end, "content_flags": ["ct"], "ratings": mark.get("ratings")}
            # KODI_RESUME: Kodi's own "Resume" / "Play" (context menu, info page) say which.
            param = guidedata.param(programme, known_age=False, then=guidedata.KODI_RESUME)
            at = int(float(mark.get("time_seconds") or 0))
            if active:
                url = self._call.url(
                    action="continue_pick", id=channel["id"], media=channel["media_id"], programme=param, mark=mark["id"], at=at
                )
            else:  # nothing to resume: a click plays it from its beginning, without asking
                url = self._call.url(
                    action="continue_pick", id=channel["id"], media=channel["media_id"], programme=param, start=1
                )
            xbmcplugin.addDirectoryItem(self._call.handle, url, li, isFolder=False)
        xbmcplugin.setContent(self._call.handle, "videos")
        rows.show_right_labels(self._call.handle)
        xbmcplugin.endOfDirectory(self._call.handle, cacheToDisc=False)

    def _menu(self, mark, active):
        """Return a row's context menu items: onto the favourite programmes; a greyed row's removal."""
        menu = []
        if mark.get("program_id"):  # the list names no series: the programme itself, as its web page's heart
            watch = self._call.url(action="watch", id=mark["program_id"], kind="program", on=1)
            # Kodi's words, its own favourites item off (as on the favourites' rows).
            menu.append((kodiutil.kodi_string(14076), "RunPlugin(%s)" % watch))
        if not active:  # no position to reset: the row itself goes, if wanted
            menu.append((_s(30263), "RunPlugin(%s)" % self._call.url(action="continue_remove", mark=mark["id"])))
        return menu

    def _log_catchup(self, listed):
        """Log whether each row's airing is still on catch-up by its programme's airings.

        Whether those are the provider's word on it the log tells: compared with what playing the row says.
        TODO: show a row as expired (and count them in the main menu) once the log shows these answers right.
        """
        for mark, state in listed:
            if not mark.get("program_id"):
                continue
            try:
                back = self._call.client.airings(mark["program_id"], "program")[0]
            except provider.ApiError as e:
                _log("catch-up of %s unknown: %s" % (mark["id"], e), xbmc.LOGDEBUG)
                continue
            _log(
                "catch-up of %s (%s, %s): %s, by its programme's %d catch-up airings"
                % (mark["id"], mark.get("title"), state, "on" if continuelist.on_catchup(mark, back) else "gone", len(back)),
                xbmc.LOGDEBUG,
            )
        self._call.laps("catch-up")

    def do_continue_pick(self):
        """Resume, play from the beginning or reset the position of a Continue watching row.

        Kodi's own resume question has only its two buttons; this one adds the reset, in Kodi's own
        words. Kodi's own "Resume" / "Play" (context menu, info page) play at once, as Kodi asks.
        """
        from resources.lib.views import play  # here: only a pick may play at once

        if self._call.params.get("start"):  # a greyed row: from its beginning, at once
            params = self._continue_play(guidedata.from_beginning(self._call.params["programme"]))
            if self._call.handle >= 0:
                return play.resolve(self._call, params)
            xbmc.executebuiltin("PlayMedia(%s)" % self._call.url(**params))
            return None
        if self._call.handle >= 0:  # Kodi waits for the stream; the programme already has its answer
            return play.resolve(self._call, self._continue_play(self._call.params["programme"]))
        if listing.opened_by_select_action():
            return None
        resume = kodiutil.kodi_string(12022)  # "Resume from {0:s}"
        at = kodiutil.clock(int(self._call.params.get("at") or 0))
        choices = [
            resume.format(at) if "{0" in resume else "%s %s" % (resume, at),
            kodiutil.kodi_string(12021),
            kodiutil.kodi_string(38209),
        ]
        choice = xbmcgui.Dialog().contextmenu(choices)
        if choice in (0, 1):
            tail = guidedata.continued if choice == 0 else guidedata.from_beginning
            xbmc.executebuiltin("PlayMedia(%s)" % self._call.url(**self._continue_play(tail(self._call.params["programme"]))))
        elif choice == 2:
            self._reset_position()
        return None

    def _continue_play(self, programme):
        return {"action": "play", "id": self._call.params["id"], "media": self._call.params["media"], "programme": programme}

    def do_continue_remove(self):
        """Take a row off Continue watching for good (a greyed row's context menu, an expired airing's question).

        Its position too, if the account still has one; the list shown again.
        """
        mark = self._account_mark()
        if mark:
            self._delete_position(mark)
        continuelist.drop(self._call.params["mark"])
        xbmc.executebuiltin("Container.Refresh")

    def _reset_position(self):
        """Remove the row's position from the account's Continue watching, then show the list again.

        The row stays, greyed out (see continuelist).
        """
        mark = self._account_mark()
        if mark:
            self._delete_position(mark)
            continuelist.set_removed(mark)
        xbmc.executebuiltin("Container.Refresh")

    def _account_mark(self):
        """Return the account's position of the call's row ("mark"); None if it has none."""
        return next((b for b in self._call.client.bookmarks(details=True) if b.get("id") == self._call.params["mark"]), None)

    def _delete_position(self, mark):
        """Delete a position: through the web's own delete; failing that, a position at the start, which the list leaves out."""
        try:
            self._call.client.delete_bookmarks([mark])
        except provider.ApiError as e:
            _log("deleting the position failed (%s): saving it at the start" % e, xbmc.LOGWARNING)
            station, start, end = guidedata.from_bookmark_id(mark["id"])
            # A removal comes without the channel's media id (an expired airing's question): its channel's.
            media = self._call.params.get("media") or channellist.by_station(self._call.client).get(station, {}).get(
                "media_id", ""
            )
            info = {"id": mark["id"], "program_id": mark.get("program_id", ""), "media_id": media}
            info.update(start_time=start, end_time=end, station_id=station)
            self._call.client.set_bookmark(info, 0, mark.get("runtime_seconds") or 0)

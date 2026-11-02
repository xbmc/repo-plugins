"""Live channels: one row per channel, the programme on air and the next one; a click plays it."""

import time

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.data import guidedata
from resources.lib.views import listing
from resources.lib.views import rows

_s = kodiutil.string
_log = kodiutil.log
# Set while a channel list is being made (when it began), across the plugin's interpreters (see do_channels).
LISTING = "%s.channels_listing" % kodiutil.ADDON_ID
# Seconds after which such a mark is a crashed listing's, not one still running.
LISTING_STALE = 30


class ChannelViews:
    """Live channels (see plugin.ROUTES).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call
        self.playing = None  # the channel last handed to Kodi to play, while something plays

    def do_channels(self):
        """List the live channels, every one (the public ones without a login), in the default order of channellist.grouped.

        One at a time: back from the full screen after a stop, Kodi asks for the list twice at once
        (its own reload, then another 0.1 s later, seen 2026-11-02), and showed both answers in one list
        (each channel twice). The later of two at once ends at once as failed: Kodi keeps the one made.
        """
        home = kodiutil.home()
        began = home.getProperty(LISTING)
        if began and time.time() - float(began) < LISTING_STALE:
            _log("channel list asked for again while one is being made: this one ends", xbmc.LOGDEBUG)
            xbmcplugin.endOfDirectory(self._call.handle, succeeded=False)
            return
        home.setProperty(LISTING, str(time.time()))
        try:
            self._list_channels()
        finally:
            home.clearProperty(LISTING)

    def _list_channels(self):
        view = listing.list_view(self._call)
        now, following = view["now"], view.get("next") or {}
        subscribed = None if view["subscribed"] is None else set(view["subscribed"])
        favourites = None if view["favourites"] is None else set(view["favourites"])
        off = set(view.get("deactivated") or ())
        trusted = not kodiutil.untrusted_widevine()
        from resources.lib.data import infopages

        # Cast only for the programme types the settings want it of (none: no page fetched).
        cast_kinds = kodiutil.cast_kinds()
        on_air = [now.get(c["station_id"]) or {} for c in view["channels"]]
        wanted = [key for p in on_air if guidedata.kind(p) in cast_kinds for key in infopages.keys_of(p)]
        cast = rows.cast_of(listing.pages(self._call, wanted), cast_kinds)
        # The channel last handed to Kodi to play, while something plays (the service drops it once none of ours does).
        from resources.lib.service import quickplay

        self.playing = kodiutil.home().getProperty(quickplay.PLAYING) if xbmc.Player().isPlaying() else None

        for position, c in enumerate(view["channels"]):
            deactivated = str(c["id"]) in off
            if deactivated or (subscribed is not None and c["id"] not in subscribed):
                # Greyed out: its name and why (see My channels), no programme. A click says why: that
                # it is deactivated, or which package it is in.
                li = self._greyed_item(c, _s(30236) if deactivated else rows.not_available(), position)
                li.addContextMenuItems(self._favourite_menu(c, favourites) if favourites is not None else [])
                url = (
                    self._call.url(action="deactivated")
                    if deactivated
                    else self._call.url(action="not_subscribed", station=c["station_id"])
                )
                xbmcplugin.addDirectoryItem(self._call.handle, url, li, isFolder=False)
                continue
            prog = now.get(c["station_id"]) or {}
            li = self.channel_item(c, prog, following.get(c["station_id"]), trusted, position)
            rows.set_credits(li.getVideoInfoTag(), infopages.programme_credits(prog, cast))
            menu = self._channel_menu(c, prog, favourites) if favourites is not None else []
            # From its beginning where the web player allows it, in Kodi's words ("Play from beginning").
            if trusted and prog.get("start_time") and "rn" not in (prog.get("content_flags") or []):
                restart = self._call.url(action="play", id=c["id"], media=c["media_id"], programme=guidedata.param(prog))
                menu.insert(0, (kodiutil.kodi_string(12021), "PlayMedia(%s)" % restart))
            li.addContextMenuItems(menu)
            xbmcplugin.addDirectoryItem(
                self._call.handle, self._call.url(action="play", id=c["id"], media=c["media_id"]), li, isFolder=False
            )
        self._call.laps("items")
        # No content type: only then does Estuary's wide list draw the item's icon (the logo); such rows
        # have no right-hand label, hence the second line (see channel_item).
        rows.add_channel_sorts(self._call.handle)
        xbmcplugin.endOfDirectory(self._call.handle)
        self._call.laps("shown")

    def do_deactivated(self):
        """Say why a deactivated channel's row does not play (a click on it in Live channels)."""
        self._call.decline_play()
        xbmcgui.Dialog().ok(kodiutil.name(), _s(30232))

    def do_not_subscribed(self):
        """Say which package a channel outside the subscription is in, the cheapest (a click on its row in Live channels).

        Asked only now: the channel list does not say, a programme of the channel does (see client.offers).
        """
        self._call.decline_play()
        from resources.lib.data import onair

        offers = []
        try:
            programme = onair.on_air(self._call.client, self._call.params.get("station"), time.time())[0]
            if programme and programme.get("program_id"):
                offers = [
                    o
                    for o in self._call.client.offers(programme["program_id"])
                    if o.get("package_name") and o.get("price") is not None
                ]
        except provider.ApiError as e:
            _log("the channel's packages are unknown: %s" % e)
        if not offers:
            xbmcgui.Dialog().ok(kodiutil.name(), _s(30139))
            return
        cheapest = min(offers, key=lambda o: float(o["price"]))
        price = float(cheapest["price"])
        xbmcgui.Dialog().ok(kodiutil.name(), _s(30241) % (cheapest["package_name"], "%g" % price))

    def _greyed_item(self, c, status, position):
        """Return a row of a channel that does not play here: its name and beside it why; greyed out.

        Deactivated or outside the subscription: no programme, so nothing of the guide is read for it.
        """
        li = xbmcgui.ListItem(rows.with_note(rows.greyed(c["name"]), status))
        rows.set_art(li, {"thumb": rows.panel_logo(c["logo"]), "icon": c["logo"]})
        # The sort keys only, no title: a titled row is "playable" to Kodi, which offers its own Play.
        rows.set_channel_sort_keys(li.getVideoInfoTag(), c, position)
        rows.hide_kodi_favourites(li)
        li.setProperty("IsPlayable", "false")
        return li

    def _favourite_menu(self, c, favourites):
        """Return the context menu item that puts a channel onto the account's favourites or off them."""
        on = c["id"] not in favourites
        action = "RunPlugin(%s)" % self._call.url(action="favourite", number=c["number"], on=int(on))
        return [(rows.favourite_channel_item(on), action)]

    def channel_item(self, c, prog, following, playable, position):
        """Return a channel's row: the programme on air, in its channel's category colour.

        `following` (if known) is the second line. Where it cannot play (Windows/macOS), a click
        only shows why, with no stream session opened.
        """
        # The logo is in the row and the channel name on the info page: the label is the programme alone.
        # The channel playing: selected, in the skin's own colour for it (no category colour over it).
        playing = c.get("id") is not None and c.get("id") == self.playing
        colour = None if playing else guidedata.channel_colour(c) if self._call.colours else None
        title = rows.row_title(prog) if prog.get("description") else c["name"]
        label = kodiutil.coloured(colour, title) if colour else title
        if following:
            # In Kodi's words ("Next"), all of it grey and italic below the programme on now.
            label += "[CR][I]%s[/I]" % rows.greyed(
                "%s: %s - %s: %s"
                % (
                    kodiutil.kodi_string(19031),
                    kodiutil.local_time(following["start_time"], date=False),
                    kodiutil.local_time(following["end_time"], date=False),
                    rows.with_episode(following.get("description") or "", following),
                )
            )
        li = xbmcgui.ListItem(label)
        if playing:  # as Kodi TV's channel list marks the one playing
            li.select(True)
        # The thumb (the logo) is the row's and, without a poster, the side panel's. No fanart: behind
        # the list it made the rows hard to read.
        art = {"thumb": rows.panel_logo(c["logo"]), "icon": c["logo"]}
        if prog and prog.get("program_id"):
            # Estuary's info page only (its side panel ignores tvshow.poster): the 2:3 poster, with the
            # thumb over it for a video or an episode.
            art["tvshow.poster"] = guidedata.poster("program", prog["program_id"])
        rows.set_art(li, art)
        tag = li.getVideoInfoTag()
        tag.setTitle(prog.get("episode_name") or prog.get("description") or c["name"])
        rows.set_channel_sort_keys(tag, c, position)
        rows.hide_kodi_favourites(li)
        rows.set_programme_extras(tag, prog)
        # Never "watched": Kodi counts a live stream as played to its end and keeps that by its address;
        # an item that sets its own play count is not given the kept one.
        tag.setPlaycount(0)
        tag.setPlot(prog.get("full_description") or prog.get("description") or "")
        tag.setGenres([g["name"] for g in prog.get("genres") or [] if g.get("name")])
        rows.set_mpaa(tag, prog.get("ratings"))
        # The played item's type (see playitem), but a movie is a video: Estuary's info page puts the
        # logo over the poster only for a video or an episode.
        kind = guidedata.kind(prog) if prog else None
        numbers = guidedata.season_episode(prog)
        episodic = bool(numbers or prog.get("episode_name"))
        if not c.get("radio"):  # a radio has no type of Kodi's: none, rather than its info page saying "video"
            tag.setMediaType(guidedata.media_type("other" if kind == "movie" else kind, episodic))
        if guidedata.year(prog):
            tag.setYear(guidedata.year(prog))
        if episodic or kind == "series":
            tag.setTvShowTitle(prog.get("description") or "")
            if numbers:
                tag.setSeason(numbers[0])
                tag.setEpisode(numbers[1])
        li.setProperty("IsPlayable", "true" if playable else "false")
        return li

    def _channel_menu(self, c, prog, favourites):
        """Return a channel's context menu for a logged-in account.

        Favourite channels, and the programme on air onto the favourite programmes (a series as a
        whole, a movie itself). The channel order is My channels' (see views.mychannels).
        """
        menu = self._favourite_menu(c, favourites)
        kind = guidedata.kind(prog)
        if prog.get("series_id") and kind == "series":
            menu.append((_s(30171), "RunPlugin(%s)" % self._call.url(action="watch", id=prog["series_id"], kind="series", on=1)))
        elif prog.get("program_id") and kind == "movie":
            menu.append(
                (_s(30171), "RunPlugin(%s)" % self._call.url(action="watch", id=prog["program_id"], kind="program", on=1))
            )
        return menu

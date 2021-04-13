import os
import sys
import pickle
from urllib.parse import urlparse, parse_qsl
from xbmcvfs import translatePath
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, addSortMethod, \
        endOfDirectory, setResolvedUrl, SORT_METHOD_LABEL, SORT_METHOD_DATE, \
        SORT_METHOD_NONE, SORT_METHOD_LABEL_IGNORE_THE, \
        SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE
from xbmcaddon import Addon
from xbmc import Keyboard
from resources.lib.utils import get_page_json, time_to_seconds, convert_date_to_kodi_format


class Eventvods():

    addon = Addon()
    localize = addon.getLocalizedString

    games = [{"name": localize(30003), "slug": "lol"},
             {"name": localize(30004), "slug": "dota"},
             {"name": localize(30005), "slug": "csgo"},
             {"name": localize(30006), "slug": "overwatch"},
             {"name": localize(30007), "slug": "valorant"},
             {"name": localize(30008), "slug": "pubg1"},
             {"name": localize(30009), "slug": "rocket-league"}]

    game_submenu_items = [{"label": localize(30017), "action": "listeventsubmenu"},
                          {"label": localize(30031), "action": "listteamalphas"}]

    event_submenu_items = [{"label": localize(30011), "action": "listyears",
                            "mode": "all"},
                           {"label": localize(30010), "action": "listevents",
                            "mode": "featured"},
                           {"label": localize(30029), "action": "listevents",
                            "mode": "search"}]

    match_url = "https://eventvods.com/api/match/"
    events_url = "https://eventvods.com/api/events"
    event_url = "https://eventvods.com/api/events/slug/"
    featured_url = "https://eventvods.com/api/featured"
    teams_url = "https://eventvods.com/api/teams"
    team_url = "https://eventvods.com/api/teams/slug/"

    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    addon_name = Addon().getAddonInfo("name")

    # For caching class state between addon calls
    cache = translatePath(addon.getAddonInfo("profile") + "cache/")
    resources = translatePath(addon.getAddonInfo("path") + "resources/media/")

    YOUTUBE = 0
    TUBED = 1

    os.makedirs(cache, exist_ok=True)


    def _add_folder_item(self, items, title, url, icon_url, fanart_url,
                         sort_title="", isfolder=True, isplayable=False,
                         date=None, info=None, context_menu_items=None):

        li = ListItem(label=title)
        li.setArt({"thumb": icon_url, "fanart": fanart_url})
        li.setInfo("video", {"title": title, "sorttitle": sort_title})

        if isplayable:
            li.setProperty("IsPlayable", "true")
        else:
            li.setProperty("IsPlayable", "false")

        if date is not None:
            li.setInfo("video", {"date": date})

        if info is not None:
            li.setInfo("video", {"plot": info})

        if context_menu_items is not None:
            li.addContextMenuItems(context_menu_items)

        items.append((url, li, isfolder))


    def _end_folder(self, items, sort_methods=()):
        addDirectoryItems(self.addon_handle, items, totalItems=len(items))

        for sort_method in sort_methods:
            addSortMethod(self.addon_handle, sort_method)

        endOfDirectory(self.addon_handle)


    def main_list(self):
        items = []
        for game_id in range(len(self.games)):
            game_name = self.games[game_id]["name"]
            url = "{0}?action=listgamesubmenu&game_id={1}". \
                format(self.addon_url, game_id)
            icon = os.path.join(self.resources, self.games[game_id]["slug"] + ".png")
            fanart = os.path.join(self.resources, self.games[game_id]["slug"] + ".jpg")

            self._add_folder_item(items, game_name, url, icon, fanart)

        self._end_folder(items, sort_methods=(SORT_METHOD_LABEL,))


    def main_game_sublist(self, game_id):
        self.game_id = int(game_id)
        self.game_slug = self.games[self.game_id]["slug"]
        self.game_icon = os.path.join(self.resources, self.game_slug + ".png")
        self.game_fanart = os.path.join(self.resources, self.game_slug + ".jpg")

        items = []
        for menu_item in self.game_submenu_items:
            url = "{0}?action={1}".format(self.addon_url,
                                          menu_item["action"])

            self._add_folder_item(items, menu_item["label"], url, self.game_icon,
                             self.game_fanart)

        self._end_folder(items, sort_methods=(SORT_METHOD_LABEL,))


    def main_event_sublist(self):
        items = []
        for menu_item in self.event_submenu_items:
            url = "{0}?action={1}&mode={2}".format(self.addon_url,
                                                   menu_item["action"],
                                                   menu_item["mode"])

            self._add_folder_item(items, menu_item["label"], url, self.game_icon,
                                  self.game_fanart)

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def team_list_alphabetical(self):
        teams = get_page_json(self.teams_url)

        items = []
        self.team_labels = {}
        for team in teams:
            if team["game"]["slug"] == self.game_slug:
                try:
                    team_name = team["name"]
                    if not isinstance(team_name, str):
                        raise ValueError
                except (AttributeError, KeyError, ValueError):
                    continue

                if team_name[:4].lower() == "the ":
                    team_label = team_name[4:5].upper()
                elif team_name[:5].lower() == "team ":
                    team_label = team_name[5:6].upper()
                else:
                    team_label = team_name[0:1].upper()

                if team_label.isdigit():
                    team_label = "0-9"

                if team_label not in self.team_labels:
                    self.team_labels[team_label] = []
                    url = "{0}?action=listteams&teamlabel={1}".format(
                        self.addon_url, team_label)

                    self._add_folder_item(items, team_label, url, self.game_icon,
                                          self.game_fanart)

                self.team_labels[team_label].append(team)

        self._end_folder(items, sort_methods=(SORT_METHOD_LABEL,))


    def team_list(self, team_label):
        self.team_label = team_label
        items = []
        for team in self.team_labels[team_label]:
            url = "{0}?action=listteammatches&teamslug={1}". \
                    format(self.addon_url, team["slug"])
            try:
                title = team["name"]
                if team["name"][:5].lower() != "team ":
                    sort_title = team["name"]
                else:
                    sort_title = team["name"][5:]
            except KeyError:
                continue

            try:
                team_icon = team["icon"]
            except KeyError:
                team_icon = self.game_icon

            self._add_folder_item(items, title, url, team_icon,
                                  self.game_fanart, sort_title=sort_title)

        self._end_folder(items,
                         sort_methods=(SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE,))


    def team_match_list(self, team_slug):
        teams_json = get_page_json(self.team_url + team_slug)

        correct_team_found = False
        for team_data in teams_json: # Teams may play different games
            try:
                if team_data["game"]["slug"] == self.games[self.game_id]["slug"]:
                    self.team_data = team_data
                    correct_team_found = True
                    break
            except (TypeError, AttributeError, KeyError):
                continue

        if not correct_team_found:
            return

        self.map_icon = self.game_icon

        items = []
        try:
            for match in self.team_data["matches"]:
                try:
                    date = match["date"]
                except (AttributeError, KeyError):
                    date = None

                try:
                    team_1 = match["team1"]["name"]
                    team_2 = match["team2"]["name"]
                except KeyError:
                    team_1 = "{0}".format(team_data["name"])
                    team_2 = "{0} B".format(self.localize(30012))

                try:
                    if match["team2"]["name"] != team_data["name"]:
                        self.match_icon = match["team2"]["icon"]
                    else:
                        self.match_icon = match["team1"]["icon"]
                except KeyError:
                    self.match_icon = self.game_icon

                try:
                    url = "{0}?action=listmaps&match_id={1}&game={2}". \
                        format(self.addon_url, match["_id"],
                               self.game_slug)
                except (AttributeError, KeyError):
                    continue

                title = "{0} vs {1}".format(team_1, team_2)

                match_info_url = "{0}?action=contextmatchinfo&match_id={1}". \
                    format(self.addon_url, match["_id"])

                context_menu = [(self.localize(30028),
                                 "RunPlugin({0})".format(match_info_url))]

                self._add_folder_item(items, title, url, self.match_icon,
                                      self.game_fanart,
                                      context_menu_items=context_menu)

        except (AttributeError, KeyError):
            return

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def year_list(self, mode):
        self.events = get_page_json(self.events_url)

        items = []
        years = []
        for event in self.events:
            year = event["startDate"].split("-")[0]
            if (year not in years
                and event["game"]["slug"] == self.game_slug):

                url = "{0}?action=listevents&year={1}&mode={2}". \
                    format(self.addon_url, year, mode)
                self._add_folder_item(items, year, url, self.game_icon,
                                      self.game_fanart)
                years.append(year)

        self._end_folder(items, sort_methods=(SORT_METHOD_DATE,))


    def event_list(self, mode, year=None):


        def correct_game_found(event):
            return event["game"]["slug"] == self.game_slug


        def correct_year(event):
            return year == event["startDate"].split("-")[0]


        def search_match(event, query):
            query = query.lower()
            return query != "" and \
                (query in event["name"].lower() or
                 query in event["slug"].lower() or
                 query in event["startDate"])


        query = ""
        if mode == "all":
            pass
        elif mode == "featured":
            self.events = get_page_json(self.featured_url)["events"]
        elif mode == "search":
            self.events = get_page_json(self.events_url)
            query = self.get_user_input(prompt_msg=self.localize(30030))
        else:
            return

        items = []
        for event in self.events:
            if (correct_game_found(event) and
                (correct_year(event) or
                search_match(event, query) or
                mode == "featured")):

                url = "{0}?action=listweeks&slug={1}&spoilmatches={2}". \
                    format(self.addon_url, event["slug"], False)
                if event["status"] == "Ongoing":
                    title = "[COLOR green]{0}[/COLOR]".format(event["name"])
                elif event["status"] == "Upcomming":
                    title = "[COLOR blue]{0}[/COLOR]".format(event["name"])
                else:
                    title = event["name"]

                kodi_date = convert_date_to_kodi_format(event["endDate"])

                teamlist_url = "{0}?action=contextlistteams&slug={1}". \
                    format(self.addon_url, event["slug"])
                hostlist_url = "{0}?action=contextlisthosts&slug={1}". \
                    format(self.addon_url, event["slug"])
                info_url = "{0}?action=contexteventinfo&slug={1}". \
                    format(self.addon_url, event["slug"])
                spoil_url = "{0}?action=listweeks&slug={1}&spoilmatches={2}". \
                    format(self.addon_url, event["slug"], True)


                context_menu = [(self.localize(30015),
                                 "ActivateWindow(videos, {0}, return)"\
                                 .format(teamlist_url)),
                                (self.localize(30016),
                                 "ActivateWindow(Videos, {0}, return)"\
                                 .format(hostlist_url)),
                                (self.localize(30019),
                                 "RunPlugin({0})".format(info_url)),
                                (self.localize(30027),
                                 "ActivateWindow(Videos, {0}, return)" \
                                 .format(spoil_url))]


                self._add_folder_item(items, title, url, event["logo"],
                    self.game_fanart, date=kodi_date,
                    info=event["progress_days"]["msg"],
                    context_menu_items=context_menu)

        self._end_folder(items, sort_methods=(SORT_METHOD_DATE,))


    def context_team_list(self, slug):
        self.event = get_page_json(self.event_url + slug)

        items = []
        for team in self.event["teams"]:
            url = "{0}?action=listeventteammatch&team={1}". \
                format(self.addon_url, team["name"])
            self._add_folder_item(items, team["name"], url, team["icon"],
                                  self.game_fanart, isfolder=False)

        self._end_folder(items, sort_methods=(SORT_METHOD_LABEL,))


    def context_hosts_list(self, slug):
        event = get_page_json(self.event_url + slug)

        try:
            staff = event["staff"]
        except (AttributeError, KeyError):
            Dialog().ok(self.addon_name, self.localize(30024))
            return

        items = []
        for person in staff:
            url = "{0}?action=noop"
            try:
                item_label = "{0} ({1})".format(person["name"], person["role"])
            except (AttributeError, KeyError):
                continue
            li = ListItem(label=item_label)
            try:
                icon = person["photo"]
            except KeyError:
                try:
                    icon = event["logo"]
                except KeyError:
                    icon = self.game_icon

            self._add_folder_item(items, item_label, url, icon,
                                  self.game_fanart, isfolder=False)

        self._end_folder(items, sort_methods=(SORT_METHOD_LABEL_IGNORE_THE,))


    def context_event_info(self, slug):
        event = get_page_json(self.event_url + slug)
        try:
            info_str = event["format"]
        except (AttributeError, KeyError):
            info_str = self.localize(30020)

        Dialog().textviewer(self.addon_name, info_str)


    def context_match_info(self, match_id):
        match_json = get_page_json(self.match_url + match_id)

        info_str = ""
        try:
            info_str = "{0}: {1}\n".format(self.localize(30026),
                                           match_json["event"]["name"])
        except (TypeError, AttributeError, KeyError):
            pass

        try:
            info_str = info_str + "{0} vs {1}\n". \
                format(match_json["team1"]["name"],
                       match_json["team2"]["name"])
        except (TypeError, AttributeError, KeyError):
            pass

        if info_str != "":
            Dialog().textviewer(self.addon_name, info_str)
        else:
            Dialog().textviewer(self.addon_name, self.localize(30023))


    def week_list(self, event_slug, spoil_matches, team=None):
        self.spoil_matches = spoil_matches
        self.event_slug = event_slug
        
        self.weeks = get_page_json(self.event_url + event_slug)
        self.event_logo = self.weeks["logo"]

        items = []
        for (week_number, week) in enumerate(self.weeks["contents"]):
            url = "{0}?action=listdays&week={1}". \
                format(self.addon_url, week_number)

            try:
                title = week["title"]
            except KeyError:
                continue

            self._add_folder_item(items, title, url, self.event_logo,
                                  self.game_fanart)

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def day_list(self, week):
        days = self.weeks["contents"][week]["modules"]
        self.week = week

        items = []
        for (day_number, day) in enumerate(days):
            url = "{0}?action=listmatches&week={1}&day={2}" \
                .format(self.addon_url, week, day_number)
            self._add_folder_item(items, day["title"], url, self.event_logo,
                                  self.game_fanart)

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def match_list(self, day):
        matches = self.weeks["contents"][self.week]["modules"][day]["matches2"]
        self.map_icon = self.event_logo

        items = []
        for (match_number, match) in enumerate(matches):
            match_icon = self.event_logo
            url = "{0}?action=listmaps&match_id={1}&game={2}". \
                format(self.addon_url, match["_id"],
                       self.game_slug)

            try:
                match_spoiler = not match["spoiler1"]
            except ValueError:
                match_spoiler = False

            team_spoiler = self.addon.getSettingBool("teamSpoiler")
            try:
                if team_spoiler or self.spoil_matches or match_spoiler:
                    team_1 = match["team1"]["name"]
                    team_2 = match["team2"]["name"]
                    match_icon = match["team1"]["icon"]
                else:
                    team_1 = match["team1Match"]
                    team_2 = match["team2Match"]
            except KeyError:
                team_1 = "{0} A".format(self.localize(30012))
                team_2 = "{0} B".format(self.localize(30012))

            match_info_url = "{0}?action=contextmatchinfo&match_id={1}". \
                format(self.addon_url, match["_id"])

            context_menu = [(self.localize(30028),
                             "RunPlugin({0})".format(match_info_url))]

            title = "{0} vs {1}".format(team_1, team_2)
            self._add_folder_item(items, title, url, match_icon,
                                  self.game_fanart,
                                  context_menu_items=context_menu)

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def map_list(self, match_id):
        try:
            match_json = get_page_json(self.match_url + match_id)
            match_data = match_json["data"]
        except (AttributeError, KeyError):
            Dialog().ok(self.addon_name, self.localize(30032))
            return

        items = []
        for (map_number, map_data) in enumerate(match_data):

            url = self._get_video_url(map_data)

            try:
                map_spoiler = self.addon.getSettingBool("mapSpoiler")

                if (not match_json["spoiler1"] or map_spoiler or
                        self.spoil_matches):
                    map_name = map_data["map"]
                else:
                    raise KeyError
            except KeyError:
                if self.game_slug != "csgo":
                    map_name = "{0} {1}".format(self.localize(30013),
                                                str(1+map_number))
                else:
                    map_name = "{0} {1}".format(self.localize(30014),
                                                str(1+map_number))

            self._add_folder_item(items, map_name, url, self.map_icon,
                                  self.game_fanart, isplayable=True,
                                  isfolder=False)

        self._end_folder(items, sort_methods=(SORT_METHOD_NONE,))


    def _get_video_url(self, map_data):
        urls = {}
        url = "{0}?action=play".format(self.addon_url)

        # Get youtube video info
        youtube_fail = False
        try:
            yt_video_url = map_data["youtube"]["gameStart"]
            yt_video_data = dict(parse_qsl(urlparse(yt_video_url).query))
        except (KeyError, TypeError):
            pass

        try:
            url = url + "&yt_video_id=" + yt_video_data["v"]
            if len(yt_video_data["v"]) < 2: # sanity check on video id
                raise KeyError
        except (KeyError, NameError):
            url = url + "&yt_video_id=none"
            youtube_fail = True

        try:
            url = url + "&yt_offset=" + yt_video_data["t"]
        except (KeyError, NameError):
            url = url + "&yt_offset=00s"

        # Get twitch video info
        twitch_fail = False
        try:
            tw_video_url = urlparse(map_data["twitch"]["gameStart"])
            tw_video_data = dict(parse_qsl(tw_video_url.query))
        except (KeyError, TypeError):
            pass

        try:
            tw_video_id = tw_video_url.path.split("/")[-1]
            url = url + "&tw_video_id=" + tw_video_id
            if len(tw_video_id) < 2: # sanity check on video id
                raise KeyError
        except (KeyError, IndexError, NameError):
            url = url + "&tw_video_id=none"
            twitch_fail = True

        try:
            url = url + "&tw_offset=" + tw_video_data["t"]
        except (KeyError, NameError):
            url = url + "&tw_offset=00s"

        if youtube_fail and twitch_fail:
            url = "{0}?action=noop"

        return url


    def play_youtube_video(self, video_id, offset="00s"):
        time_stamp_sec = time_to_seconds(offset)

        youtube_player = self.addon.getSettingInt("YouTubePlayer")
        if youtube_player == self.YOUTUBE:
            path = "plugin://plugin.video.youtube/play/" \
                "?video_id={0}&seek={1}&FullScreen=true". \
                format(video_id, time_stamp_sec)
        elif youtube_player == self.TUBED:
            path = "plugin://plugin.video.tubed/" \
                "?mode=play&video_id={0}&start_offset={1}". \
                format(video_id, time_stamp_sec)

        play_item = ListItem(path=path)
        setResolvedUrl(self.addon_handle, True, listitem=play_item)


    def play_twitch_video(self, video_id, offset="00s"):
        time_stamp_sec = time_to_seconds(offset)
        path = "plugin://plugin.video.twitch/" \
            "?mode=play&video_id={0}&seek_time={1}". \
            format(video_id, time_stamp_sec)

        play_item = ListItem(path=path)
        setResolvedUrl(self.addon_handle, True, listitem=play_item)


    def save_state(self):
        with open(os.path.join(self.cache, "eventstate"), "wb") as file_out:
            pickle.dump(self, file_out)


    @classmethod
    def load_state(cls):
        with open(os.path.join(cls.cache, "eventstate"), "rb") as file_in:
            return pickle.load(file_in)


    @staticmethod
    def get_user_input(prompt_msg=""):
        keyboard = Keyboard("", prompt_msg)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return ""

        input_str = keyboard.getText()
        return input_str

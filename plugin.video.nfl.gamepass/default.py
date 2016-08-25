# -*- coding: utf-8 -*-
"""
A Kodi addon/skin for NFL Game Pass
"""
import calendar
from datetime import datetime
import os
import sys
import time
from traceback import format_exc

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.pigskin import pigskin

addon = xbmcaddon.Addon()
language = addon.getLocalizedString
ADDON_PATH = xbmc.translatePath(addon.getAddonInfo('path'))
ADDON_PROFILE = xbmc.translatePath(addon.getAddonInfo('profile'))
LOGGING_PREFIX = '[%s-%s]' % (addon.getAddonInfo('id'), addon.getAddonInfo('version'))

if not xbmcvfs.exists(ADDON_PROFILE):
    xbmcvfs.mkdir(ADDON_PROFILE)

cookie_file = os.path.join(ADDON_PROFILE, 'cookie_file')
username = addon.getSetting('email')
password = addon.getSetting('password')
if addon.getSetting('debug') == 'false':
    debug = False
else:
    debug = True

proxy_config = None
if addon.getSetting('proxy_enabled') == 'true':
    proxy_config = {
        'scheme': addon.getSetting('proxy_scheme'),
        'host': addon.getSetting('proxy_host'),
        'port': addon.getSetting('proxy_port'),
        'auth': {
            'username': addon.getSetting('proxy_username'),
            'password': addon.getSetting('proxy_password'),
        },
    }
    if addon.getSetting('proxy_auth') == 'false':
        proxy_config['auth'] = None

gpr = pigskin(proxy_config, cookie_file=cookie_file, debug=debug)


def addon_log(string):
    if debug:
        xbmc.log("%s: %s" % (LOGGING_PREFIX, string))


class GamepassGUI(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.season_list = None
        self.season_items = []
        self.clicked_season = -1
        self.weeks_list = None
        self.weeks_items = []
        self.clicked_week = -1
        self.games_list = None
        self.games_items = []
        self.clicked_game = -1
        self.live_list = None
        self.live_items = []
        self.selected_season = ''
        self.selected_week = ''
        self.main_selection = None
        self.player = None
        self.list_refill = False
        self.focusId = 100
        self.seasons_and_weeks = gpr.get_seasons_and_weeks()

        xbmcgui.WindowXML.__init__(self, *args, **kwargs)
        self.action_previous_menu = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)

    def onInit(self):  # pylint: disable=invalid-name
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.season_list = self.window.getControl(210)
        self.weeks_list = self.window.getControl(220)
        self.games_list = self.window.getControl(230)
        self.live_list = self.window.getControl(240)

        if gpr.subscription == 'domestic':
            self.window.setProperty('domestic', 'true')

        if self.list_refill:
            self.season_list.reset()
            self.season_list.addItems(self.season_items)
            self.weeks_list.reset()
            self.weeks_list.addItems(self.weeks_items)
            self.games_list.reset()
            self.games_list.addItems(self.games_items)
            self.live_list.reset()
            self.live_list.addItems(self.live_items)
        else:
            self.window.setProperty('NW_clicked', 'false')
            self.window.setProperty('GP_clicked', 'false')

        xbmc.executebuiltin("Dialog.Close(busydialog)")

        try:
            self.setFocus(self.window.getControl(self.focusId))
        except:
            addon_log('Focus not possible: %s' % self.focusId)

    def coloring(self, text, meaning):
        """Return the text wrapped in appropriate color markup."""
        if meaning == "disabled":
            color = "FF000000"
        elif meaning == "disabled-info":
            color = "FF111111"
        colored_text = "[COLOR=%s]%s[/COLOR]" % (color, text)
        return colored_text

    def display_seasons(self):
        """List seasons"""
        self.season_items = []
        for season in sorted(self.seasons_and_weeks.keys(), reverse=True):
            listitem = xbmcgui.ListItem(season)
            self.season_items.append(listitem)

        self.season_list.addItems(self.season_items)

    def display_nfln_seasons(self):
        """List seasons"""
        self.season_items = []
        # sort so that years are first (descending) followed by text
        for season in sorted(gpr.nflnSeasons, key=lambda x: (x[0].isdigit(), x), reverse=True):
            listitem = xbmcgui.ListItem(season)
            self.season_items.append(listitem)

        self.season_list.addItems(self.season_items)

    def display_nfl_network_archive(self):
        """List shows for a given season"""
        self.weeks_items = []
        shows = gpr.get_shows(self.selected_season)
        for show_name in shows:
            listitem = xbmcgui.ListItem(show_name)
            self.weeks_items.append(listitem)

        self.weeks_list.addItems(self.weeks_items)

    def display_weeks_games(self):
        """Show games for a given season/week"""
        self.games_items = []
        games = gpr.get_weeks_games(self.selected_season, self.selected_week)

        date_time_format = '%Y-%m-%dT%H:%M:%S.000'
        for game in games:
            if game['homeTeam']['id'] is None:  # sometimes the first item is empty
                continue

            game_info = ''
            game_id = game['id']
            game_versions = []
            isPlayable = 'true'
            isBlackedOut = 'false'
            home_team = game['homeTeam']
            away_team = game['awayTeam']

            # Pro-bowl doesn't have a team "name" only a team city, which is the
            # team name... wtf
            if game['homeTeam']['name'] is None:
                game_name_shrt = '[B]%s[/B] at [B]%s[/B]' % (away_team['city'], home_team['city'])
                game_name_full = game_name_shrt
            else:
                game_name_shrt = '[B]%s[/B] at [B]%s[/B]' % (away_team['name'], home_team['name'])
                game_name_full = '[B]%s %s[/B] at [B]%s %s[/B]' % (away_team['city'], away_team['name'], home_team['city'], home_team['name'])

            for key, value in {'Condensed': 'condensedId', 'Full': 'programId'}.items():
                if value in game:
                    game_versions.append(key)

            if 'isLive' in game:
                game_versions.append('Live')

            if 'gameEndTimeGMT' in game:
                # Show game duration only if user wants to see it
                if addon.getSetting('hide_game_length') == 'false':
                    try:
                        start_time = datetime(*(time.strptime(game['gameTimeGMT'], date_time_format)[0:6]))
                        end_time = datetime(*(time.strptime(game['gameEndTimeGMT'], date_time_format)[0:6]))
                        game_info = 'Final [CR] Duration: %s' % time.strftime('%H:%M:%S', time.gmtime((end_time - start_time).seconds))
                    except:
                        addon_log(format_exc())
                        if 'result' in game:
                            game_info = 'Final'
                else:
                    game_info = 'Final'
            else:
                if 'isLive' in game:
                    game_info = '» Live «'

                try:
                    if addon.getSetting('local_tz') == '0':  # don't localize
                        game_datetime = datetime(*(time.strptime(game['date'], date_time_format)[0:6]))
                        game_info = game_datetime.strftime('%A, %b %d - %I:%M %p')
                    else:
                        game_gmt = time.strptime(game['gameTimeGMT'], date_time_format)
                        secs = calendar.timegm(game_gmt)
                        game_local = time.localtime(secs)

                        if addon.getSetting('local_tz') == '1':  # localize and use 12-hour clock
                            game_info = time.strftime('%A, %b %d - %I:%M %p', game_local)
                        else:  # localize and use 24-hour clock
                            game_info = time.strftime('%A, %b %d - %H:%M', game_local)
                except:  # all else fails, just use their raw date value
                    game_datetime = game['date'].split('T')
                    game_info = game_datetime[0] + '[CR]' + game_datetime[1].split('.')[0] + ' ET'

                if 'hasProgram' not in game:  # if subscription doesn't allow
                    isPlayable = 'false'
                    game_name_full = self.coloring(game_name_full, "disabled")
                    game_name_shrt = self.coloring(game_name_shrt, "disabled")
                    game_info = self.coloring(game_info, "disabled-info")

                try:
                    if game['blocked'] == 'true':
                        isPlayable = 'false'
                        isBlackedOut = 'true'
                        game_info = '» Blacked Out «'
                        game_name_full = self.coloring(game_name_full, "disabled")
                        game_name_shrt = self.coloring(game_name_shrt, "disabled")
                        game_info = self.coloring(game_info, "disabled-info")
                except KeyError:
                    pass

            listitem = xbmcgui.ListItem(game_name_shrt, game_name_full)
            listitem.setProperty('away_thumb', 'http://i.nflcdn.com/static/site/7.4/img/logos/teams-matte-144x96/%s.png' % away_team['id'])
            listitem.setProperty('home_thumb', 'http://i.nflcdn.com/static/site/7.4/img/logos/teams-matte-144x96/%s.png' % home_team['id'])
            listitem.setProperty('game_info', game_info)
            listitem.setProperty('is_game', 'true')
            listitem.setProperty('is_show', 'false')
            listitem.setProperty('isPlayable', isPlayable)
            listitem.setProperty('isBlackedOut', isBlackedOut)
            listitem.setProperty('game_id', game_id)
            listitem.setProperty('game_date', game['date'].split('T')[0])
            listitem.setProperty('game_versions', ' '.join(game_versions))
            self.games_items.append(listitem)

        self.games_list.addItems(self.games_items)

    def display_seasons_weeks(self):
        """List weeks for a given season"""
        weeks = self.seasons_and_weeks[self.selected_season]

        for week_code, week in sorted(weeks.iteritems()):
            future = 'false'
            try:
                # convert EST to GMT by adding 6 hours
                week_date = week['@start'] + ' 06:00'
                # avoid super annoying bug http://forum.kodi.tv/showthread.php?tid=112916
                week_datetime = datetime(*(time.strptime(week_date, '%Y%m%d %H:%M')[0:6]))
                now_datetime = datetime.utcnow()

                if week_datetime > now_datetime:
                    future = 'true'
            except KeyError:  # some old seasons don't provide week dates
                pass

            listitem = xbmcgui.ListItem(week['@label'].title())
            listitem.setProperty('week_code', week_code)
            listitem.setProperty('future', future)
            self.weeks_items.append(listitem)
        self.weeks_list.addItems(self.weeks_items)

    def display_shows_episodes(self, show_name, season):
        """Show episodes for a given season/show"""
        self.games_items = []
        items = gpr.get_shows_episodes(show_name, season)

        for i in items:
            try:
                listitem = xbmcgui.ListItem('[B]%s[/B]' % show_name)
                listitem.setProperty('game_info', i['name'])
                listitem.setProperty('away_thumb', gpr.image_url + i['image'])
                listitem.setProperty('url', i['publishPoint'])
                listitem.setProperty('id', i['id'])
                listitem.setProperty('type', i['type'])
                listitem.setProperty('is_game', 'false')
                listitem.setProperty('is_show', 'true')
                listitem.setProperty('isPlayable', 'true')
                self.games_items.append(listitem)
            except:
                addon_log('Exception adding archive directory: %s' % format_exc())
                addon_log('Directory name: %s' % i['name'])
        self.games_list.addItems(self.games_items)

    def play_url(self, url):
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.list_refill = True
        xbmc.Player().play(url)

    def init(self, level):
        if level == 'season':
            self.weeks_items = []
            self.weeks_list.reset()
            self.games_list.reset()
            self.clicked_week = -1
            self.clicked_game = -1

            if self.clicked_season > -1:  # unset previously selected season
                self.season_list.getListItem(self.clicked_season).setProperty('clicked', 'false')

            self.season_list.getSelectedItem().setProperty('clicked', 'true')
            self.clicked_season = self.season_list.getSelectedPosition()
        elif level == 'week/show':
            self.games_list.reset()
            self.clicked_game = -1

            if self.clicked_week > -1:  # unset previously selected week/show
                self.weeks_list.getListItem(self.clicked_week).setProperty('clicked', 'false')

            self.weeks_list.getSelectedItem().setProperty('clicked', 'true')
            self.clicked_week = self.weeks_list.getSelectedPosition()
        elif level == 'game/episode':
            if self.clicked_game > -1:  # unset previously selected game/episode
                self.games_list.getListItem(self.clicked_game).setProperty('clicked', 'false')

            self.games_list.getSelectedItem().setProperty('clicked', 'true')
            self.clicked_game = self.games_list.getSelectedPosition()

    def ask_bitrate(self, bitrates):
        """Presents a dialog for user to select from a list of bitrates.
        Returns the value of the selected bitrate.
        """
        options = []
        for bitrate in bitrates:
            options.append(bitrate + ' Kbps')
        dialog = xbmcgui.Dialog()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        ret = dialog.select(language(30003), options)
        if ret > -1:
            return bitrates[ret]
        else:
            return None

    def select_bitrate(self, manifest_bitrates=None):
        """Returns a bitrate, while honoring the user's /preference/."""
        bitrate_setting = int(addon.getSetting('preferred_bitrate'))
        bitrate_values = ['4500', '3000', '2400', '1600', '1200', '800', '400']

        highest = False
        preferred_bitrate = None
        if bitrate_setting == 0:  # 0 === "highest"
            highest = True
        elif 0 < bitrate_setting and bitrate_setting < 8:  # a specific bitrate. '8' === "ask"
            preferred_bitrate = bitrate_values[bitrate_setting - 1]

        if manifest_bitrates:
            manifest_bitrates.sort(key=int, reverse=True)
            if highest:
                return manifest_bitrates[0]
            elif preferred_bitrate and preferred_bitrate in manifest_bitrates:
                return preferred_bitrate
            else:  # ask user
                return self.ask_bitrate(manifest_bitrates)
        else:
            if highest:
                return bitrate_values[0]
            elif preferred_bitrate:
                return preferred_bitrate
            else:  # ask user
                return self.ask_bitrate(bitrate_values)

    def select_version(self, game_versions):
        """Returns a game version, while honoring the user's /preference/.
        Note: the full version is always available but not always the condensed.
        """
        preferred_version = int(addon.getSetting('preferred_game_version'))

        # user wants to be asked to select version
        if preferred_version == 2:
            versions = [language(30014)]
            if 'Condensed' in game_versions:
                versions.append(language(30015))
            if 'Coach' in game_versions:
                versions.append(language(30032))
            dialog = xbmcgui.Dialog()
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            preferred_version = dialog.select(language(30016), versions)

        if preferred_version == 1 and 'Condensed' in game_versions:
            game_version = 'condensed'
        elif preferred_version == 2 and 'Coach' in game_versions:
            game_version = 'coach'
        else:
            game_version = 'archive'

        if preferred_version > -1:
            return game_version
        else:
            return None

    def onFocus(self, controlId):  # pylint: disable=invalid-name
        # save currently focused list
        if controlId in [210, 220, 230, 240]:
            self.focusId = controlId

    def onClick(self, controlId):  # pylint: disable=invalid-name
        try:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            if controlId in [110, 120, 130]:
                self.games_list.reset()
                self.weeks_list.reset()
                self.season_list.reset()
                self.live_list.reset()
                self.games_items = []
                self.weeks_items = []
                self.live_items = []
                self.clicked_game = -1
                self.clicked_week = -1
                self.clicked_season = -1

                if controlId in [110, 120]:
                    self.main_selection = 'GamePass'
                    self.window.setProperty('NW_clicked', 'false')
                    self.window.setProperty('GP_clicked', 'true')

                    # display games of current week for usability purposes
                    cur_s_w = gpr.get_current_season_and_week()
                    self.selected_season = cur_s_w.keys()[0]
                    self.selected_week = cur_s_w.values()[0]
                    self.display_seasons()

                    try:
                        self.display_seasons_weeks()
                        self.display_weeks_games()
                    except:
                        addon_log('Error while reading seasons weeks and games')
                elif controlId == 130:
                    self.main_selection = 'NFL Network'
                    self.window.setProperty('NW_clicked', 'true')
                    self.window.setProperty('GP_clicked', 'false')
                    if gpr.subscription == 'international':
                        listitem = xbmcgui.ListItem('NFL Network - Live', 'NFL Network - Live')
                        self.live_items.append(listitem)
                        if gpr.redzone_on_air():
                            listitem = xbmcgui.ListItem('NFL RedZone - Live', 'NFL RedZone - Live')
                            self.live_items.append(listitem)

                    self.live_list.addItems(self.live_items)
                    self.display_nfln_seasons()

                xbmc.executebuiltin("Dialog.Close(busydialog)")
                return

            if self.main_selection == 'GamePass':
                if controlId == 210:  # season is clicked
                    self.init('season')
                    self.selected_season = self.season_list.getSelectedItem().getLabel()

                    self.display_seasons_weeks()
                elif controlId == 220:  # week is clicked
                    self.init('week/show')
                    self.selected_week = self.weeks_list.getSelectedItem().getProperty('week_code')

                    self.display_weeks_games()
                elif controlId == 230:  # game is clicked
                    selectedGame = self.games_list.getSelectedItem()
                    if selectedGame.getProperty('isPlayable') == 'true':
                        self.init('game/episode')
                        game_id = selectedGame.getProperty('game_id')
                        game_versions = selectedGame.getProperty('game_versions')

                        if 'Live' in game_versions:
                            if 'Final' in selectedGame.getProperty('game_info'):
                                game_version = self.select_version(game_versions)
                                if game_version == 'archive':
                                    game_version = 'dvr'
                            else:
                                game_version = 'live'
                        else:
                            # Check for coaches film availability
                            if gpr.check_for_coachestape(game_id, self.selected_season):
                                game_versions = game_versions + ' Coach'

                            game_version = self.select_version(game_versions)
                        if game_version:
                            if game_version == 'coach':
                                xbmc.executebuiltin("ActivateWindow(busydialog)")
                                coachesItems = []
                                game_date = selectedGame.getProperty('game_date').replace('-', '/')
                                self.playBackStop = False

                                play_stream = gpr.get_coaches_url(game_id, game_date, 'dummy')
                                plays = gpr.get_coaches_playIDs(game_id, self.selected_season)
                                for playID in sorted(plays, key=int):
                                    cf_url = str(play_stream).replace('dummy', playID)
                                    item = xbmcgui.ListItem(plays[playID])
                                    item.setProperty('url', cf_url)
                                    coachesItems.append(item)

                                self.list_refill = True
                                xbmc.executebuiltin("Dialog.Close(busydialog)")
                                coachGui = CoachesFilmGUI('script-gamepass-coach.xml', ADDON_PATH, plays=coachesItems)
                                coachGui.doModal()
                                del coachGui
                            else:
                                game_streams = gpr.get_publishpoint_streams(game_id, 'game', game_version)
                                bitrate = self.select_bitrate(game_streams.keys())
                                if bitrate:
                                    game_url = game_streams[bitrate]
                                    self.play_url(game_url)

            elif self.main_selection == 'NFL Network':
                if controlId == 210:  # season is clicked
                    self.init('season')
                    self.selected_season = self.season_list.getSelectedItem().getLabel()

                    self.display_nfl_network_archive()
                elif controlId == 220:  # show is clicked
                    self.init('week/show')
                    show_name = self.weeks_list.getSelectedItem().getLabel()

                    self.display_shows_episodes(show_name, self.selected_season)
                elif controlId == 230:  # episode is clicked
                    self.init('game/episode')
                    video_id = self.games_list.getSelectedItem().getProperty('id')
                    video_streams = gpr.get_publishpoint_streams(video_id, 'video')
                    if video_streams:
                        addon_log('Video-Streams: %s' % video_streams)
                        bitrate = self.select_bitrate(video_streams.keys())
                        if bitrate:
                            video_url = video_streams[bitrate]
                            self.play_url(video_url)
                    else:
                        dialog = xbmcgui.Dialog()
                        dialog.ok(language(30043), language(30045))
                elif controlId == 240:  # Live content (though not games)
                    show_name = self.live_list.getSelectedItem().getLabel()
                    if show_name == 'NFL RedZone - Live':
                        rz_live_streams = gpr.get_publishpoint_streams('redzone')
                        if rz_live_streams:
                            bitrate = self.select_bitrate(rz_live_streams.keys())
                            if bitrate:
                                rz_live_url = rz_live_streams[bitrate]
                                self.play_url(rz_live_url)
                        else:
                            dialog = xbmcgui.Dialog()
                            dialog.ok(language(30043), language(30045))
                    elif show_name == 'NFL Network - Live':
                        nw_live_streams = gpr.get_publishpoint_streams('nfl_network')
                        if nw_live_streams:
                            bitrate = self.select_bitrate(nw_live_streams.keys())
                            if bitrate:
                                nw_live_url = nw_live_streams[bitrate]
                                self.play_url(nw_live_url)
                        else:
                            dialog = xbmcgui.Dialog()
                            dialog.ok(language(30043), language(30045))
            xbmc.executebuiltin("Dialog.Close(busydialog)")
        except Exception:  # catch anything that might fail
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            addon_log(format_exc())

            dialog = xbmcgui.Dialog()
            if self.main_selection == 'NFL Network' and controlId == 230:  # episode
                # inform that not all shows will work
                dialog.ok(language(30043), language(30044))
            else:
                # generic oops
                dialog.ok(language(30021), language(30024))


class CoachesFilmGUI(xbmcgui.WindowXML):
    def __init__(self, xmlFilename, scriptPath, plays, defaultSkin="Default", defaultRes="720p"):  # pylint: disable=invalid-name
        self.playsList = None
        self.playsItems = plays

        xbmcgui.WindowXML.__init__(self, xmlFilename, scriptPath, defaultSkin, defaultRes)
        self.action_previous_menu = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)

    def onInit(self):  # pylint: disable=invalid-name
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        if addon.getSetting('coach_lite') == 'true':
            self.window.setProperty('coach_lite', 'true')

        self.playsList = self.window.getControl(110)
        self.window.getControl(99).setLabel(language(30032))
        self.playsList.addItems(self.playsItems)
        self.setFocus(self.playsList)
        url = self.playsList.getListItem(0).getProperty('url')
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        xbmc.executebuiltin('PlayMedia(%s,False,1)' % url)

    def onClick(self, controlId):  # pylint: disable=invalid-name
        if controlId == 110:
            url = self.playsList.getSelectedItem().getProperty('url')
            xbmc.executebuiltin('PlayMedia(%s,False,1)' % url)

if __name__ == "__main__":
    addon_log('script starting')
    xbmc.executebuiltin("Dialog.Close(busydialog)")

    try:
        gpr.login(username, password)
    except gpr.LoginFailure as error:
        dialog = xbmcgui.Dialog()
        if error.value == 'Game Pass Domestic Blackout':
            addon_log('Game Pass Domestic is in blackout.')
            dialog.ok(language(30021),
                      language(30022))
        else:
            addon_log('login failed')
            dialog.ok(language(30021),
                      language(30023))
        sys.exit(0)
    except:
        addon_log(format_exc())
        dialog = xbmcgui.Dialog()
        dialog.ok('Epic Failure',
                  language(30024))
        sys.exit(0)

    gui = GamepassGUI('script-gamepass.xml', ADDON_PATH)
    gui.doModal()
    del gui

addon_log('script finished')

from xbmcgui import Dialog, INPUT_NUMERIC
from xbmcaddon import Addon as KodiAddon
from tmdbhelper.lib.addon.plugin import ADDONPATH, get_localized
from jurialmunkey.parser import try_int
from tmdbhelper.lib.addon.dialog import BusyDialog
from tmdbhelper.lib.addon.consts import PLAYERS_BASEDIR_SAVE, PLAYERS_PRIORITY
from tmdbhelper.lib.files.futils import dumps_to_file, delete_file
from tmdbhelper.lib.items.listitem import ListItem
from tmdbhelper.lib.player.create import CreatePlayer
from tmdbhelper.lib.player.putils import get_players_from_file
from tmdbhelper.lib.player.editsteps import _EditPlayer
from json import dumps
from copy import deepcopy


def configure_players(*args, **kwargs):
    ConfigurePlayers().run()


class _ConfigurePlayer():
    def __init__(self, player, filename):
        self.player = player
        self.filename = filename
        self._dialogsettings = [
            {
                'name': lambda: f'name: {self.player.get("name")}',
                'func': lambda: self.set_name(),
            },
            {
                'name': lambda: f'disabled: {self.player.get("disabled", "false").lower()}',
                'func': lambda: self.set_disabled(),
            },
            {
                'name': lambda: f'priority: {self.player.get("priority") or PLAYERS_PRIORITY}',
                'func': lambda: self.set_priority(),
            },
            {
                'name': lambda: f'is_resolvable: {self.player.get("is_resolvable", "select")}',
                'func': lambda: self.set_resolvable(),
            },
            {
                'name': lambda: f'make_playlist: {self.player.get("make_playlist", "false").lower()}',
                'func': lambda: self.set_makeplaylist(),
            },
            {
                'name': lambda: f'fallback: {dumps(self.player.get("fallback"))}',
                'func': lambda: self.set_fallbacks(),
            },
            {
                'name': lambda: get_localized(32440),
                'func': lambda: _EditPlayer(self.player, self.filename).run()
            },
            {
                'name': lambda: get_localized(32330),
                'func': lambda: -1,
                'returns': True
            },
            {
                'name': lambda: get_localized(190),
                'func': lambda: self.player,
                'returns': True
            }
        ]

    def get_player_settings(self):
        if not self.player:
            return
        return [i['name']() for i in self._dialogsettings]

    def set_name(self):
        name = self.player.get('name', '')
        name = Dialog().input(get_localized(32331).format(self.filename), defaultt=name)
        if not name:
            return
        self.player['name'] = name

    def set_disabled(self):
        disabled = 'false'
        if self.player.get('disabled', 'false').lower() == 'false':
            disabled = 'true'
        self.player['disabled'] = disabled

    def set_priority(self):
        priority = f'{self.player.get("priority") or PLAYERS_PRIORITY}'  # Input numeric takes str for some reason?!
        priority = Dialog().input(
            get_localized(32344).format(self.filename),
            defaultt=priority, type=INPUT_NUMERIC)
        priority = try_int(priority)
        if not priority:
            return
        self.player['priority'] = priority

    def set_resolvable(self):
        x = Dialog().select(get_localized(32332), [
            'setResolvedURL (true)', 'PlayMedia (false)', f'{get_localized(32333)} (select)'])
        if x == -1:
            return
        is_resolvable = 'select'
        if x == 0:
            is_resolvable = 'true'
        elif x == 1:
            if not Dialog().yesno(
                    get_localized(32339).format(self.filename),
                    get_localized(32340)):
                return self.set_resolvable()
            is_resolvable = 'false'
        self.player['is_resolvable'] = is_resolvable

    def set_makeplaylist(self):
        x = Dialog().yesnocustom(get_localized(32424), get_localized(32425), customlabel=get_localized(32447))
        if x == -1:
            return
        self.player['make_playlist'] = ['false', 'true', 'upnext'][x]

    @staticmethod
    def _get_method_type(method):
        for i in ['movie', 'episode']:
            if i in method:
                return i

    @staticmethod
    def _get_player_methods(player):
        methods = ['play_movie', 'play_episode', 'search_movie', 'search_episode']
        return [i for i in methods if i in player and player[i]]

    def get_fallback_method(self, player, filename, og_method):
        """ Get the available methods for the player and ask user to select one """
        mt = self._get_method_type(og_method)
        methods = [
            f'{filename} {i}' for i in self._get_player_methods(player) if mt in i
            and (filename != self.filename or i != og_method)]  # Avoid adding same fallback method as original
        if not methods:
            return
        x = Dialog().select(get_localized(32341), methods)
        if x == -1:
            return
        return methods[x]

    def get_fallback_player(self, og_method=None):
        # Get players from files and ask user to select one
        players = ConfigurePlayers()
        filename = players.select_player(get_localized(32343).format(self.filename, og_method))
        player = players.players.get(filename)
        if player and filename:
            return self.get_fallback_method(player, filename, og_method)

    def set_fallbacks(self):
        # Get the methods that the player supports and ask user to select which they want to set
        methods = self._get_player_methods(self.player)
        x = Dialog().select(get_localized(32342).format(self.filename), [
            f'{i}: {self.player.get("fallback", {}).get(i, "null")}' for i in methods])
        if x == -1:
            return
        fallback = self.get_fallback_player(methods[x])
        if fallback:
            self.player.setdefault('fallback', {})[methods[x]] = fallback
        return self.set_fallbacks()

    def run(self):
        """
        Returns player or -1 if reset to default (i.e. delete configured player)
        """
        x = Dialog().select(self.filename, self.get_player_settings())
        if x == -1:
            return self.player
        try:
            value = self._dialogsettings[x]['func']()
            if self._dialogsettings[x].get('returns'):
                return value
        except IndexError:
            pass
        return self.run()


class ConfigurePlayers():
    def __init__(self):
        with BusyDialog():
            self.get_players()

    @staticmethod
    def _get_dialog_players(players):
        return [
            ListItem(
                label=f"{'[DISABLED] ' if v.get('disabled', 'false').lower() == 'true' else ''}{v.get('name')}",
                label2=k,
                art={
                    'thumb': v.get('icon', '').format(ADDONPATH)
                    or KodiAddon(v.get('plugin', '')).getAddonInfo('icon')}).get_listitem()
            for k, v in sorted(
                players.items(),
                key=lambda i: try_int(i[1].get('priority')) or PLAYERS_PRIORITY)]

    def get_players(self):
        self.players = {'create_player': {'name': 'Create new player', 'icon': '-', 'priority': 1}}
        self.players.update(get_players_from_file())
        self.dialog_players = self._get_dialog_players(self.players)

    def select_player(self, header=get_localized(32328)):
        x = Dialog().select(header, self.dialog_players, useDetails=True)
        if x == -1:
            return
        return self.dialog_players[x].getLabel2()  # Filename is saved in label2

    def delete_player(self, filename):
        if not Dialog().yesno(
                get_localized(32334),
                get_localized(32335).format(filename),
                yeslabel=get_localized(13007), nolabel=get_localized(222)):
            return
        with BusyDialog():
            delete_file(PLAYERS_BASEDIR_SAVE, filename, join_addon_data=False)
            self.get_players()

    def save_player(self, player, filename, confirm=True):
        if confirm and not Dialog().yesno(
                get_localized(32336), get_localized(32337).format(filename),
                yeslabel=get_localized(190), nolabel=get_localized(32338)):
            return
        with BusyDialog():
            self.players[filename] = player  # Update our players dictionary
            self.dialog_players = self._get_dialog_players(self.players)  # Update our dialog list
            dumps_to_file(player, PLAYERS_BASEDIR_SAVE, filename, indent=4, join_addon_data=False)  # Write out file
        return filename

    def run(self):
        filename = self.select_player()
        if not filename:
            return

        def _configure_selected_player():
            try:
                player = deepcopy(self.players[filename])
            except KeyError:
                return

            player = _ConfigurePlayer(player, filename=filename).run()

            if player == -1:  # Reset player (i.e. delete player file)
                self.delete_player(filename)
            elif player and player != self.players[filename]:
                self.save_player(player, filename)

        if filename == 'create_player':
            filename = CreatePlayer().create_player()
            self.get_players()

        _configure_selected_player()
        return self.run()

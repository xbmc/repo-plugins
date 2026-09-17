"""
Module for Arte History also known as last viewed
"""

import xbmcgui
from resources.lib import api
from resources.lib import user
from resources.lib.mapper.artecollection import ArteCollection


class ArteHistory(ArteCollection):
    """
    Arte history allows to keep track of what user watched fully or partially.
    It is populated thanks to synchronization with arteplussept Player.
    It is available with Arte TV APA "last viewed" only.
    """

    def build_item(self, label):
        """
        Return menu item to access logged-in user's Arte history
        """
        return super()._build_item('last_viewed', label, 30030)

    def build_menu(self, page):
        """
        Return current page of user's history
        """
        menu = None
        auth_token = user.get_cached_token(self.plugin, self.settings.username)
        if auth_token:
            menu = super()._build_menu(
                api.get_last_viewed(self.settings.language, auth_token, page),
                'last_viewed'
            )
        return menu

    def purge(self):
        """Flush user history and notify about success or failure"""
        auth_token = user.get_cached_token(self.plugin, self.settings.username)
        if auth_token:
            purge_confirmed = xbmcgui.Dialog().yesno(
                self.plugin.addon.getLocalizedString(30030),
                self.plugin.addon.getLocalizedString(30033),
                autoclose=10000)
            if purge_confirmed:
                if 200 == api.purge_last_viewed(auth_token):
                    self.plugin.notify(
                        msg=self.plugin.addon.getLocalizedString(30031), image='info')
                else:
                    self.plugin.notify(
                        msg=self.plugin.addon.getLocalizedString(30032), image='error')

    def mark_as_watched(self, program_id, label):
        """
        Get program duration and synch progress with total duration
        in order to mark a program as watched
        """
        status = -1
        lang = self.settings.language
        usr = self.settings.username
        program_info = api.player_video(lang, program_id)
        total_time = program_info.get('attributes').get('metadata').get('duration').get('seconds')
        auth_token = user.get_cached_token(self.plugin, usr)
        if auth_token:
            status = api.sync_last_viewed(auth_token, program_id, total_time)
            if 200 == status:
                msg = self.plugin.addon.getLocalizedString(30036).format(label=label)
                self.plugin.notify(msg=msg, image='info')
            else:
                msg = self.plugin.addon.getLocalizedString(30037).format(label=label)
                self.plugin.notify(msg=msg, image='error')

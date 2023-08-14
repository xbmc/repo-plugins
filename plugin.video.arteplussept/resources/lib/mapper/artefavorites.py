"""
Module for Arte Favorites
"""

# pylint: disable=import-error
from xbmcswift2 import xbmcgui
from resources.lib import api
from resources.lib import user
from resources.lib.mapper.artecollection import ArteCollection


class ArteFavorites(ArteCollection):
    """Arte favorites is a kind of user bookmark of arte content managed with Arte TV API."""

    def __init__(self, plugin, settings):
        super().__init__(plugin, settings)
        self.auth_token = user.get_cached_token(self.plugin, settings.username)

    def build_item(self, label):
        """
        Return menu item to access logged-in user's Arte favorites
        """
        return super()._build_item('favorites', label, 30040)

    def build_menu(self, page):
        """Build the menu for user favorites thanks to API call"""
        return super()._build_menu(
            api.get_favorites(self.settings.language, self.auth_token, page),
            'favorites')

    def add_favorite(self, program_id, label):
        """Add content program_id to user favorites.
        Notify about completion success or failure with label."""
        if 200 == api.add_favorite(self.auth_token, program_id):
            msg = self.plugin.addon.getLocalizedString(30025).format(label=label)
            self.plugin.notify(msg=msg, image='info')
        else:
            msg = self.plugin.addon.getLocalizedString(30026).format(label=label)
            self.plugin.notify(msg=msg, image='error')

    def remove_favorite(self, program_id, label):
        """Remove content program_id from user favorites.
        Notify about completion success or failure with label."""
        if 200 == api.remove_favorite(self.auth_token, program_id):
            msg = self.plugin.addon.getLocalizedString(30027).format(label=label)
            self.plugin.notify(msg=msg, image='info')
        else:
            msg = self.plugin.addon.getLocalizedString(30028).format(label=label)
            self.plugin.notify(msg=msg, image='error')

    def purge(self):
        """Flush user favorites and notify about success or failure"""
        purge_confirmed = xbmcgui.Dialog().yesno(
            self.plugin.addon.getLocalizedString(30040),
            self.plugin.addon.getLocalizedString(30043),
            autoclose=10000)

        if purge_confirmed:
            if 200 == api.purge_favorites(self.auth_token):
                self.plugin.notify(msg=self.plugin.addon.getLocalizedString(30041), image='info')
            else:
                self.plugin.notify(msg=self.plugin.addon.getLocalizedString(30042), image='error')

__author__ = 'bromix'

from ..abstract_settings import AbstractSettings


class KodiSettings(AbstractSettings):
    def __init__(self, context, xbmc_addon):
        AbstractSettings.__init__(self)
        
        self._xbmc_addon = xbmc_addon

        if self.get_int('converted', 0) < 2:
            self._convert(context)
            pass
        pass

    def _convert(self, context):
        convert_map = {'kodion.fanart.show': self.ADDON_SHOW_FANART,
                       'kodion.content.max_per_page': self.ADDON_ITEMS_PER_PAGE,
                       'kodion.search.size': self.ADDON_SEARCH_SIZE,
                       'kodion.cache.size': self.ADDON_CACHE_SIZE,
                       'kodion.video.quality': self.VIDEO_QUALITY,
                       'kodion.video.quality.ask': self.VIDEO_QUALITY_ASK,
                       'kodion.setup_wizard': self.ADDON_SETUP,
                       'kodion.support.alternative_player': '',
                       'kodion.view.override': self.VIEW_OVERRIDE,
                       'kodion.view.default': self.VIEW_X % 'default',
                       'kodion.view.movies': self.VIEW_X % 'movies',
                       'kodion.view.tvshows': self.VIEW_X % 'tvshows',
                       'kodion.view.episodes': self.VIEW_X % 'episodes',
                       'kodion.view.musicvideos': self.VIEW_X % 'musicvideos',
                       'kodion.view.songs': self.VIEW_X % 'songs',
                       'kodion.view.albums': self.VIEW_X % 'albums',
                       'kodion.view.artists': self.VIEW_X % 'artists',
                       'kodion.login.username': self.LOGIN_USERNAME,
                       'kodion.login.password': self.LOGIN_PASSWORD,
                       'kodion.login.hash': self.LOGIN_HASH,
                       'kodion.access_token': self.LOGIN_ACCESS_TOKEN,
                       'kodion.refresh_token': self.LOGIN_REFRESH_TOKEN,
                       'kodion.access_token.expires': self.LOGIN_ACCESS_TOKEN_EXPIRES}

        for old_key, new_key in convert_map.iteritems():
            setting = self.get_string(old_key, None)
            if setting:
                context.log_info('Converting setting "%s" to "%s' % (old_key, new_key))
                self.set_string(new_key, setting)
                pass
            pass

        self.set_int('converted', 2)
        pass

    def get_string(self, setting_id, default_value=None):
        return self._xbmc_addon.getSetting(setting_id)
    
    def set_string(self, setting_id, value):
        self._xbmc_addon.setSetting(setting_id, value)
        pass
    
    pass
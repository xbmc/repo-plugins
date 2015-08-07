__author__ = 'bromix'


class ViewManager(object):
    def __init__(self, context, provider):
        self._context = context
        self._provider = provider
        pass

    def setup(self):
        skin_id = self._context.get_ui().get_skin_id()
        self._context.log_info('Running View Manager for skin "%s"' % skin_id)
        if not skin_id in self.SKIN_DATA:
            self._context.log_info('Skin "%s" not support' % skin_id)
            return

        if not self._context.get_ui().on_yes_no_input(self._context.get_name(),
                                                      self._context.localize(self._provider.LOCAL_SETUP_OVERRIDE_VIEW)):
            return

        content_types = self._provider.on_setup(self._context, mode='content-type')
        if content_types is None or not content_types:
            content_types = ['default']
            pass

        skin_data = self.SKIN_DATA.get(skin_id, {})
        content_type_map = {'default': 30027,
                            'episodes': 30028,
                            'movies': 30029,
                            'tvshows': 30032,
                            'songs': 30033,
                            'artists': 30034,
                            'albums': 30035}

        settings = self._context.get_settings()
        for content_type in content_types:
            if content_type in self.SUPPORTED_CONTENT_TYPES:
                views = skin_data.get(content_type, [])
                for index, view in enumerate(views):
                    views[index] = (view['name'], view['id'])
                    pass
                title = self._context.localize(content_type_map[content_type])
                view_id = self._context.get_ui().on_select(title, views)

                # user input (fallback)
                if view_id == -1:
                    old_value = settings.get_string(settings.VIEW_X % view, '')
                    if old_value:
                        result, view_id = self._context.get_ui().on_numeric_input(title, old_value)
                        if not result:
                            view_id = -1
                            pass
                        pass
                    pass

                # set the new value
                if view_id > -1:
                    settings.set_int(settings.VIEW_X % content_type, view_id)
                    pass
                pass
            else:
                self._context.log_error('Unsupported or unknown content type "%s"' % content_type)
                pass

        settings.set_bool(settings.VIEW_OVERRIDE, True)
        pass

    SUPPORTED_CONTENT_TYPES = ['default', 'movies', 'tvshows', 'episodes', 'musicvideos', 'songs', 'albums', 'artists']
    SKIN_DATA = {
        'skin.confluence': {
            'default': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500}
            ],
            'movies': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 504},
                {'name': 'Media info 2', 'id': 503}
            ],
            'episodes': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 504},
                {'name': 'Media info 2', 'id': 503}
            ],
            'tvshows': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Poster', 'id': 500},
                {'name': 'Wide', 'id': 505},
                {'name': 'Media info', 'id': 504},
                {'name': 'Media info 2', 'id': 503},
                {'name': 'Fanart', 'id': 508}
            ],
            'musicvideos': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 504},
                {'name': 'Media info 2', 'id': 503}
            ],
            'songs': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 506}
            ],
            'albums': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 506}
            ],
            'artists': [
                {'name': 'List', 'id': 50},
                {'name': 'Big List', 'id': 51},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Media info', 'id': 506}
            ]
        },
        'skin.aeon.nox.5': {
            'default': [
                {'name': 'List', 'id': 50},
                {'name': 'Episodes', 'id': 502},
                {'name': 'LowList', 'id': 501},
                {'name': 'BannerWall', 'id': 58},
                {'name': 'Shift', 'id': 57},
                {'name': 'Posters', 'id': 56},
                {'name': 'ShowCase', 'id': 53},
                {'name': 'Landscape', 'id': 52},
                {'name': 'InfoWall', 'id': 51}
            ]
        },
        'skin.1080xf': {
            'default': [
                {'name': 'List', 'id': 50},
                {'name': 'Thumbnail', 'id': 500},
            ],
            'episodes': [
                {'name': 'List', 'id': 50},
                {'name': 'Info list', 'id': 52},
                {'name': 'Fanart', 'id': 502},
                {'name': 'Landscape', 'id': 54},
                {'name': 'Poster', 'id': 55},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Banner', 'id': 60}
            ],
        },
        'skin.xperience1080': {
            'default': [
                {'name': 'List', 'id': 50},
                {'name': 'Thumbnail', 'id': 500},
            ],
            'episodes': [
                {'name': 'List', 'id': 50},
                {'name': 'Info list', 'id': 52},
                {'name': 'Fanart', 'id': 502},
                {'name': 'Landscape', 'id': 54},
                {'name': 'Poster', 'id': 55},
                {'name': 'Thumbnail', 'id': 500},
                {'name': 'Banner', 'id': 60}
            ],
        }
    }

    pass

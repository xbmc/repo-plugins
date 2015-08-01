__author__ = 'bromix'

import json

from .core.nightcrawler_decorators import register_path, register_context_value, register_path_value
from .core.view_manager import ViewManager
from .exception import ProviderException


class Provider(object):
    LOCAL_SETUP_WIZARD_EXECUTE = 30030
    LOCAL_LOGIN_FAILED = 30121
    LOCAL_LOGIN_USERNAME = 30001
    LOCAL_LOGIN_PASSWORD = 30002

    LOCAL_PLEASE_WAIT = 30119

    LOCAL_FAVORITES = 30100
    LOCAL_FAVORITES_ADD = 30101
    LOCAL_FAVORITES_REMOVE = 30108

    LOCAL_WATCH_LATER = 30107
    LOCAL_WATCH_LATER_ADD = 30107
    LOCAL_WATCH_LATER_REMOVE = 30108

    LOCAL_SEARCH = 30102
    LOCAL_SEARCH_TITLE = 30102
    LOCAL_SEARCH_NEW = 30110
    LOCAL_SEARCH_RENAME = 30113
    LOCAL_SEARCH_REMOVE = 30108
    LOCAL_SEARCH_CLEAR = 30120

    LOCAL_CONFIRM_DELETE = 30114
    LOCAL_CONFIRM_REMOVE = 30115
    LOCAL_DELETE_CONTENT = 30116
    LOCAL_REMOVE_CONTENT = 30117

    LOCAL_SELECT_VIDEO_QUALITY = 30010

    LOCAL_SETUP_VIEW_DEFAULT = 30027
    LOCAL_SETUP_VIEW_VIDEOS = 30028

    LOCAL_LIBRARY = 30103
    LOCAL_HIGHLIGHTS = 30104
    LOCAL_ARCHIVE = 30105
    LOCAL_NEXT_PAGE = 30106

    LOCAL_LATEST_VIDEOS = 30109

    LOCAL_SETUP_OVERRIDE_VIEW = 30037

    PATH_SEARCH = '/search/list/'
    PATH_SEARCH_LIST = '/search/list/'
    PATH_SEARCH_QUERY = '/search/query/'
    PATH_SEARCH_CLEAR = '/search/clear/'
    PATH_SEARCH_RENAME = '/search/rename/'
    PATH_SEARCH_REMOVE = '/search/remove/'

    PATH_FAVORITES_ADD = '/favorites/add/'
    PATH_FAVORITES_LIST = '/favorites/list/'
    PATH_FAVORITES_REMOVE = '/favorites/remove/'

    PATH_WATCH_LATER_ADD = '/watch_later/add/'
    PATH_WATCH_LATER_LIST = '/watch_later/list/'
    PATH_WATCH_LATER_REMOVE = '/watch_later/remove/'

    def __init__(self):
        pass

    def _process_addon_setup(self, context):
        settings = context.get_settings()

        # exit if the setup isn't enabled
        if not settings.is_setup_wizard_enabled():
            return

        # exit if the setup shouldn't be executed
        if not context.get_ui().on_yes_no_input(context.get_name(), context.localize(self.LOCAL_SETUP_WIZARD_EXECUTE)):
            return

        view_manager = ViewManager(context, self)
        view_manager.setup()

        self.on_setup(context, mode='setup')

        # disable the setup
        settings.set_bool(settings.ADDON_SETUP, False)
        pass

    def on_setup(self, context, mode):
        if mode == 'content-types':
            return ['default']

        return None

    def select_video_stream(self, context, video_streams, video_quality_index=None, video_item=None):
        """
        Returns a selected video stream or False if the user aborted
        :param context: the current context
        :param video_streams: a list of selectable video streams
        :param video_item: (optional) video item to update with the uri of the selected video stream
        :param video_quality_index: index mapping to video quality
        :return:
        """
        if not video_quality_index:
            video_quality_index = [360, 720]
            pass

        def _sort_video_streams(_video_stream):
            return _video_stream.get('sort', 0)

        def _find_best_fit(_video_streams):
            _video_quality = context.get_settings().get_video_quality(video_quality_index=video_quality_index)
            _last_delta = None

            _selected_video_stream = None
            for _video_stream in _video_streams:
                _delta = abs(_video_stream.get('video', {}).get('height', 0) - _video_quality)
                if _selected_video_stream is None or _last_delta is None or _last_delta > _delta:
                    _last_delta = _delta
                    _selected_video_stream = _video_stream
                    pass
                pass

            return _selected_video_stream

        # sort stream, highest values first based on 'sort' array
        video_streams = sorted(video_streams, key=_sort_video_streams, reverse=True)

        # log all possible steams
        context.log_debug('selectable streams: %d' % len(video_streams))
        for video_stream in video_streams:
            context.log_debug('selectable stream: %s' % video_stream)
            pass

        # show a list of selectable streams (if enabled)
        selected_video_stream = None
        if context.get_settings().ask_for_video_quality() and len(video_streams) > 1:
            items = map(lambda x: (x['title'], x), video_streams)
            selected_video_stream = context.get_ui().on_select(context.localize(self.LOCAL_SELECT_VIDEO_QUALITY), items,
                                                               default=None)
            pass
        else:
            # fallback - use best fit
            selected_video_stream = _find_best_fit(video_streams)
            pass

        if selected_video_stream is None:
            return False

        # log selected video stream
        context.log_debug('selected stream: %s' % selected_video_stream)

        # we need an uri in the video stream
        if not 'uri' in selected_video_stream:
            raise ProviderException('Missing uri in video stream')

        # update the given video item (optional)
        if video_item:
            video_item['uri'] = selected_video_stream['uri']
            return video_item

        # return an uri item
        return {'type': 'uri',
                'uri': selected_video_stream['uri']}

    def navigate(self, context):
        self._process_addon_setup(context)

        method_names = dir(self)
        for method_name in method_names:
            method = getattr(self, method_name)
            if hasattr(method, 'nightcrawler_registered_path'):
                result = method(context)
                if result is not None:
                    return result
                pass
            pass

        raise ProviderException('Missing method for path "%s"' % context.get_path())

    def get_fanart(self, context):
        """
        Can be overriden by the derived class to return an alternate image
        :param context: the current image
        :return: full path to the fanart image
        """
        return context.get_fanart()

    def on_search(self, context, search_text):
        """
        The derived class has to implement this method in case of support for search
        :param context: the current context
        :param search_text: the search term in unicode
        :return: a list of items or False if something went wrong
        """
        raise NotImplementedError()

    @register_path('/favorites/(?P<method>add|remove)/')
    @register_path_value('method', unicode)
    @register_context_value('item', dict, required=True)
    def _internal_favorites_with_item(self, context, method, item):
        if method == 'add':
            context.get_favorite_list().add(item)
            return True

        if method == 'remove':
            context.get_favorite_list().remove(item)
            context.get_ui().refresh_container()
            return True

        return False

    @register_path('/favorites/list/')
    def on_favorites_list(self, context):
        result = context.get_favorite_list().list()
        for directory_item in result:
            context_menu = [(context.localize(self.LOCAL_WATCH_LATER_REMOVE),
                             'RunPlugin(%s)' % context.create_uri(self.PATH_FAVORITES_REMOVE,
                                                                  {'item': json.dumps(directory_item)}))]
            directory_item['context-menu'] = {'items': context_menu}
            pass

        return result

    @register_path('/watch_later/(?P<method>add|remove)/')
    @register_path_value('method', unicode)
    @register_context_value('item', dict, required=True)
    def _internal_watch_later_with_item(self, context, method, item):
        if method == 'add':
            context.get_watch_later_list().add(item)
            return True

        if method == 'remove':
            context.get_watch_later_list().remove(item)
            context.get_ui().refresh_container()
            return True

        return False

    @register_path('/watch_later/list/')
    def on_watch_later(self, context):
        video_items = context.get_watch_later_list().list()

        for video_item in video_items:
            context_menu = [(context.localize(self.LOCAL_WATCH_LATER_REMOVE),
                             'RunPlugin(%s)' % context.create_uri(self.PATH_WATCH_LATER_REMOVE,
                                                                  {'item': json.dumps(video_item)}))]
            video_item['context-menu'] = {'items': context_menu}
            pass

        return video_items

    @register_path('/search/(?P<method>(remove|rename))/')
    @register_path_value('method', unicode)
    @register_context_value('q', unicode, alias='query', required=True)
    def _internal_search_with_query(self, context, method, query):
        search_history = context.get_search_history()
        if method == 'remove':
            search_history.remove(query)
            context.get_ui().refresh_container()
            return True

        if method == 'rename':
            result, new_query = context.get_ui().on_keyboard_input(context.localize(self.LOCAL_SEARCH_RENAME), query)
            if result:
                search_history.rename(query, new_query)
                context.get_ui().refresh_container()
                pass
            return True

        return False

    @register_path('/search/(?P<method>(list|query|clear))/')
    @register_path_value('method', unicode)
    @register_context_value('q', unicode, alias='query', default=u'')
    def _internal_search_without_query(self, context, method, query):
        search_history = context.get_search_history()
        if method == 'clear':
            search_history.clear()
            context.get_ui().refresh_container()
            return True

        if method == 'list':
            # add new search
            result = [{'type': 'folder',
                       'title': '[B]%s[/B]' % context.localize(self.LOCAL_SEARCH_NEW),
                       'uri': context.create_uri(self.PATH_SEARCH_QUERY),
                       'images': {'thumbnail': context.create_resource_path('media/new_search.png'),
                                  'fanart': self.get_fanart(context)}}]

            for query in search_history.list():
                # we create a new instance of the SearchItem
                context_menu = [(context.localize(self.LOCAL_SEARCH_REMOVE),
                                 'RunPlugin(%s)' % context.create_uri(self.PATH_SEARCH_REMOVE, {'q': query})),
                                (context.localize(self.LOCAL_SEARCH_RENAME),
                                 'RunPlugin(%s)' % context.create_uri(self.PATH_SEARCH_RENAME, {'q': query})),
                                (context.localize(self.LOCAL_SEARCH_CLEAR),
                                 'RunPlugin(%s)' % context.create_uri(self.PATH_SEARCH_CLEAR))]
                item = {'type': 'folder',
                        'title': query,
                        'uri': context.create_uri(self.PATH_SEARCH_QUERY, {'q': query}),
                        'images': {'thumbnail': context.create_resource_path('media/search.png'),
                                   'fanart': self.get_fanart(context)},
                        'context-menu': {'items': context_menu}}
                result.append(item)
                pass

            return result

        if method == 'query':
            result = True
            if not query:
                result, query = context.get_ui().on_keyboard_input(context.localize(self.LOCAL_SEARCH_TITLE))
                pass

            if result and query:
                search_history.update(query)
                return self.on_search(context, query)
            pass

        return False

    def handle_exception(self, context, exception_to_handle):
        """
        Can be overridden by the derived class to handle exceptions
        :param context: the current context
        :param exception_to_handle: the caught exception
        :return: None if nothing can be done. True exception can be handled, False if not. A list of items is also possible.
        """
        return None

    def tear_down(self, context):
        """
        Can be overridden by the derived class to free resources or write some stuff to disk/cache
        :param context: the current context
        """
        pass

    pass
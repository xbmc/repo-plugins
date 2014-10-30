import hashlib
import os
import re
import time


class AbstractProvider(object):
    PATH_SEARCH = 'kodimon/search'
    PATH_FAVORITES = 'kodimon/favorites'
    PATH_WATCH_LATER = 'kodimon/watch_later'

    RESULT_CACHE_TO_DISC = 'cache_to_disc'  # (bool)

    LOCAL_FAVORITES = 'kodimon.favorites'
    LOCAL_FAVORITES_ADD = 'kodimon.favorites.add'
    LOCAL_FAVORITES_REMOVE = 'kodimon.favorites.remove'
    LOCAL_SEARCH = 'kodimon.search'
    LOCAL_SEARCH_TITLE = 'kodimon.search.title'
    LOCAL_SEARCH_NEW = 'kodimon.search.new'
    LOCAL_SEARCH_REMOVE = 'kodimon.search.remove'
    LOCAL_LIBRARY = 'kodimon.library'
    LOCAL_HIGHLIGHTS = 'kodimon.highlights'
    LOCAL_ARCHIVE = 'kodimon.archive'
    LOCAL_NEXT_PAGE = 'kodimon.next_page'
    LOCAL_WATCH_LATER = 'kodimon.watch_later'
    LOCAL_WATCH_LATER_ADD = 'kodimon.watch_later.add'
    LOCAL_WATCH_LATER_REMOVE = 'kodimon.watch_later.remove'
    LOCAL_LATEST_VIDEOS = 'kodimon.latest_videos'

    def __init__(self, plugin=None):
        """
        Default constructor for a new content provider.
        You can provide an alternative implementation of a plugin. If the given
        plugin is None we try to get a implementation the good way :)

        :param plugin:
        :return:
        """

        # if no plugin is given (should be default) we create our own implementation
        if plugin is None:
            from . import Plugin

            self._plugin = Plugin()
        else:
            self._plugin = plugin
            pass

        # initialize class for caching results of functions
        from helper import FunctionCache, SearchHistory, FavoriteList, WatchLaterList
        import constants

        # initialize cache
        cache_path = os.path.join(self.get_plugin().get_data_path(), u'kodimon')
        max_cache_size_mb = self.get_plugin().get_settings().get_int(constants.SETTING_CACHE_SIZE, 5)
        self._cache = FunctionCache(os.path.join(cache_path, u'cache'), max_file_size_kb=max_cache_size_mb * 1024)

        # initialize search history
        max_search_history_items = self.get_plugin().get_settings().get_int(constants.SETTING_SEARCH_SIZE, 50,
                                                                            lambda x: x * 10)
        self._search = SearchHistory(os.path.join(cache_path, u'search'), max_search_history_items)
        self._favorites = FavoriteList(os.path.join(cache_path, u'favorites'))
        self._watch_later = WatchLaterList(os.path.join(cache_path, u'watch_later'))

        # map for regular expression (path) to method (names)
        self._dict_path = {}

        # map for localization: (string)<ID> => (int)<ID>
        self._dict_localization = {}

        # register some default paths
        self.register_path('^/$', '_internal_root')
        self.register_path('^/' + self.PATH_WATCH_LATER + '/(?P<command>add|remove|list)/?$', '_internal_watch_later')
        self.register_path('^/' + self.PATH_FAVORITES + '/(?P<command>add|remove|list)/?$', '_internal_favorite')
        self.register_path('^/' + self.PATH_SEARCH + '/(?P<command>new|query|list|remove)/?$', '_internal_search')

        """
        Test each method of this class for the appended attribute '_re_match' by the
        decorator (RegisterPath).
        The '_re_match' attributes describes the path which must match for the decorated method.
        """

        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, 'kodimon_re_path'):
                self.register_path(method.kodimon_re_path, method_name)
                pass
            pass

        self.set_localization({self.LOCAL_FAVORITES: 30100,
                               self.LOCAL_FAVORITES_ADD: 30101,
                               self.LOCAL_FAVORITES_REMOVE: 30108,
                               self.LOCAL_SEARCH: 30102,
                               self.LOCAL_SEARCH_TITLE: 30102,
                               self.LOCAL_SEARCH_NEW: 30110,
                               self.LOCAL_SEARCH_REMOVE: 30108,
                               self.LOCAL_LIBRARY: 30103,
                               self.LOCAL_HIGHLIGHTS: 30104,
                               self.LOCAL_ARCHIVE: 30105,
                               self.LOCAL_NEXT_PAGE: 30106,
                               self.LOCAL_WATCH_LATER: 30107,
                               self.LOCAL_WATCH_LATER_ADD: 30107,
                               self.LOCAL_WATCH_LATER_REMOVE: 30108,
                               self.LOCAL_LATEST_VIDEOS: 30109})
        pass

    def shut_down(self):
        self._search = None
        self._cache = None
        self._watch_later = None
        pass

    def get_search_history(self):
        return self._search

    def get_favorite_list(self):
        return self._favorites

    def get_watch_later_list(self):
        return self._watch_later

    def get_function_cache(self):
        return self._cache

    def set_localization(self, *args):
        """
        set_localization('some.id', 50000)
        set_localization({'some.id: 50000, 'some.id2': 50001})
        :param args:
        :return:
        """
        if len(args) == 1 and isinstance(args[0], dict):
            self._dict_localization.update(args[0])
            pass
        elif len(args) == 2:
            if isinstance(args[0], basestring) and isinstance(args[1], int):
                self._dict_localization[unicode(args[0])] = args[1]
            pass
        pass

    def get_settings(self):
        return self._plugin.get_settings()

    def localize(self, text_id, default_text=None):
        """
        Returns the localized version of the given id. If no localization exists
        the default text will be returned.
        :param text_id:
        :param default_text:
        :return:
        """
        mapped_id = self._dict_localization.get(text_id, None)

        # no mapping was found
        if mapped_id is None:
            if default_text:
                return default_text
            return unicode(text_id)

        return self.get_plugin().localize(mapped_id, default_text)

    def create_next_page_item(self, current_page_index, path, params=None):
        """
        Creates a default next page item based on the current path.
        :param current_page_index: current page index (int)
        :param path: current path
        :param params:
        :return:
        """
        if not params:
            params = {}
            pass

        new_params = {}
        new_params.update(params)
        new_params['page'] = unicode(current_page_index + 1)
        name = self.localize(self.LOCAL_NEXT_PAGE, 'Next Page')
        if name.find('%d') != -1:
            name %= current_page_index + 1
            pass

        from . import DirectoryItem

        return DirectoryItem(name, self.create_uri(path, new_params))

    def get_fanart(self):
        """
        Returns the fanart of the plugin
        :return:
        """
        return self.get_plugin().get_fanart()

    def get_plugin(self):
        """
        Returns the current implementation of a plugin.
        :return:
        """
        return self._plugin

    def call_function_cached(self, partial_func, seconds, return_cached_only=False):
        """
        Use this method to cache the result of a (partial) given method.
        :param partial_func:
        :param seconds: Time to live.
        :param return_cached_only: if True returns only a cached result without calling the given method.
        :return:
        """
        return self._cache.get(partial_func=partial_func, seconds=seconds,
                               return_cached_only=return_cached_only)

    def set_content_type(self, content_type):
        """
        Sets the type of the content.
        :param content_type:
        :return:
        """
        self.get_plugin().set_content_type(content_type)
        pass

    def add_sort_method(self, *sort_methods):
        """
        Adds a sort method for the current content.
        :param sort_methods:
        :return:
        """
        for sort_method in sort_methods:
            self.get_plugin().add_sort_method(sort_method)
            pass
        pass

    def register_path(self, re_path, method_name):
        """
        Registers a new method by name (string) for the given regular expression
        :param re_path: regular expression of the path
        :param method_name: name of the method
        :return:
        """
        self._dict_path[re_path] = method_name

    def navigate(self, path, params=None):
        if not params:
            params = {}
            pass

        for key in self._dict_path:
            re_match = re.search(key, path, re.UNICODE)
            if re_match is not None:
                method_name = self._dict_path.get(key, '')
                method = getattr(self, method_name)
                if method is not None:
                    result = method(path, params, re_match)
                    if not isinstance(result, tuple):
                        result = result, {}
                        pass
                    return result
                pass
            pass

        from . import KodimonException

        raise KodimonException("Mapping for path '%s' not found" % path)

    def on_search(self, search_text, path, params, re_match):
        """
        This method must be implemented by the derived class if the default search will be used.
        :param search_text:
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        raise NotImplementedError()

    def on_root(self, path, params, re_match):
        """
        This method must be implemented by the derived class
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        raise NotImplementedError()

    def on_watch_later(self, path, params, re_match):
        """
        This method can be implemented by the derived class to set the content type or add a sort method.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        pass

    def _internal_root(self, path, params, re_match):
        """
        Internal method to call the on root event.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        return self.on_root(path, params, re_match)

    def _internal_favorite(self, path, params, re_match):
        """
        Internal implementation of handling favorites.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        import constants

        self.add_sort_method(constants.SORT_METHOD_LABEL_IGNORE_THE)

        command = re_match.group('command')
        if command == 'add':
            from . import json_to_item

            fav_item = json_to_item(params['item'])
            self._favorites.add(fav_item)
            pass
        elif command == 'remove':
            from . import json_to_item

            fav_item = json_to_item(params['item'])
            self._favorites.remove(fav_item)
            self.refresh_container()
            pass
        elif command == 'list':
            import contextmenu

            directory_items = self._favorites.list()

            for directory_item in directory_items:
                context_menu = []
                remove_item = contextmenu.create_remove_from_favs(self.get_plugin(),
                                                                  self.localize(self.LOCAL_FAVORITES_REMOVE),
                                                                  directory_item)
                context_menu.append(remove_item)
                directory_item.set_context_menu(context_menu)
                pass

            return directory_items
        else:
            pass
        pass

    def _internal_watch_later(self, path, params, re_match):
        """
        Internal implementation of handling a watch later list.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        self.on_watch_later(path, params, re_match)

        command = re_match.group('command')
        if command == 'add':
            from . import json_to_item

            item = json_to_item(params['item'])
            self._watch_later.add(item)
            pass
        elif command == 'remove':
            from . import json_to_item

            item = json_to_item(params['item'])
            self._watch_later.remove(item)
            self.refresh_container()
            pass
        elif command == 'list':
            video_items = self._watch_later.list()

            from . import contextmenu

            for video_item in video_items:
                context_menu = []
                remove_item = contextmenu.create_remove_from_watch_later(self.get_plugin(),
                                                                         self.localize(self.LOCAL_WATCH_LATER_REMOVE),
                                                                         video_item)
                context_menu.append(remove_item)
                video_item.set_context_menu(context_menu)
                pass

            return video_items
        else:
            # do something
            pass
        pass

    def _internal_search(self, path, params, re_match):
        """
        Internal implementation of handling a search.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        from . import json_to_item, DirectoryItem

        command = re_match.group('command')
        if command == 'new' or (command == 'list' and self._search.is_empty()):
            from . import input

            result, text = input.on_keyboard_input(self.localize(self.LOCAL_SEARCH_TITLE))
            if result:
                self._search.update(text)

                # we adjust the path and params as would it be a normal query
                new_path = self.PATH_SEARCH+'/query/'
                new_params = {}
                new_params.update(params)
                new_params['q'] = text
                return self.on_search(text, new_path, new_params, re_match)
            pass
        elif command == 'remove':
            query = params['q']
            self._search.remove(query)
            self.refresh_container()
            return True
        elif command == 'query':
            query = params['q']
            self._search.update(query)
            return self.on_search(query, path, params, re_match)
        else:
            result = []

            # 'New Search...'
            search_item = DirectoryItem('[B]' + self.localize(self.LOCAL_SEARCH_NEW) + '[/B]',
                                        self.create_uri([self.PATH_SEARCH, 'new']),
                                        image=self.create_resource_path('media/search.png'))
            search_item.set_fanart(self.get_fanart())
            result.append(search_item)

            from . import contextmenu

            for search in self._search.list():
                # little fallback for old history entries
                if isinstance(search, DirectoryItem):
                    search = search.get_name()
                    pass

                # we create a new instance of the SearchItem
                search_item = DirectoryItem(search,
                                            self.create_uri([self.PATH_SEARCH, 'query'], {'q': search}),
                                            image=self.create_resource_path('media/search.png'))
                search_item.set_fanart(self.get_fanart())
                context_menu = [contextmenu.create_remove_from_search_history(self.get_plugin(),
                                                                              self.localize(self.LOCAL_SEARCH_REMOVE),
                                                                              search_item)]
                search_item.set_context_menu(context_menu)
                result.append(search_item)
                pass
            return result, {self.RESULT_CACHE_TO_DISC: False}

        return False

    def handle_exception(self, exception_to_handle):
        return True

    def refresh_container(self):
        """
        Needs to be implemented by a mock for testing or the real deal.
        This will refresh the current container or list.
        :return:
        """
        raise NotImplementedError()

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        raise NotImplementedError()

    def log(self, text, log_level=2):
        from . import log
        log_line = '[%s] %s' % (self.get_plugin().get_id(), text)
        log(log_line, log_level)
        pass

    def create_resource_path(self, *args):
        return self._plugin.create_resource_path(*args)

    def create_uri(self, path=None, params=None):
        from . import create_plugin_uri

        return create_plugin_uri(self._plugin, path, params)

    def get_access_manager(self):
        """
        Returns an AccessManager to help with credentials and access_tokens
        :return: AccessManager
        """
        from helper import AccessManager
        return AccessManager(self._plugin.get_settings())

    pass
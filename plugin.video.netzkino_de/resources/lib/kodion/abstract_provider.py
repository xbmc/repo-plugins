import re

from .exceptions import KodionException
from . import items
from . import constants
from . import utils


class AbstractProvider(object):
    RESULT_CACHE_TO_DISC = 'cache_to_disc'  # (bool)

    def __init__(self):
        self._local_map = {
            'kodion.wizard.view.default': 30027,
            'kodion.wizard.view.episodes': 30028,
            'kodion.wizard.view.movies': 30029,
            'kodion.wizard.view.tvshows': 30032,
            'kodion.wizard.view.songs': 30033,
            'kodion.wizard.view.artists': 30034,
            'kodion.wizard.view.albums': 30035
        }

        # map for regular expression (path) to method (names)
        self._dict_path = {}

        # register some default paths
        self.register_path('^/$', '_internal_root')
        self.register_path('^/' + constants.paths.WATCH_LATER + '/(?P<command>add|remove|list)/?$',
                           '_internal_watch_later')
        self.register_path('^/' + constants.paths.FAVORITES + '/(?P<command>add|remove|list)/?$', '_internal_favorite')
        self.register_path('^/' + constants.paths.SEARCH + '/(?P<command>input|query|list|remove|clear|rename)/?$',
                           '_internal_search')
        self.register_path('(?P<path>.*\/)extrafanart\/([\?#].+)?$', '_internal_on_extra_fanart')

        """
        Test each method of this class for the appended attribute '_re_match' by the
        decorator (RegisterProviderPath).
        The '_re_match' attributes describes the path which must match for the decorated method.
        """

        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, 'kodion_re_path'):
                self.register_path(method.kodion_re_path, method_name)
                pass
            pass

        pass

    def get_alternative_fanart(self, context):
        return context.get_fanart()

    def register_path(self, re_path, method_name):
        """
        Registers a new method by name (string) for the given regular expression
        :param re_path: regular expression of the path
        :param method_name: name of the method
        :return:
        """
        self._dict_path[re_path] = method_name
        pass

    def _process_wizard(self, context):
        def _setup_views(_context, view):
            view_manager = utils.ViewManager(_context)
            if not view_manager.update_view_mode(_context.localize(self._local_map['kodion.wizard.view.%s' % view]),
                                                 view):
                return

            _context.get_settings().set_bool(constants.setting.VIEW_OVERRIDE, True)
            pass

        # start the setup wizard
        wizard_steps = []
        if context.get_settings().is_setup_wizard_enabled():
            context.get_settings().set_bool(constants.setting.SETUP_WIZARD, False)

            if utils.ViewManager(context).has_supported_views():
                views = self.get_wizard_supported_views()
                for view in views:
                    if view in utils.ViewManager.SUPPORTED_VIEWS:
                        wizard_steps.append((_setup_views, [context, view]))
                        pass
                    else:
                        context.log_warning('[Setup-Wizard] Unsupported view "%s"' % view)
                        pass
                    pass
                pass
            else:
                skin_id = context.get_ui().get_skin_id()
                context.log("ViewManager: Unknown skin id '%s'" % skin_id)
                pass

            wizard_steps.extend(self.get_wizard_steps(context))
            pass

        if wizard_steps and context.get_ui().on_yes_no_input(context.get_name(),
                                                             context.localize(constants.localize.SETUP_WIZARD_EXECUTE)):
            for wizard_step in wizard_steps:
                wizard_step[0](*wizard_step[1])
                pass
            pass
        pass

    def get_wizard_supported_views(self):
        return ['default']

    def get_wizard_steps(self, context):
        # can be overridden by the derived class
        return []

    def navigate(self, context):
        self._process_wizard(context)

        path = context.get_path()

        for key in self._dict_path:
            re_match = re.search(key, path, re.UNICODE)
            if re_match is not None:
                method_name = self._dict_path.get(key, '')
                method = getattr(self, method_name)
                if method is not None:
                    result = method(context, re_match)
                    if not isinstance(result, tuple):
                        result = result, {}
                        pass
                    return result
                pass
            pass

        raise KodionException("Mapping for path '%s' not found" % path)

    def on_extra_fanart(self, context, re_match):
        """
        The implementation of the provider can override this behavior.
        :param context:
        :param re_match:
        :return:
        """
        return None

    def _internal_on_extra_fanart(self, context, re_match):
        path = re_match.group('path')
        new_context = context.clone(new_path=path)
        return self.on_extra_fanart(new_context, re_match)

    def on_search(self, search_text, context, re_match):
        """
        This method must be implemented by the derived class if the default search will be used.
        :param search_text:
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        raise NotImplementedError()

    def on_root(self, context, re_match):
        """
        This method must be implemented by the derived class
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        raise NotImplementedError()

    def on_watch_later(self, context, re_match):
        """
        This method can be implemented by the derived class to set the content type or add a sort method.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        pass

    def _internal_root(self, context, re_match):
        """
        Internal method to call the on root event.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        return self.on_root(context, re_match)

    def _internal_favorite(self, context, re_match):
        """
        Internal implementation of handling favorites.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        context.add_sort_method(constants.sort_method.LABEL_IGNORE_THE)

        params = context.get_params()

        command = re_match.group('command')
        if command == 'add':
            fav_item = items.from_json(params['item'])
            context.get_favorite_list().add(fav_item)
            pass
        elif command == 'remove':
            fav_item = items.from_json(params['item'])
            context.get_favorite_list().remove(fav_item)
            context.get_ui().refresh_container()
            pass
        elif command == 'list':

            directory_items = context.get_favorite_list().list()

            for directory_item in directory_items:
                context_menu = [(context.localize(constants.localize.WATCH_LATER_REMOVE),
                                 'RunPlugin(%s)' % context.create_uri([constants.paths.FAVORITES, 'remove'],
                                                                      params={'item': items.to_jsons(directory_item)}))]
                directory_item.set_context_menu(context_menu)
                pass

            return directory_items
        else:
            pass
        pass

    def _internal_watch_later(self, context, re_match):
        """
        Internal implementation of handling a watch later list.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        self.on_watch_later(context, re_match)

        params = context.get_params()

        command = re_match.group('command')
        if command == 'add':
            item = items.from_json(params['item'])
            context.get_watch_later_list().add(item)
            pass
        elif command == 'remove':
            item = items.from_json(params['item'])
            context.get_watch_later_list().remove(item)
            context.get_ui().refresh_container()
            pass
        elif command == 'list':
            video_items = context.get_watch_later_list().list()

            for video_item in video_items:
                context_menu = [(context.localize(constants.localize.WATCH_LATER_REMOVE),
                                 'RunPlugin(%s)' % context.create_uri([constants.paths.WATCH_LATER, 'remove'],
                                                                      params={'item': items.to_jsons(video_item)}))]
                video_item.set_context_menu(context_menu)
                pass

            return video_items
        else:
            # do something
            pass
        pass

    def _internal_search(self, context, re_match):
        """
        Internal implementation of handling a search.
        :param path:
        :param params:
        :param re_match:
        :return:
        """
        params = context.get_params()

        command = re_match.group('command')
        search_history = context.get_search_history()
        if command == 'remove':
            query = params['q']
            search_history.remove(query)
            context.get_ui().refresh_container()
            return True
        elif command == 'rename':
            query = params['q']
            result, new_query = context.get_ui().on_keyboard_input(context.localize(constants.localize.SEARCH_RENAME),
                                                                   query)
            if result:
                search_history.rename(query, new_query)
                context.get_ui().refresh_container()
                pass
            return True
        elif command == 'clear':
            search_history.clear()
            context.get_ui().refresh_container()
            return True
        elif command == 'input':
            result, query = context.get_ui().on_keyboard_input(context.localize(constants.localize.SEARCH_TITLE))
            if result:
                context.execute(
                    'Container.Update(%s)' % context.create_uri([constants.paths.SEARCH, 'query'], {'q': query}))
                pass

            return True
        elif command == 'query':
            query = params['q']
            search_history.update(query)
            return self.on_search(query, context, re_match)
        else:
            result = []

            # 'New Search...'
            new_search_item = items.NewSearchItem(context, fanart=self.get_alternative_fanart(context))
            result.append(new_search_item)

            for search in search_history.list():
                # little fallback for old history entries
                if isinstance(search, items.DirectoryItem):
                    search = search.get_name()
                    pass

                # we create a new instance of the SearchItem
                search_history_item = items.SearchHistoryItem(context, search,
                                                              fanart=self.get_alternative_fanart(context))
                result.append(search_history_item)
                pass

            if search_history.is_empty():
                context.execute('RunPlugin(%s)' % context.create_uri([constants.paths.SEARCH, 'input']))
                pass

            return result, {self.RESULT_CACHE_TO_DISC: False}

        return False

    def handle_exception(self, context, exception_to_handle):
        return True

    def tear_down(self, context):
        pass

    pass
import json

__author__ = 'bromix'

import time
import tempfile

from ... import utils
from ..abstract_context import AbstractContext
from .settings import MockSettings
from .context_ui import MockContextUI


class MockContext(AbstractContext):
    def __init__(self, path=u'/', params=None, plugin_name='MOCK Plugin', plugin_id='mock.plugin', ):
        AbstractContext.__init__(self, path, params, plugin_name, plugin_id)

        self._ui = None
        self._data_path = tempfile.gettempdir()
        self._settings = MockSettings()
        self._dict_localization = {5000: u'Hello World',
                                   5001: u'MOCK Plugin'}
        pass

    def log(self, text, log_level):
        log_level_2_string = {self.LOG_DEBUG: 'DEBUG',
                              self.LOG_INFO: 'INFO',
                              self.LOG_WARNING: 'WARNING',
                              self.LOG_ERROR: 'ERROR'}
        log_text = utils.strings.to_utf8("[%s] %s" % (log_level_2_string.get(log_level, 'UNKNOWN'), text))
        print log_text
        pass

    def set_localization(self, text_id, value):
        self._dict_localization[text_id] = value
        pass

    def get_language(self):
        return 'en-US'

    def get_system_version(self):
        return (1, 0, 0)

    def get_system_name(self):
        return 'Nightcrawler by bromix'

    def get_ui(self):
        if not self._ui:
            self._ui = MockContextUI(self)
            pass
        return self._ui

    def get_handle(self):
        return 666

    def get_data_path(self):
        return self._data_path

    def get_native_path(self):
        return '\\user\\x\\data\\'

    def get_settings(self):
        return self._settings

    def localize(self, text_id, default=u''):
        return self._dict_localization.get(text_id, default)

    def set_content_type(self, content_type):
        self.log_info("Set ContentType to '%s'" % content_type)
        pass

    def add_sort_method(self, *sort_methods):
        for sort_method in sort_methods:
            self.log_info("add SortMethod '%s'" % (str(sort_method)))
            pass
        pass

    def clone(self, new_path=None, new_params=None):
        if not new_path:
            new_path = self.get_path()
            pass

        if not new_params:
            new_params = self.get_params()
            pass

        new_context = MockContext(path=new_path, params=new_params, plugin_name=self._plugin_name,
                                  plugin_id=self._plugin_id)

        new_context._function_cache = self._function_cache
        new_context._search_history = self._search_history
        new_context._favorite_list = self._favorite_list
        new_context._watch_later_list = self._watch_later_list
        new_context._access_manager = self._access_manager

        return new_context

    def execute(self, command):
        self.log_info("execute '%s'" % command)
        pass

    def sleep(self, milli_seconds):
        time.sleep(milli_seconds / 1000.0)
        pass

    def add_item(self, item):
        self.log_info('Adding item: %s' % json.dumps(item))
        pass

    def end_of_content(self, succeeded=True):
        self.log_info('called "end_of_content"')
        pass

    pass
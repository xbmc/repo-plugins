import tempfile

from ...abstract_plugin import AbstractPlugin
from mock_settings import MockSettings


class MockPlugin(AbstractPlugin):
    def __init__(self, plugin_name='Kodimon Plugin-Dummy', plugin_id='bromix.kodimon.plugin_dummy'):
        AbstractPlugin.__init__(self, plugin_name, plugin_id)

        self._settings = MockSettings()
        self._path = u'/'
        self._params = {}
        self._data_path = tempfile.gettempdir()
        self._dict_localization = {5000: u'Hello World',
                                   5001: u'Kodimon Plugin'}
        pass

    def get_data_path(self):
        return self._data_path

    def set_path(self, path):
        self._path = path

    def set_params(self, params):
        self._params = params

    def get_path(self):
        return self._path

    def get_params(self):
        return self._params

    def get_native_path(self):
        return 'addon'

    def get_settings(self):
        return self._settings

    def localize(self, text_id, default_text=None):
        mapped_text = self._dict_localization.get(text_id, None)

        if mapped_text is None:
            if default_text:
                return default_text
            return unicode(text_id)

        return mapped_text

    def set_content_type(self, content_type):
        from ... import log
        log("Set ContentType to '%s'" % content_type)
        pass

    def add_sort_method(self, sort_method):
        from ... import log
        log("add SortMethod '%s'" % (str(sort_method)))
        pass

    pass
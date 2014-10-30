import tempfile

from ...abstract_plugin import AbstractPlugin
from mock_settings import MockSettings


class MockPlugin(AbstractPlugin):
    def __init__(self, plugin_name='Kodimon Plugin', plugin_id='kodimon.plugin', path=None, params=None):
        AbstractPlugin.__init__(self, plugin_name, plugin_id)
        if not params:
            params = {}
            pass
        if not path:
            path = u''
            pass


        from ... import create_plugin_uri
        self._uri = create_plugin_uri(self, path, params)
        self._data_path = tempfile.gettempdir()
        self._settings = MockSettings()
        self._dict_localization = {5000: u'Hello World',
                                   5001: u'Kodimon Plugin'}
        pass

    def get_handle(self):
        return 666

    def get_data_path(self):
        return self._data_path

    def get_uri(self):
        return self._uri

    def get_native_path(self):
        return 'virtual_path'

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
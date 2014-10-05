import urllib
import os


class AbstractPlugin(object):
    def __init__(self, plugin_name=None, plugin_id=None):
        """

        :param plugin_name:
        :param plugin_id:
        """
        object.__init__(self)

        self._plugin_name = plugin_name
        self._plugin_id = plugin_id
        pass

    def get_data_path(self):
        raise NotImplementedError()

    def get_native_path(self):
        raise NotImplementedError()

    def get_fanart(self):
        return os.path.join(self.get_native_path(), 'fanart.jpg')

    def create_resource_path(self, relative_path):
        path_comps = relative_path.split('/')
        path = os.path.join(self.get_native_path(), 'resources', *path_comps)
        return path

    def get_path(self):
        raise NotImplementedError()

    def get_params(self):
        raise NotImplementedError()

    def get_name(self):
        return self._plugin_name

    def get_id(self):
        return self._plugin_id

    def get_handle(self):
        raise NotImplementedError()

    def get_settings(self):
        raise NotImplementedError()

    def localize(self, text_id, default_text=None):
        raise NotImplementedError()

    def set_content_type(self, content_type):
        raise NotImplementedError()

    def add_sort_method(self, sort_method):
        raise NotImplementedError()
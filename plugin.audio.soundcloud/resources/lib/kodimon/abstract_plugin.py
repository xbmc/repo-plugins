import os
import urllib
import urlparse


class AbstractPlugin(object):
    def __init__(self, plugin_name=None, plugin_id=None):
        """

        :param plugin_name:
        :param plugin_id:
        """
        object.__init__(self)

        self._plugin_name = unicode(plugin_name)
        self._plugin_id = plugin_id
        self._path = None
        self._params = None
        pass

    def get_path(self):
        """
        Returns the relative path (utf-8 decoded) of the plugin.
        :return:
        """
        if not self._path:
            comps = urlparse.urlparse(self._uri)
            self._path = urllib.unquote(comps[2]).decode('utf-8')
            pass

        return self._path

    def get_params(self):
        """
        Returns the params (utf-8 decoded) of the uri
        :return:
        """
        if not self._params:
            self._params = {}
            comps = urlparse.urlparse(self._uri)
            _params = dict(urlparse.parse_qsl(comps[4]))
            for _param in _params:
                self._params[_param] = _params[_param].decode('utf-8')
                pass
            pass

        return self._params

    def get_data_path(self):
        raise NotImplementedError()

    def get_native_path(self):
        raise NotImplementedError()

    def get_icon(self):
        return os.path.join(self.get_native_path(), 'icon.png')

    def get_fanart(self):
        return os.path.join(self.get_native_path(), 'fanart.jpg')

    def create_resource_path(self, *args):
        path_comps = []
        for arg in args:
            path_comps.extend(arg.split('/'))
            pass
        path = os.path.join(self.get_native_path(), 'resources', *path_comps)
        return path

    def get_uri(self):
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
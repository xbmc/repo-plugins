import hashlib


class BaseItem(object):
    VERSION = 2
    INFO_DATE = ('data', unicode)
    INFO_DATEADDED = ('dateadded', unicode)

    def __init__(self, name, uri, image=u''):
        self._version = BaseItem.VERSION
        self._name = unicode(name)
        self._uri = unicode(uri)
        self._image = ""
        self._fanart = ""
        self._context_menu = None
        self.set_image(image)
        self._info_labels = {}
        pass

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        name = self._name
        uri = self._uri
        obj_str = "------------------------------\n'%s'\nURI: %s\nImage: %s\n------------------------------" % (
            name, uri, self._image)
        return obj_str

    def set_info(self, info_type, info_value):
        def _check_instance(_info_type):
            if _info_type[1] == list:
                return True

            return False

        def _to_unicode(_info_value):
            if isinstance(_info_value, list):
                for i in range(len(_info_value)):
                    _item = unicode(_info_value[i])
                    _info_value[i] = _item
                    pass
                pass

            return _info_value
            pass

        if _check_instance(info_type) and not isinstance(info_value, info_type[1]):
            found_type = str(type(info_value))
            from . import KodimonException

            raise KodimonException(
                "Wrong type of for '%s' (expected '%s' but found '%s')" % (info_type[0], str(info_type[1]), found_type))

        casted_value = info_value
        if not isinstance(info_value, info_type[1]):
            casted_value = info_type[1](info_value)
            pass

        casted_value = _to_unicode(casted_value)

        self._info_labels[info_type[0]] = casted_value
        pass

    def get_info(self, info_type):
        """
        Returns only one info given by the type
        :param info_type:
        :return:
        """
        if info_type[0] in self._info_labels:
            return self._info_labels[info_type[0]]

        return None

    def get_info_labels(self):
        """
        Returns the complete dictionary of info labels
        :return:
        """
        return self._info_labels

    def get_id(self):
        """
        Returns a unique id of the item.
        :return: unique id of the item.
        """
        m = hashlib.md5()
        m.update(self._name.encode('utf-8'))
        m.update(self._uri.encode('utf-8'))
        return m.hexdigest()

    def get_name(self):
        """
        Returns the name of the item.
        :return: name of the item.
        """
        return self._name

    def get_uri(self):
        """
        Returns the path of the item.
        :return: path of the item.
        """
        return self._uri

    def set_image(self, image):
        if image:
            self._image = unicode(image)
        else:
            self._image = u''
        pass

    def get_image(self):
        return self._image

    def set_fanart(self, fanart):
        if fanart:
            self._fanart = fanart
        pass

    def get_fanart(self):
        return self._fanart

    def set_context_menu(self, context_menu):
        if len(context_menu) == 0:
            self._context_menu = None
        else:
            self._context_menu = context_menu
        pass

    def get_context_menu(self):
        return self._context_menu

    def set_date_added(self, year, month, day, hour, minute, second=0):
        date_time_str = '%04d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second)
        self.set_info(self.INFO_DATEADDED, date_time_str)
        pass

    def set_date(self, year, month, day):
        date_str = '%02d.%02d.%04d' % (day, month, year)
        self.set_info(self.INFO_DATE, date_str)
        pass

    pass
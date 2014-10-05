from .base_item import BaseItem


class DirectoryItem(BaseItem):
    def __init__(self, name, path, params=None, image=u''):
        if not params:
            params = {}
            pass

        BaseItem.__init__(self, name, path, params, image)
        pass

    pass
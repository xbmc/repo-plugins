from .base_item import BaseItem


class DirectoryItem(BaseItem):
    def __init__(self, name, uri, image=u''):
        BaseItem.__init__(self, name, uri, image)
        pass

    pass
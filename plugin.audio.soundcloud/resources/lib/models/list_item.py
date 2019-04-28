import xbmcgui


class ListItem:
    id = 0
    label = ""
    label2 = None

    def __init__(self, id, label):
        self.id = id
        self.label = label

    def to_list_item(self, addon_base):
        return addon_base, xbmcgui.ListItem(label=self.label), False

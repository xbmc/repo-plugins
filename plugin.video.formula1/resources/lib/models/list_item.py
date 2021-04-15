import xbmcgui


class ListItem:
    id = 0
    label = ""
    label2 = None
    thumb = ""

    def __init__(self, item_id, label):
        self.id = item_id
        self.label = label

    def to_list_item(self, addon_base):
        return addon_base, xbmcgui.ListItem(label=self.label), False

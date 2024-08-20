class BaseItemSkinDefaults(dict):
    baseitem_default_properties = [
        ('base_label', ('label',), None),
        ('base_title', ('title',), None),
        ('base_icon', ('icon',), None),
        ('base_dbtype', ('dbtype',), None),
    ]

    baseitem_functions = {
        'split': lambda v: v.split(' / ')[0],
        'boolean': 'boolean'
    }

    def get_skin_baseitem_properties(self):
        import json
        import xbmcvfs
        import contextlib

        filepath = 'special://skin/extras/tmdbhelper/baseitem.json'

        response = None
        with contextlib.suppress(IOError, json.JSONDecodeError):
            with xbmcvfs.File(filepath, 'r') as file:
                response = json.load(file)

        if not response:
            return []

        def get_item_tuple(k, v):
            key = f'base_{k}'
            values = v.get('infolabels') or []
            function = self.baseitem_functions.get(v.get('function'))
            return (key, values, function)

        return [get_item_tuple(k, v) for k, v in response.items()]

    def __missing__(self, key):
        self[key] = self.get_skin_baseitem_properties() + self.baseitem_default_properties
        return self[key]

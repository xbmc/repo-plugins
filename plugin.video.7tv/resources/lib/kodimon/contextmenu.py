import json


def create_run_plugin(plugin, label, path='', params=None):
    if not params:
        params = {}
        pass

    from . import create_plugin_url
    return (label, 'RunPlugin(' + create_plugin_url(plugin, path, params) + ')')


def create_add_to_favs(plugin, label, base_item):
    from . import item_to_json, create_content_path, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             path=create_content_path(AbstractProvider.PATH_FAVORITES, 'add'),
                             params=params)


def create_remove_from_favs(plugin, label, base_item):
    from . import item_to_json, create_content_path, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             path=create_content_path(AbstractProvider.PATH_FAVORITES, 'remove'),
                             params=params)


def create_add_to_watch_later(plugin, label, base_item):
    from . import item_to_json, create_content_path, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             path=create_content_path(AbstractProvider.PATH_WATCH_LATER, 'add'),
                             params=params)


def create_remove_from_watch_later(plugin, label, base_item):
    from . import item_to_json, create_content_path, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             path=create_content_path(AbstractProvider.PATH_WATCH_LATER, 'remove'),
                             params=params)


def create_remove_from_search_history(plugin, label, base_item):
    from . import item_to_json, create_content_path, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             path=create_content_path(AbstractProvider.PATH_SEARCH, 'remove'),
                             params=params)
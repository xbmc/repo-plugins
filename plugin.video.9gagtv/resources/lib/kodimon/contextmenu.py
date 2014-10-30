import json


def create_run_plugin(plugin, label, path, params=None):
    """
    :param plugin:
    :param label:
    :param path: can be either string or list of path components
    :param params:
    :return:
    """
    if not params:
        params = {}
        pass

    from . import create_plugin_uri
    return (label, 'RunPlugin(' + create_plugin_uri(plugin, path, params) + ')')


def create_add_to_favs(plugin, label, base_item):
    from . import item_to_json, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             [AbstractProvider.PATH_FAVORITES, 'add'],
                             params=params)


def create_remove_from_favs(plugin, label, base_item):
    from . import item_to_json, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             [AbstractProvider.PATH_FAVORITES, 'remove'],
                             params=params)


def create_add_to_watch_later(plugin, label, base_item):
    from . import item_to_json, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             [AbstractProvider.PATH_WATCH_LATER, 'add'],
                             params=params)


def create_remove_from_watch_later(plugin, label, base_item):
    from . import item_to_json, AbstractProvider

    params = {'item': json.dumps(item_to_json(base_item))}

    return create_run_plugin(plugin,
                             label,
                             [AbstractProvider.PATH_WATCH_LATER, 'remove'],
                             params=params)


def create_remove_from_search_history(plugin, label, base_item):
    from . import AbstractProvider
    return create_run_plugin(plugin,
                             label,
                             [AbstractProvider.PATH_SEARCH, 'remove'],
                             params={'q': base_item.get_name()})
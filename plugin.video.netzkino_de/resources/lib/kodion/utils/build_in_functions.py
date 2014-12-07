import json

from .. import constants
from .. import items


def run_plugin(context, path, params=None):
    """
    :param context:
    :param path: can be either string or list of path components
    :param params:
    :return:
    """
    if not params:
        params = {}
        pass

    return 'RunPlugin(' + context.create_uri(path, params) + ')'


def run_plugin_add_to_favs(context, base_item):
    params = {'item': json.dumps(items.to_json(base_item))}

    return run_plugin(context,
                      [constants.paths.FAVORITES, 'add'],
                      params=params)


def run_plugin_remove_from_favs(context, base_item):
    params = {'item': json.dumps(items.to_json(base_item))}

    return run_plugin(context,
                      [constants.paths.FAVORITES, 'remove'],
                      params=params)


def run_plugin_add_to_watch_later(context, base_item):
    params = {'item': json.dumps(items.to_json(base_item))}

    return run_plugin(context,
                      [constants.paths.WATCH_LATER, 'add'],
                      params=params)


def run_plugin_remove_from_watch_later(context, base_item):
    params = {'item': json.dumps(items.to_json(base_item))}

    return run_plugin(context,
                      [constants.paths.WATCH_LATER, 'remove'],
                      params=params)


def run_plugin_remove_from_search_history(context, base_item):
    return run_plugin(context,
                      [constants.paths.SEARCH, 'remove'],
                      params={'q': base_item.get_name()})
__author__ = 'bromix'

from . import Context
from ..exception import ProviderException


def _process_result(context, result):
    if result is None:
        context.end_of_content()
        pass
    elif isinstance(result, bool):
        context.end_of_content(succeeded=result)
        pass
    elif isinstance(result, dict):
        item_type = result['type']
        if item_type in ['video', 'movie', 'audio', 'music', 'uri']:
            context.resolve_item(result)
        else:
            raise ProviderException('Found not playable item of type "%s"' % item_type)
        pass
    elif isinstance(result, list):
        for item in result:
            context.add_item(item)
            pass
        context.end_of_content()
        pass
    pass


def run(provider, context=None):
    if not context:
        context = Context()
        pass

    context.log_debug('Starting Nightcrawler by bromix...')
    python_version = 'Python (%s)' % '.'.join(map(str, context.get_python_version()))
    system_info_string = '%s (%s)' % (context.get_system_name(), '.'.join(map(str, context.get_system_version())))
    context.log_info(
        'Running: %s (%s) on %s with %s' % (
            context.get_name(), context.get_version(), system_info_string, python_version))
    context.log_debug('Path: "%s"' % context.get_path())
    context.log_debug('Params: "%s"' % unicode(context.get_params()))

    # start the navigation
    result = None
    try:
        result = provider.navigate(context)
        _process_result(context, result)
        pass
    except ProviderException, ex:
        result = provider.handle_exception(context, ex)
        if result:
            context.log_error(ex.__str__())
            context.get_ui().on_ok('Exception in ContentProvider', ex.__str__())
            context.end_of_content(succeeded=False)
            return
        pass

    provider.tear_down(context)
    context.log_debug('Shutdown of Nightcrawler')
    pass

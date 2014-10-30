from ... import constants
import urlparse


def run(provider):
    from ... import KodimonException, VideoItem

    plugin = provider.get_plugin()
    results = None
    try:
        results = provider.navigate(plugin.get_path(), plugin.get_params())
    except KodimonException, ex:
        if provider.handle_exception(ex):
            provider.log(ex.message, constants.LOG_ERROR)
            pass
        return

    result = results[0]
    options = {}
    options.update(results[1])

    if isinstance(result, bool) and not result:
        log("navigate returned 'False'")
    elif isinstance(result, VideoItem):
        log("resolve video item for '%s'" % (result.get_name()))
    elif isinstance(result, list):
        for content_item in result:
            log("%s" % (content_item.get_name()))
            pass
        pass
    else:
        # handle exception
        pass

    provider.shut_down()
    pass


def log(text, log_level=2):
    log_level_2_string = {0: 'DEBUG',
                          1: 'INFO',
                          2: 'NOTICE',
                          3: 'WARNING',
                          4: 'ERROR',
                          5: 'SEVERE',
                          6: 'FATAL',
                          7: 'NONE'}

    print "[%s] %s" % (log_level_2_string.get(log_level, 'UNKNOWN'), text)
    pass


def refresh_container():
    log("refreshContainer()")
    pass
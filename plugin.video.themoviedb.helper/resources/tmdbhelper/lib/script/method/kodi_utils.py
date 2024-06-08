# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


def container_refresh():
    from tmdbhelper.lib.addon.tmdate import set_timestamp
    from jurialmunkey.window import get_property
    from tmdbhelper.lib.addon.plugin import executebuiltin
    executebuiltin('Container.Refresh')
    get_property('Widgets.Reload', set_property=f'{set_timestamp(0, True)}')


def split_value(split_value, separator=None, **kwargs):
    """ Split string values and output to window properties """
    from jurialmunkey.window import get_property
    if not split_value:
        return
    v = f'{split_value}'
    s = separator or ' / '
    p = kwargs.get("property") or "TMDbHelper.Split"
    for x, i in enumerate(v.split(s)):
        get_property(f'{p}.{x}', set_property=i, prefix=-1)


def kodi_setting(kodi_setting, **kwargs):
    """ Get Kodi setting value and output to window property """
    from tmdbhelper.lib.api.kodi.rpc import get_jsonrpc
    from jurialmunkey.window import get_property
    method = "Settings.GetSettingValue"
    params = {"setting": kodi_setting}
    response = get_jsonrpc(method, params)
    get_property(
        name=kwargs.get('property') or 'KodiSetting',
        set_property=f'{response.get("result", {}).get("value", "")}')


def do_wikipedia_gui(wikipedia, tmdb_type=None, **kwargs):
    """ Reroutes to wikipedia script: Included for legacy purposes """
    from xbmc import executebuiltin
    from tmdbhelper.lib.addon.plugin import get_language
    language = get_language()[:2]
    cmd = f'script.wikipedia,wikipedia={wikipedia},xml_file=script-tmdbhelper-wikipedia.xml'
    if tmdb_type:
        cmd = f'{cmd},tmdb_type={tmdb_type}'
    if language:
        cmd = f'{cmd},language={language}'
    executebuiltin(f'RunScript({cmd})')

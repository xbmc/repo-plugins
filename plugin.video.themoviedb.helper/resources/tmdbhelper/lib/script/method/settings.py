# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


def configure_provider_allowlist():
    from xbmcgui import Dialog
    from tmdbhelper.lib.api.tmdb.api import TMDb
    from tmdbhelper.lib.addon.plugin import get_localized, get_setting, set_setting
    tmdb_api = TMDb()

    def _get_available_providers():
        available_providers = set()
        for tmdb_type in ['movie', 'tv']:
            results = tmdb_api.get_request_lc('watch/providers', tmdb_type, watch_region=tmdb_api.iso_country).get('results')
            if not results:
                continue
            available_providers |= {i.get('provider_name') for i in results}
        return available_providers

    available_providers = _get_available_providers()
    if not available_providers:
        return
    available_providers = sorted(available_providers)

    provider_allowlist = get_setting('provider_allowlist', 'str')
    provider_allowlist = provider_allowlist.split(' | ') if provider_allowlist else []
    preselected = [x for x, i in enumerate(available_providers) if not provider_allowlist or i in provider_allowlist]
    indices = Dialog().multiselect(get_localized(32437), available_providers, preselect=preselected)
    if indices is None:
        return

    selected_providers = [available_providers[x] for x in indices]
    if not selected_providers:
        return
    set_setting('provider_allowlist', ' | '.join(selected_providers), 'str')
    Dialog().ok(get_localized(32438), get_localized(32439))

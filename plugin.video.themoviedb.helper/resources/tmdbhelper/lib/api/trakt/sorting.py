from tmdbhelper.lib.addon.plugin import get_localized


def get_sort_methods(info=None):
    items = [
        {
            'name': f'{get_localized(32287)}: {get_localized(32451)} {get_localized(32286)}',
            'params': {'sort_by': 'rank', 'sort_how': 'asc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32452)} {get_localized(32286)}',
            'params': {'sort_by': 'rank', 'sort_how': 'desc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(20382).capitalize()}',
            'params': {'sort_by': 'added', 'sort_how': 'desc'},
            'blocklist': ('trakt_collection',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32473)}',
            'params': {'sort_by': 'collected', 'sort_how': 'desc'},
            'allowlist': ('trakt_collection',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(369)} (A-Z)',
            'params': {'sort_by': 'title', 'sort_how': 'asc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(369)} (Z-A)',
            'params': {'sort_by': 'title', 'sort_how': 'desc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(16102)}',
            'params': {'sort_by': 'watched', 'sort_how': 'desc', 'extended': 'sync'},
            'allowlist': ('trakt_userlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(563)}',
            'params': {'sort_by': 'percentage', 'sort_how': 'desc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(345)} {get_localized(584)}',
            'params': {'sort_by': 'year', 'sort_how': 'asc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(345)} {get_localized(585)}',
            'params': {'sort_by': 'year', 'sort_how': 'desc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32453).capitalize()}',
            'params': {'sort_by': 'plays', 'sort_how': 'asc', 'extended': 'sync'},
            'allowlist': ('trakt_userlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32205)}',
            'params': {'sort_by': 'plays', 'sort_how': 'desc', 'extended': 'sync'},
            'allowlist': ('trakt_userlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32242)} {get_localized(584)}',
            'params': {'sort_by': 'released', 'sort_how': 'asc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32242)} {get_localized(585)}',
            'params': {'sort_by': 'released', 'sort_how': 'desc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32454)} {get_localized(2050)}',
            'params': {'sort_by': 'runtime', 'sort_how': 'asc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32455)} {get_localized(2050)}',
            'params': {'sort_by': 'runtime', 'sort_how': 'desc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(205)}',
            'params': {'sort_by': 'votes', 'sort_how': 'desc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(32175)}',
            'params': {'sort_by': 'popularity', 'sort_how': 'desc', 'extended': 'full'},
            'allowlist': ('trakt_userlist', 'trakt_watchlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(575)}',
            'params': {'sort_by': 'watched', 'sort_how': 'desc', 'extended': 'inprogress'},
            'allowlist': ('trakt_userlist',)},
        {
            'name': f'{get_localized(32287)}: {get_localized(590)}',
            'params': {'sort_by': 'random'}}]

    return [
        i for i in items
        if (
            ('allowlist' not in i or info in i['allowlist'])
            and ('blocklist' not in i or info not in i['blocklist'])
        )]

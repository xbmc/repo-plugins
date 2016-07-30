config = {
    'types': {
      'by_type': 'Format',
      'by_language': 'Language',
      'by_location': 'Location'
    },
    'endpoints': {
        'base_url': 'http://vtuner.com/setupapp/guide/asp/BrowseStations',
        'search_items': '/SearchForm.asp?sSearchInput={0}&sSearchType=&iCurrPage='
    },
    'paths': {
        'base_path': 'special://home/addons/plugin.audio.tunir'
    },
    'icons': {
        'by_type': 'DefaultMusicGenres.png',
        'by_language': 'DefaultAddonSubtitles.png',
        'by_location': 'DefaultAddonLanguage.png',
        'by_editor': 'DefaultMusicTop100.png',
        'by_search': 'DefaultMusicSongs.png',
        'by_favorites': 'DefaultPlaylist.png'
    }
}

config['endpoints']['by_type'] = '{0}/StartPage.asp?sBrowseType={1}'\
    .format(config['endpoints']['base_url'], config['types']['by_type'])
config['endpoints']['by_language'] = '{0}/StartPage.asp?sBrowseType={1}'\
    .format(config['endpoints']['base_url'], config['types']['by_language'])
config['endpoints']['by_location'] = '{0}/StartPage.asp?sBrowseType={1}'\
    .format(config['endpoints']['base_url'], config['types']['by_location'])
config['endpoints']['base_stations'] = '{0}/BrowsePremiumStations.aspq?sBrowseType=Location'\
    .format(config['endpoints']['base_url'])
config['paths']['fanarts'] = '{0}/resources/media/fanarts'.format(config['paths']['base_path'])

import re
import sys

import routing

from directory import Directory
from kodi import Kodi
from orf_on import OrfOn

SETTINGS_FILE = 'settings.json'
CHANNEL_MAP_FILE = 'channels.json'
SEARCH_HISTORY_FILE = 'search_history'

route_plugin = routing.Plugin()
kodi_worker = Kodi(route_plugin)
if not sys.argv[0].startswith('plugin://' + kodi_worker.addon_id + '/dialog'):
    channel_map, channel_map_cached = kodi_worker.get_cached_file(CHANNEL_MAP_FILE)
    settings, settings_cached = kodi_worker.get_cached_file(SETTINGS_FILE)
    api = OrfOn(channel_map=channel_map, settings=settings, useragent=kodi_worker.useragent, kodi_worker=kodi_worker)
    api.set_pager_limit(kodi_worker.pager_limit)
    api.set_segments_behaviour(kodi_worker.use_segments)

    kodi_worker.set_geo_lock(api.is_geo_locked())
    channel_map = api.get_channel_map()
    settings = api.get_settings()

    # Only overwrite if cache was invalidated
    if not channel_map_cached:
        kodi_worker.save_json(channel_map, CHANNEL_MAP_FILE)

    if not settings_cached:
        kodi_worker.save_json(settings, SETTINGS_FILE)


@route_plugin.route('/')
def get_main_menu():
    kodi_worker.log("Loading Main Menu", 'route')
    if kodi_worker.is_geo_locked():
        kodi_worker.render(
            Directory(
                kodi_worker.get_translation(30128, 'Geo lock active', ' [COLOR red]*** %s ***[/COLOR]'),
                kodi_worker.get_translation(30129, 'Some content may not be available in your country'),
                '/', translator=kodi_worker))
    index_directories = api.get_main_menu()
    for index_directory in index_directories:
        kodi_worker.render(index_directory)
    if not kodi_worker.hide_accessibility_menu():
        kodi_worker.render(Directory(kodi_worker.get_translation(30147, 'Accessibility'), '', '/accessibility', '', 'accessibility', translator=kodi_worker))
    kodi_worker.list_callback(None)


@route_plugin.route('/page/start')
def get_frontpage():
    kodi_worker.log("Loading Frontpage Teasers", 'route')
    teasers = api.get_frontpage()
    for teaser in teasers:
        kodi_worker.render(teaser)
    kodi_worker.list_callback()


@route_plugin.route('/accessibility')
def get_accessibility_menu():
    if not kodi_worker.hide_sign_language():
        kodi_worker.render(api.get_sign_language_menu())
    if not kodi_worker.hide_audio_description():
        kodi_worker.render(api.get_audio_description_menu())
    if kodi_worker.use_subtitles:
        kodi_worker.render(api.get_subtitles_menu())
    kodi_worker.list_callback()


@route_plugin.route('/livestreams')
def get_livestreams():
    kodi_worker.log("Loading Livestream Overview", 'route')
    streams = api.get_live_schedule()
    for stream in streams:
        kodi_worker.render(stream)
    kodi_worker.list_callback()


@route_plugin.route('/restart/<livestreamid>')
def get_live_restart(livestreamid):
    kodi_worker.log("Playing Livestream Restart %s" % livestreamid, 'route')
    livestream_item = api.get_livestream(livestreamid)
    livestream_item = api.get_restart_stream(livestream_item)
    kodi_worker.restart(livestream_item)


@route_plugin.route('/profile/<profileid>')
def get_profile(profileid):
    kodi_worker.log("Loading Profile %s" % profileid, 'route')
    request_url = '/profile/%s' % profileid
    directories = api.get_url(request_url)
    if len(directories) > 1:
        for directory in directories:
            kodi_worker.render(directory)
        kodi_worker.list_callback()
    else:
        videos = api.load_stream_data('/profile/%s/episodes' % profileid)
        kodi_worker.play(videos)


@route_plugin.route('/episode/<episodeid>')
def get_episode(episodeid):
    kodi_worker.log("Playing Episode %s" % episodeid, 'route')
    videos = api.load_stream_data('/episode/%s' % episodeid)
    kodi_worker.play(videos)


@route_plugin.route('/episode/<episodeid>/more')
def get_show_from_episode(episodeid):
    kodi_worker.log("Loading Shows from Episode %s" % episodeid, 'route')
    other_episodes = api.get_related(episodeid)
    for other_episode in other_episodes:
        kodi_worker.render(other_episode)
    kodi_worker.list_callback()


@route_plugin.route('/episode/<episodeid>/segments')
def get_segements(episodeid):
    kodi_worker.log("Playing Episode %s" % episodeid, 'route')
    videos = api.load_stream_data('/episode/%s/segments?limit=500' % episodeid)
    if kodi_worker.use_segments and kodi_worker.show_segments:
        for video in videos:
            kodi_worker.render(video)
        kodi_worker.list_callback()
    else:
        kodi_worker.play(videos)


@route_plugin.route('/segment/<segmentid>')
def get_segement(segmentid):
    kodi_worker.log("Playing Segment %s" % segmentid, 'route')
    videos = api.load_stream_data('/segment/%s' % segmentid)
    kodi_worker.play(videos)


@route_plugin.route('/videoitem/<videoid>')
def get_videoitem(videoid):
    kodi_worker.log("Playing Video %s" % videoid, 'route')
    videos = api.load_stream_data('/videoitem/%s' % videoid)
    kodi_worker.play(videos)


@route_plugin.route('/livestream/<videoid>')
def get_livestream(videoid):
    kodi_worker.log("Playing Livestream %s" % videoid, 'route')
    videos = api.load_stream_data('/livestream/%s' % videoid)
    kodi_worker.play(videos)


@route_plugin.route('/pvr/<channelreel>')
def get_pvr_livestream(channelreel):
    kodi_worker.log("Playing PVR Livestream %s" % channelreel, 'route')
    livestream = api.get_pvr(channelreel)
    if livestream:
        kodi_worker.play([livestream])


@route_plugin.route('/recent')
def get_recently_added():
    videos = api.get_last_uploads()
    for video in videos:
        kodi_worker.render(video)
    kodi_worker.list_callback()


@route_plugin.route('/schedule')
def get_schedule_selection():
    kodi_worker.log("Opening Schedule Selection", 'route')
    items, filters = api.get_schedule_dates()
    selected = kodi_worker.select_dialog(kodi_worker.get_translation(30130, 'Select a date'), items)
    api.log(selected)
    if selected is not False and selected > -1:
        api.log("Loading %s Schedule" % filters[selected])
        request_url = api.api_endpoint_schedule % filters[selected]
        target_url = kodi_worker.plugin.url_for_path(request_url)
        kodi_worker.list_callback()
        kodi_worker.execute('Container.Update(%s, replace)' % target_url)
    else:
        api.log("Canceled selection")


@route_plugin.route('/schedule/<scheduledate>')
def get_schedule(scheduledate):
    kodi_worker.log("Opening Schedule %s" % scheduledate, 'route')
    request_url = api.api_endpoint_schedule % scheduledate
    directories = api.get_url(request_url)
    for directory in directories:
        directory.annotate_channel()
        directory.annotate_time()
        kodi_worker.render(directory)
    kodi_worker.list_callback()


@route_plugin.route('/search')
def get_search():
    kodi_worker.log("Opening Search History", 'route')
    search_link = '/search/query'
    search_dir = Directory(kodi_worker.get_translation(30131, 'Enter search ...', '%s ...'), "", search_link, translator=kodi_worker)
    kodi_worker.render(search_dir)
    directories = kodi_worker.get_stored_directories(SEARCH_HISTORY_FILE)
    for directory in directories:
        kodi_worker.render(directory)
    kodi_worker.list_callback()


@route_plugin.route('/search/results/<query>')
def get_search_results(query):
    directories = api.get_search(query)
    for directory in directories:
        kodi_worker.render(directory)
    kodi_worker.list_callback()


@route_plugin.route('/search-partial/<section>/<query>')
def get_search_partial(section, query):
    directories = api.get_search_partial(section, query, route_plugin.args)
    for directory in directories:
        kodi_worker.render(directory)
    kodi_worker.list_callback()


@route_plugin.route('/search/query')
def get_search_dialog():
    kodi_worker.log("Opening Search Dialog", 'route')
    query = kodi_worker.get_keyboard_input()
    search_url = "/search/results/%s" % query
    search_history_dir = Directory(query, "", search_url, translator=kodi_worker)
    kodi_worker.list_callback()
    if query and query.strip() != "":
        kodi_worker.store_directory(search_history_dir, 'search_history')
        target_url = kodi_worker.plugin.url_for_path(search_url)
    else:
        error_url = '/search'
        target_url = kodi_worker.plugin.url_for_path(error_url)
    kodi_worker.execute('Container.Update(%s, replace)' % target_url)


@route_plugin.route('/dialog/clear_search_history')
def clear_search_history():
    dialog = kodi_worker.get_progress_dialog(kodi_worker.get_translation(30132, 'Clearing search history'))
    dialog.update(0, kodi_worker.get_translation(30133, 'Clearing ...', '%s ...'))
    kodi_worker.clear_stored_directories(SEARCH_HISTORY_FILE)
    dialog.update(100, kodi_worker.get_translation(30134, 'Done'))
    dialog.close()


@route_plugin.route('/dialog/reload_cache')
def clear_cache():
    dialog = kodi_worker.get_progress_dialog('Reloading cache')
    dialog.update(0, kodi_worker.get_translation(30136, 'Reloading cache ...', '%s ...'))
    kodi_worker.log("Reloading channel/settings cache", 'route')
    tmp_channel_map, _ = kodi_worker.get_cached_file(CHANNEL_MAP_FILE)
    tmp_settings, _ = kodi_worker.get_cached_file(SETTINGS_FILE)
    kodi_worker.remove_file(SETTINGS_FILE)
    kodi_worker.remove_file(CHANNEL_MAP_FILE)
    tmp_api = OrfOn(channel_map=tmp_channel_map, settings=tmp_settings, useragent=kodi_worker.useragent, kodi_worker=kodi_worker)
    tmp_api.channel_map = False
    tmp_api.settings = False
    dialog.update(33, kodi_worker.get_translation(30137, 'Loading channels'))
    tmp_channel_map = tmp_api.get_channel_map()
    kodi_worker.save_json(tmp_channel_map, CHANNEL_MAP_FILE)
    dialog.update(66, kodi_worker.get_translation(30138, 'Loading settings'))
    tmp_settings = tmp_api.get_settings()
    kodi_worker.save_json(tmp_settings, SETTINGS_FILE)
    dialog.update(100, kodi_worker.get_translation(30134, 'Done'))
    dialog.close()


@route_plugin.route('<path:url>')
def get_url(url):
    if re.search(r"^/https?://", url):
        url = url[1:]
        kodi_worker.log("Opening Video Url %s" % url, 'route')
        kodi_worker.play_url(url)
    else:
        kodi_worker.log("Opening Generic Url %s" % url, 'route')
        request_url = kodi_worker.build_url(url, route_plugin.args)
        directories = api.get_url(request_url)
        for directory in directories:
            kodi_worker.render(directory)
        kodi_worker.list_callback()


def run():
    route_plugin.run()

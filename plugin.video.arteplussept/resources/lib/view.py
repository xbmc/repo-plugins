from xbmcswift2 import xbmc

from . import api
from . import mapper
from . import hof
from . import utils

def build_home_page(plugin, cached_categories, settings):
    addon_menu = [
        mapper.create_search_item(),
    ]
    try:
        live_stream_data = api.program_video(settings.language, 'LIVE')
        live_stream_item = mapper.map_live_video(live_stream_data, settings.quality, '1')
        addon_menu.append(live_stream_item)
    except:
        xbmc.log("Unable to build live stream item with lang:{ln} quality:{qlt}".format(ln=settings.language, qlt=settings.quality))

    arte_home = api.page(settings.language)
    for zone in arte_home.get('zones'):
        menu_item = mapper.map_zone_to_item(zone, cached_categories)
        if menu_item:
            addon_menu.append(menu_item)
    return addon_menu


def build_categories(plugin, cached_categories, settings):
    categories = [
        mapper.create_search_item(),
        mapper.map_live_video(api.program_video(settings.language, 'LIVE'), settings.quality, '1'),
        mapper.create_favorites_item(),
        mapper.create_last_viewed_item(),
        mapper.create_newest_item(),
        mapper.create_most_viewed_item(),
        mapper.create_last_chance_item(),
    ]
    categories.extend(mapper.map_categories(
        api.categories(settings.language), settings.show_video_streams, cached_categories))
    # categories.append(mapper.create_creative_item())
    categories.append(mapper.create_magazines_item())
    categories.append(mapper.create_week_item())
    return categories


def build_api_category(category_code, settings):
    category = [mapper.map_category_item(item, category_code) for item in
            api.category(category_code, settings.language)]

    return category


def get_cached_category(category_title, most_viewed_categories):
    return most_viewed_categories[category_title]


def build_magazines(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.magazines(settings.language)]


def build_favorites(plugin, settings):
    return [mapper.map_artetv_video(item) for item in
            api.get_favorites(plugin, settings.language, settings.username, settings.password) or
            # display an empty list in case of error. error should be display in a notification
            []]

def add_favorite(plugin, usr, pwd, program_id):
    if 200 == api.add_favorite(plugin, usr, pwd, program_id):
        plugin.notify(msg=plugin.addon.getLocalizedString(30025), image='info')
    else:
        plugin.notify(msg=plugin.addon.getLocalizedString(30026), image='error')

def remove_favorite(plugin, usr, pwd, program_id):
    if 200 == api.remove_favorite(plugin, usr, pwd, program_id):
        plugin.notify(msg=plugin.addon.getLocalizedString(30027), image='info')
    else:
        plugin.notify(msg=plugin.addon.getLocalizedString(30028), image='error')


def build_last_viewed(plugin, settings):
    return [mapper.map_artetv_video(item) for item in
            api.get_last_viewed(plugin, settings.language, settings.username, settings.password) or
            # display an empty list in case of error. error should be display in a notification
            []]

def purge_last_viewed(plugin, usr, pwd):
    if 200 == api.purge_last_viewed(plugin, usr, pwd):
        plugin.notify(msg=plugin.addon.getLocalizedString(30031), image='info')
    else:
        plugin.notify(msg=plugin.addon.getLocalizedString(30032), image='error')



def build_newest(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.home_category('mostRecent', settings.language)]


def build_most_viewed(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.home_category('mostViewed', settings.language)]


def build_last_chance(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.home_category('lastChance', settings.language)]


def build_sub_category_by_code(sub_category_code, settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.subcategory(sub_category_code, settings.language)]


def build_sub_category_by_title(category_code, sub_category_title, settings):
    category = api.category(category_code, settings.language)
    unquoted_title = utils.decode_string(sub_category_title)

    sub_category = hof.find(lambda i: i.get('title') == unquoted_title, category)

    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            sub_category.get('teasers')]


def build_mixed_collection(kind, collection_id, settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.collection(kind, collection_id, settings.language)]


def build_video_streams(program_id, settings):
    item = api.video(program_id, settings.language)

    if item is None:
        raise RuntimeError('Video not found...')

    programId = item.get('programId')
    kind = item.get('kind')

    return mapper.map_streams(item, api.streams(kind, programId, settings.language), settings.quality)


def build_stream_url(plugin, kind, program_id, audio_slot, settings):
    program_stream = api.streams(kind, program_id, settings.language)
    if not program_stream:
        msg=plugin.addon.getLocalizedString(30029)
        plugin.notify(msg=msg.format(strm=program_id, ln=settings.language), image='error')
    else:
        return mapper.map_playable(program_stream, settings.quality, audio_slot, mapper.match_hbbtv)


_useless_kinds = ['CLIP', 'MANUAL_CLIP', 'TRAILER']


def build_weekly(settings):
    programs = hof.flatten([api.daily(date, settings.language)
                            for date in utils.past_week()])

    def keep_video_item(item):
        video = hof.get_property(item, 'video')

        if video is None:
            return False
        return hof.get_property(item, 'kind') not in _useless_kinds

    videos_filtered = [hof.get_property(item, 'video')
                       for item in programs if keep_video_item(item)]

    videos_mapped = [mapper.map_generic_item(
        item, settings.show_video_streams) for item in videos_filtered]
    videos_mapped.sort(key=lambda item: hof.get_property(
        item, 'info.aired'), reverse=True)

    return videos_mapped

def search(plugin, settings):
    query = get_search_query(plugin)
    if not query:
        plugin.end_of_directory(succeeded=False)
    return mapper.map_cached_categories(
        api.search(settings.language, query))

def get_search_query(plugin):
    searchStr = ''
    keyboard = xbmc.Keyboard(searchStr, plugin.addon.getLocalizedString(30012))
    keyboard.doModal()
    if False == keyboard.isConfirmed():
        return
    searchStr = keyboard.getText()
    if len(searchStr) == 0:
        return
    else:
        return searchStr
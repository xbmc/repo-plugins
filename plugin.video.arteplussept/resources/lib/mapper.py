from addon import plugin
from xbmcswift2 import xbmc
from xbmcswift2 import actions
from . import hof
from . import utils

def map_categories(api_categories, show_video_streams, cached_categories):
    categories = []
    for item in api_categories:
        # categories have code MOST_VIEWED, when content is returned in teasers
        # and not available in sub API call
        if item.get('code') == "MOST_VIEWED":
            cat_code = "MOST_VIEWED_{id}".format(id=(len(cached_categories) or 0))
            item['code'] = cat_code
            if item.get('teasers'):
                # build cached categories
                cached_categories[cat_code]=[map_generic_item(teaser, show_video_streams)
                        for teaser in item.get('teasers')]
                categories.append(map_categories_item(item, 'cached_category'))
            else:
                xbmc.log("category \"{cat_title}\" will be ignored, because it contains no teaser".format(cat_title=item.get('title')))
        else:
            categories.append(map_categories_item(item, 'api_category'))
    return categories

def map_categories_item(item, category_rule, category_code=None):
    if(not category_code):
        category_code=item.get('code')
    return {
        'label': utils.colorize(item.get('title'), item.get('color')),
        'path': plugin.url_for(category_rule, category_code=category_code)
    }


# def create_creative_item():
#     return {
#         'label': 'Creative I18N',
#         'path': plugin.url_for('creative')
#     }


def create_favorites_item(label=None):
    if(not label):
        label = plugin.addon.getLocalizedString(30010)
    return {
        'label': label,
        'path': plugin.url_for('favorites')
    }


def create_last_viewed_item(label=None):
    if(not label):
        label = plugin.addon.getLocalizedString(30011)
    return {
        'label': label,
        'path': plugin.url_for('last_viewed'),
        'context_menu': [
            (plugin.addon.getLocalizedString(30030),
                actions.background(plugin.url_for('purge_last_viewed')))
        ]
    }


def create_search_item():
    return {
        'label': plugin.addon.getLocalizedString(30012),
        'path': plugin.url_for('search')
    }


def create_magazines_item():
    return {
        'label': plugin.addon.getLocalizedString(30008),
        'path': plugin.url_for('magazines')
    }


def create_week_item():
    return {
        'label': plugin.addon.getLocalizedString(30009),
        'path': plugin.url_for('weekly')
    }


def create_newest_item():
    return {
        'label': plugin.addon.getLocalizedString(30005),
        'path': plugin.url_for('newest')
    }


def create_most_viewed_item():
    return {
        'label': plugin.addon.getLocalizedString(30006),
        'path': plugin.url_for('most_viewed')
    }


def create_last_chance_item():
    return {
        'label': plugin.addon.getLocalizedString(30007),
        'path': plugin.url_for('last_chance')
    }


def map_category_item(item, category_code):
    title = item.get('title')
    path = plugin.url_for('sub_category_by_title',
                          category_code=category_code, sub_category_title=utils.encode_string(title))

    return {
        'label': title,
        'path': path
    }


def map_generic_item(item, show_video_streams):
    programId = item.get('programId')

    is_playlist = programId.startswith('RC-') or programId.startswith('PL-')
    if not is_playlist:
        return map_video(item, show_video_streams)
    else:
        return map_playlist(item)


# Create a video menu item from a json returned by Arte HBBTV API
def map_video(item, show_video_streams):
    programId = item.get('programId')
    kind = item.get('kind')
    duration = item.get('durationSeconds')
    airdate = item.get('broadcastBegin')
    if airdate is not None:
        airdate = str(utils.parse_date(airdate))

    return {
        'label': utils.format_title_and_subtitle(item.get('title'), item.get('subtitle')),
        'path': plugin.url_for('streams', program_id=programId) if show_video_streams else plugin.url_for('play', kind=kind, program_id=programId),
        'thumbnail': item.get('imageUrl'),
        'is_playable': not show_video_streams,
        'info_type': 'video',
        'info': {
            'title': item.get('title'),
            'duration': duration,
            'genre': item.get('genrePresse'),
            'plot': item.get('shortDescription') or item.get('fullDescription'),
            'plotoutline': item.get('teaserText'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            'country': [country.get('label') for country in item.get('productionCountries', [])],
            'director': item.get('director'),
            'aired': airdate
        },
        'properties': {
            'fanart_image': item.get('imageUrl'),
        },
        'context_menu': [
            (plugin.addon.getLocalizedString(30023),
                actions.background(plugin.url_for('add_favorite', program_id=programId))),
            (plugin.addon.getLocalizedString(30024),
                actions.background(plugin.url_for('remove_favorite', program_id=programId))),
        ],
    }

# Create a video menu item from a json returned by Arte TV API
# Source data example, unable to find public documentation
# {
#   "type": "teaser",
#   "id": "079395-000-A_fr",
#   "kind": "SHOW",
# OR
#   "kind":{"code":"SHOW","label":"Programme","isCollection":false}
#   "programId": "079395-000-A",
#   "language": "fr",
#   "url": "https://www.arte.tv/fr/videos/079395-000-A/maitriser-l-energie-des-etoiles-la-revolution-de-demain/",
#   "title": "Maîtriser l'énergie des étoiles, la révolution de demain",
#   "subtitle": null,
#   "images": [
#     {
#       "url": "https://api-cdn.arte.tv/img/v2/image/te28ppavJQNmHtpNndKqUG/1920x1080?type=TEXT", "format": "landscape", "width": 1920, "height": 1080,
#       "alternateResolutions": [
#         { "url": "https://api-cdn.arte.tv/img/v2/image/te28ppavJQNmHtpNndKqUG/1920x1080?type=TEXT", "width": 1920, "height": 1080, "imageSize": "1920x1080" }
#       ]
#     }
#   ],
#   "markings": [],
#   "geoblocking": null,
#   "warning": null,
#   "description": "La technique de la fusion nucléaire revient régulièrement sur le devant de la scène. Face au défi de la transition énergétique, elle pourrait représenter une puissante alternative,aussi puissante que l'énergie du soleil dont elle entend s'inspirer. Sans déchets radioactifs, sans extractions polluantes, durable, elle est encore à ce stade un chantier pour la science et un gouffre financier. Explications.",
#   "shortDescription": "La technique de la fusion nucléaire revient régulièrement sur le devant de la scène. Face au défi de la transition énergétique, elle pourrait représenter une puissante alternative,aussi puissante que l'énergie du soleil dont elle entend s'inspirer. Sans déchets radioactifs, sans extractions polluantes, durable, elle est encore à ce stade un chantier pour la science et un gouffre financier. Explications.",
#   "beginsAt": "2022-07-01T03:00:00Z",
#   "expireAt": "2023-06-30T03:00:00Z",
#   "availability": { "type": "VOD", "start": "2022-07-01T03:00:00Z", "end": "2023-06-30T03:00:00Z", "hasVideoStreams": true, "broadcastBegin": null, "displayDate": "2022-07-01T03:00:00Z" },
#   "duration": 52,
#   "durationSeconds": 3114,
#   "video_url": "/api/1/player/079395-000-A",
#   "player": {
#     "config": "https://api.arte.tv/api/player/v2/config/fr/079395-000-A"
#   },
#   "playable": true,
#   "stickers": [
#     { "code": "PLAYABLE", "label": "PLAYABLE"}
#   ],
#   "durationLabel": null,
#   "available": true,
#   "trackingPixel": "https://www.arte.tv/ct/?language=fr&support=web&pageid={HOME}&zonename=myarte_favorites&zoneid=myarte_favorites&teasertitle=Maitriser-l-energie-des-etoiles-la-revolution-de-demain&teaserid=079395-000-A&programid=079395-000-A&position=17",
#   "lastviewed": { "is": true, "timecode": 0, "progress": 1 },
#   "favorite": { "is": true }
# }
# Destination object : https://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
def map_artetv_video(item):
    programId = item.get('programId')
    kind = item.get('kind')
    duration = item.get('durationSeconds')
    airdate = item.get('beginsAt') # broadcastBegin
    if airdate is not None:
        airdate = str(utils.parse_artetv_date(airdate))

    fanartUrl = ""
    thumbnailUrl = ""
    if item.get('images') and item.get('images')[0] and item.get('images')[0].get('url'):
        # Remove query param type=TEXT to avoid title embeded in image
        fanartUrl = item.get('images')[0].get('url').replace('?type=TEXT', '')
        # Set same image for fanart and thumbnail to spare network bandwidth
        # and business logic easier to maintain
        #if item.get('images')[0].get('alternateResolutions'):
        #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
        #    if smallerImage and smallerImage.get('url'):
        #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
    if(not fanartUrl):
        fanartUrl = item.get('mainImage').get('url').replace('__SIZE__', '1920x1080')
    thumbnailUrl = fanartUrl

    progress = item.get('lastviewed') and item.get('lastviewed').get('progress') or 0
    time_offset = item.get('lastviewed') and item.get('lastviewed').get('timecode') or 0
    
    if(not isinstance(kind, str)):
        kind = kind.get('code')
    if(kind == 'EXTERNAL'):
        return None

    is_playlist = programId.startswith('RC-') or programId.startswith('PL-')
    path = plugin.url_for('collection' if is_playlist else 'play', kind=kind, program_id=programId)
    
    return {
        'label': utils.format_title_and_subtitle(item.get('title'), item.get('subtitle')),
        'path': path,
        'thumbnail': thumbnailUrl,
        'is_playable': not is_playlist, # item.get('playable') # not show_video_streams
        'info_type': 'video',
        'info': {
            'title': item.get('title'),
            'duration': duration,
            #'genre': item.get('genrePresse'),
            'plot': item.get('description'),
            'plotoutline': item.get('shortDescription'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            #'country': [country.get('label') for country in item.get('productionCountries', [])],
            #'director': item.get('director'),
            #'aired': airdate
            'playcount': progress,
        },
        'properties': {
            'fanart_image': fanartUrl,
            'ResumeTime': str(time_offset),
            'StartPercent': str(progress * 100)
        },
        'context_menu': [
            (plugin.addon.getLocalizedString(30023),
                actions.background(plugin.url_for('add_favorite', program_id=programId))),
            (plugin.addon.getLocalizedString(30024),
                actions.background(plugin.url_for('remove_favorite', program_id=programId))),
        ],
    }


def map_live_video(item, quality, audio_slot):
    programId = item.get('id')
    attr = item.get('attributes')
    meta = attr.get('metadata')

    duration = meta.get('duration').get('seconds')

    fanartUrl = ""
    thumbnailUrl = ""
    if meta.get('images') and meta.get('images')[0] and meta.get('images')[0].get('url'):
        # Remove query param type=TEXT to avoid title embeded in image
        fanartUrl = meta.get('images')[0].get('url').replace('?type=TEXT', '')
        thumbnailUrl = fanartUrl
        # Set same image for fanart and thumbnail to spare network bandwidth
        # and business logic easier to maintain
        #if item.get('images')[0].get('alternateResolutions'):
        #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
        #    if smallerImage and smallerImage.get('url'):
        #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
    streamUrl=map_playable(attr.get('streams'), quality, audio_slot, match_artetv).get('path')

    return {
        'label': utils.format_live_title_and_subtitle(meta.get('title'), meta.get('subtitle')),
        'path': plugin.url_for('play_live', streamUrl=streamUrl),
        # playing the stream from program id makes the live starts from the beginning of the video
        # while it starts the video like the live tv, with the above
        #  'path': plugin.url_for('play', kind='SHOW', program_id=programId.replace('_fr', '')),
        'thumbnail': thumbnailUrl,
        'is_playable': True, # not show_video_streams
        'info_type': 'video',
        'info': {
            'title': meta.get('title'),
            'duration': duration,
            #'genre': item.get('genrePresse'),
            'plot': meta.get('description'),
            #'plotoutline': meta.get('shortDescription'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            #'country': [country.get('label') for country in item.get('productionCountries', [])],
            #'director': item.get('director'),
            #'aired': airdate
            'playcount': 0
        },
        'properties': {
            'fanart_image': fanartUrl,
        }
    }


def map_playlist(item):
    programId = item.get('programId')
    kind = item.get('kind')

    return {
        'label': utils.format_title_and_subtitle(item.get('title'), item.get('subtitle')),
        'path': plugin.url_for('collection', kind=kind, collection_id=programId),
        'thumbnail': item.get('imageUrl'),
        'info': {
            'title': item.get('title'),
            'plotoutline': item.get('teaserText')
        }
    }


def map_streams(item, streams, quality):
    programId = item.get('programId')
    kind = item.get('kind')

    video_item = map_video(item, False)

    # TODO: filter streams by quality
    filtered_streams = None
    for q in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        filtered_streams = [s for s in streams if s.get('quality') == q]
        if len(filtered_streams) > 0:
            break

    if filtered_streams is None or len(filtered_streams) == 0:
        raise RuntimeError('Could not resolve stream...')

    sorted_filtered_streams = sorted(
        filtered_streams, key=lambda s: s.get('audioSlot'))

    def map_stream(video_item, stream):
        audio_slot = stream.get('audioSlot')
        audio_label = stream.get('audioLabel')

        video_item['label'] = audio_label
        video_item['is_playable'] = True
        video_item['path'] = plugin.url_for(
            'play_specific', kind=kind, program_id=programId, audio_slot=str(audio_slot))

        return video_item

    return [map_stream(dict(video_item), stream) for stream in sorted_filtered_streams]


def map_playable(streams, quality, audio_slot, match):
    stream = None
    for q in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        stream = hof.find(lambda s: match(s, q, audio_slot), streams)
        if stream:
            break

    if stream is None:
        raise RuntimeError('Could not resolve stream...')

    return {
        'info_type': 'video',
        'path': stream.get('url'),
    }


def match_hbbtv(item, quality, audio_slot):
    return item.get('quality') == quality and item.get('audioSlot') == audio_slot

def match_artetv(item, quality, audio_slot):
    return item.get('mainQuality').get('code') == quality and str(item.get('slot')) == audio_slot


# Arte TV API page is split into zones. Map a 'zone' to menu item(s).
# Populate cached_categories for zones with videos available in child 'content'
def map_zone_to_item(zone, cached_categories):
    menu_item = None
    title = zone.get('title')
    if(zone.get('id') == '9fc57105-847b-49c5-9b4a-f46863754059'):
        menu_item = create_favorites_item(title)
    elif(zone.get('id') == '67cea6f3-7af0-4ffa-a6c2-59b1da0ecd4b'):
        menu_item = create_last_viewed_item(title)
    elif (zone.get('link')):
        menu_item = map_categories_item(zone, 'api_category', zone.get('link').get('page'))
    else:
        cached_category = map_cached_categories(zone)
        if cached_category:
            category_code = zone.get('code')
            cached_categories[category_code] = cached_category
            menu_item = map_categories_item(zone, 'cached_category')
    return menu_item


def map_cached_categories(zone):
    cached_category = []
    for item in zone.get('content').get('data'):
        menu_video = map_artetv_video(item)
        if(menu_video):
            cached_category.append(menu_video)
    return cached_category
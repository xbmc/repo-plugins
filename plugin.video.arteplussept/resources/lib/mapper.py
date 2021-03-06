from addon import plugin

import hof
import utils


def map_categories_item(item):
    return {
        'label': utils.colorize(item.get('title'), item.get('color')),
        'path': plugin.url_for('category', category_code=item.get('code'))
    }


# def create_creative_item():
#     return {
#         'label': 'Creative I18N',
#         'path': plugin.url_for('creative')
#     }


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
    # code = item.get('code')
    title = item.get('title')

    # if code:
    #     path = plugin.url_for('sub_category_by_code',
    #                           category_code=category_code, sub_category_code=code)
    # else:
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


def map_video(item, show_video_streams):
    programId = item.get('programId')
    kind = item.get('kind')
    duration = int(item.get('duration') or 0) * \
        60 or item.get('durationSeconds')
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


def map_playable(streams, quality, audio_slot):
    stream = None
    for q in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        stream = hof.find(lambda s: match(s, q, audio_slot), streams)
        if stream:
            break

    if stream is None:
        raise RuntimeError('Could not resolve stream...')

    return {
        'path': stream.get('url')
    }


def match(item, quality, audio_slot):
    return item.get('quality') == quality and item.get('audioSlot') == audio_slot

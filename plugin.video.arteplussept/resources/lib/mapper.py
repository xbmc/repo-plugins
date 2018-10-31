from addon import plugin

import hof
import utils


def map_categories_item(item):
    return {
        'label': utils.colorize(item.get('title'), item.get('color')),
        'path': plugin.url_for('category', category_code=item.get('code'))
    }


def create_creative_item():
    return {
        'label': 'Creative I18N',
        'path': plugin.url_for('creative')
    }


def create_magazines_item():
    return {
        'label': 'Emissions I18N',
        'path': plugin.url_for('magazines')
    }


def create_week_item():
    return {
        'label': 'Semaine I18N',
        'path': plugin.url_for('weekly')
    }


def map_category_item(item, category_code):
    code = item.get('code')
    title = item.get('title')

    if code:
        path = plugin.url_for('sub_category_by_code', sub_category_code=code)
    else:
        path = plugin.url_for('sub_category_by_title', category_code=category_code,
                              sub_category_title=utils.sanitize_string(title))

    return {
        'label': title,
        'path': path
    }


def map_generic_item(config):
    programId = config.get('programId')

    is_playlist = programId.startswith('RC-') or programId.startswith('PL-')
    if not is_playlist:
        return map_video(config)
    else:
        return map_playlist(config)


def map_video(config):
    programId = config.get('programId')
    kind = config.get('kind')
    duration = int(config.get('duration') or 0) * \
        60 or config.get('durationSeconds')
    airdate = config.get('broadcastBegin')
    if airdate is not None:
        airdate = str(utils.parse_date(airdate))

    return {
        'label': utils.format_title_and_subtitle(config.get('title'), config.get('subtitle')),
        'path': plugin.url_for('play', kind=kind, program_id=programId),
        'thumbnail': config.get('imageUrl'),
        'is_playable': True,
        'info_type': 'video',
        'info': {
            'title': config.get('title'),
            'duration': duration,
            'genre': config.get('genrePresse'),
            'plot': config.get('shortDescription'),
            'plotoutline': config.get('teaserText'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            #'year': int(config.get('productionYear')),
            'country': [country.get('label') for country in config.get('productionCountries', [])],
            'director': config.get('director'),
            'aired': airdate
        },
        'properties': {
            'fanart_image': config.get('imageUrl'),
        }
    }


def map_playlist(config):
    programId = config.get('programId')
    kind = config.get('kind')

    return {
        'label': utils.format_title_and_subtitle(config.get('title'), config.get('subtitle')),
        'path': plugin.url_for('collection', kind=kind, collection_id=programId),
        'thumbnail': config.get('imageUrl'),
        'info': {
            'title': config.get('title'),
            'plotoutline': config.get('teaserText')
        }
    }


def map_playable(streams, quality):
    stream = None
    for q in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        stream = hof.find(lambda s: match(s, q), streams)
        if stream:
            break
    return {
        'path': stream.get('url')
    }


def match(item, quality):
    return item.get('quality') == quality and item.get('audioSlot') == 1


import api
import mapper
import hof
import utils


def build_categories(settings):
    categories = [
        mapper.create_newest_item(),
        mapper.create_most_viewed_item(),
        mapper.create_last_chance_item(),
    ]
    categories.extend([mapper.map_categories_item(
        item) for item in api.categories(settings.language)])
    # categories.append(mapper.create_creative_item())
    categories.append(mapper.create_magazines_item())
    categories.append(mapper.create_week_item())

    return categories


def build_category(category_code, settings):
    category = [mapper.map_category_item(
        item, category_code) for item in api.category(category_code, settings.language)]

    return category


def build_magazines(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in api.magazines(settings.language)]


def build_newest(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for
            item in api.home_category('mostRecent', settings.language)]


def build_most_viewed(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for
            item in api.home_category('mostViewed', settings.language)]


def build_last_chance(settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for
            item in api.home_category('lastChance', settings.language)]


def build_sub_category_by_code(sub_category_code, settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in api.subcategory(sub_category_code, settings.language)]


def build_sub_category_by_title(category_code, sub_category_title, settings):
    category = api.category(category_code, settings.language)
    unquoted_title = utils.decode_string(sub_category_title)

    sub_category = hof.find(lambda i: i.get('title') == unquoted_title, category)

    return [mapper.map_generic_item(item, settings.show_video_streams) for item in sub_category.get('teasers')]


def build_mixed_collection(kind, collection_id, settings):
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in api.collection(kind, collection_id, settings.language)]


def build_video_streams(program_id, settings):
    item = api.video(program_id, settings.language)

    if item is None:
        raise RuntimeError('Video not found...')

    programId = item.get('programId')
    kind = item.get('kind')

    return mapper.map_streams(item, api.streams(kind, programId, settings.language), settings.quality)


def build_stream_url(kind, program_id, audio_slot, settings):
    return mapper.map_playable(api.streams(kind, program_id, settings.language), settings.quality, audio_slot)


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

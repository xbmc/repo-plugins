
import api
import mapper
import hof


def build_categories(lang):
    categories = [mapper.map_categories_item(
        item) for item in api.categories(lang)]
    categories.append(mapper.create_creative_item())
    categories.append(mapper.create_magazines_item())

    return categories


def build_magazines(lang):
    return [mapper.map_generic_item(item) for item in api.magazines(lang)]


def build_category(category_code, lang):
    category = [mapper.map_category_item(
        item, category_code) for item in api.category(category_code, lang)]

    return category


def build_sub_category_by_code(sub_category_code, lang):
    return [mapper.map_generic_item(item) for item in api.subcategory(sub_category_code, lang)]


def build_sub_category_by_title(category_code, sub_category_title, lang):
    category = api.category(category_code, lang)
    sub_category = hof.find(lambda i: i.get('title') ==
                            sub_category_title, category)

    return [mapper.map_generic_item(item) for item in sub_category.get('teasers')]


def build_mixed_collection(kind, collection_id, lang):
    return [mapper.map_generic_item(item) for item in api.collection(kind, collection_id, lang)]


def build_stream_url(kind, program_id, lang, quality):
    return mapper.map_playable(api.streams(kind, program_id, lang), quality)

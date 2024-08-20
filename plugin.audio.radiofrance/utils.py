#!/bin/python3

from urllib.parse import urlencode, quote_plus
import json
import sys
import requests
from enum import Enum
from time import localtime, strftime

RADIOFRANCE_PAGE = "https://www.radiofrance.fr/"
BRAND_EXTENSION = "/api/live/webradios/"


class Model(Enum):
    Other = 0
    Theme = 1
    Concept = 2
    Highlight = 3
    HighlightElement = 4
    Expression = 5
    ManifestationAudio = 6
    EmbedImage = 7
    PageTemplate = 8
    Brand = 9
    Tag = 10
    Search = 11
    Article = 12
    Event = 13
    Slug = 14
    Station = 15


def create_item_from_page(data):

    if "model" not in data:
        if "content" in data:
            data = data["content"]
        elif "layout" in data:
            data = data["layout"]
        elif "podcastsData" in data:
            data = data["podcastsData"]

    item = create_item(data)
    while len(item.subs) == 1:
        item = create_item(item.subs[0])
    return item


def create_item(data):
    match_list = {
        Model.Other.name: Other,
        Model.Brand.name: Brand,
        Model.Theme.name: Theme,
        Model.Concept.name: Concept,
        Model.Highlight.name: Highlight,
        Model.HighlightElement.name: HighlightElement,
        Model.Expression.name: Expression,
        Model.ManifestationAudio.name: ManifestationAudio,
        Model.EmbedImage.name: EmbedImage,
        Model.PageTemplate.name: PageTemplate,
        Model.Tag.name: Tag,
        Model.Article.name: Article,
        Model.Event.name: Event,
        Model.Slug.name: Slug,
        Model.Station.name: Station,
    }

    if 'model' in data:
        item = match_list[data['model']](data)
    elif 'stationName' in data:
        item = Station(data)
    elif 'items' in data and 'concepts' in data['items'] and 'expressions_articles' in data['items']:
        item = Search(data)
    elif 'slug' in data:
        item = match_list['Slug'](data)
    elif 'brand' in data:
        item = match_list['Brand'](data)
    else:
        item = match_list['Other'](data)

    # Remove singletons
    if item.path is None and len(item.subs) == 1:
        item = create_item(item.subs[0])

    item.elements = item.subs
    while len(item.elements) == 1 and item.elements[0] is not None:
        item.elements = create_item(item.elements[0]).elements

    return item


class Item:
    def __init__(self, data):
        self.id = data['id'] if 'id' in data else "x" * 8

        # Model
        self.model = Model[data['model']] if "model" in data else Model['Other']
        # Path
        self.path = podcast_url(data['path'] if "path" in data else None)

        # Sub elements
        self.subs = []
        self.elements = []

        # Image
        self.image = (
            data['visual']['src']
            if "visual" in data
            and data['visual'] is not None
            and "src" in data['visual']
            else None
        )
        self.icon = (
            data['squaredVisual']['src']
            if "squaredVisual" in data and data['squaredVisual'] is not None
            else None
        )

        # Other pages (tuple (x,n): current page x over n)
        self.pages = (1, 1)
        if "pagination" in data:
            self.pages = (
                data['pagination']['pageNumber'],
                data['pagination']['lastPage'] if "lastPage" in data['pagination'] else data['pagination']['pageNumber'],
            )

        # Title
        self.title = (
            str(data['title'])
            if "title" in data and data['title'] is not None
            else None
        )

    def __str__(self):
        return (
            str(self.pages)
            if self.pages != (1, 1)
            else ""
            + str(self.title)
            + " ["
            + str(self.model)
            + "]"
            + " ["
            + str(len(self.elements))
            + "] ("
            + str(self.path)
            + ")"
            + " — "
            + str(self.id[:8])
        )

    def is_folder(self):
        return self.model in [
            Model['Theme'],
            Model['Concept'],
            Model['Highlight'],
            Model['HighlightElement'],
            Model['PageTemplate'],
            Model['Tag'],
            Model['Article'],
            Model['Slug'],
            Model['Other'],
        ]

    def is_image(self):
        return self.model in [Model['EmbedImage']]

    def is_audio(self):
        return not self.is_folder() and not self.is_image()


class Event(Item):
    def __init__(self, data):
        super().__init__(data)
        self.path = podcast_url(data['href'])


class Station(Item):
    def __init__(self, data):
        super().__init__(data)
        self.model = Model['Station']
        self.title = data['stationName'] + ": " + data['now']['secondLine']['title']
        self.artists = data['stationName']
        self.duration = None
        self.release = None
        self.subs = []
        self.path = data['now']['media']['sources'][0]['url'] if 0 < len(data['now']['media']['sources']) else None


class Tag(Item):
    def __init__(self, data):
        super().__init__(data)
        self.path = podcast_url(data['path'])
        self.subs = data['documents']['items'] if 'documents' in data else []
        if 'documents' in data and 'pagination' in data['documents']:
            self.pages = (
                data['documents']['pagination']['pageNumber'],
                data['documents']['pagination']['lastPage'] if "lastPage" in data['documents']['pagination'] else data['documents']['pagination']['pageNumber'],
            )


class Search(Item):
    def __init__(self, data):
        super().__init__(data)
        self.subs = data['items']['concepts']['contents'] + data['items']['expressions_articles']['contents']


class Article(Item):
    def __init__(self, data):
        super().__init__(data)


class Other(Item):
    def __init__(self, data):
        super().__init__(data)

        if 'link' in data and isinstance(data['link'], str) and data['link'] != "":
            self.path = podcast_url(data['link'])

        self.subs = []
        if "items" in data:
            if isinstance(data['items'], dict):
                for k in ['concepts", "personalities", "expressions_articles']:
                    if k in data['items']:
                        self.subs += data['items'][k]['contents']
            elif isinstance(data['items'], list):
                self.subs += data['items']
            else:
                self.subs = data['items'] if "items" in data else []


class PageTemplate(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.PageTemplate.name:
            self.subs = [data['layout']] if "layout" in data else []


class ManifestationAudio(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.ManifestationAudio.name:
            self.path = podcast_url(data['url'])
            self.duration = int(data['duration'])
            self.release = strftime("%d-%m.%y", localtime(data['created']))


class Concept(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.Concept.name:
            if "expressions" in data:
                self.subs = data['expressions']['items']
                self.pages = (
                    data['expressions']['pageNumber'],
                    data['expressions']['lastPage'] if 'lastPage' in data['expressions'] else data['expressions']['pageNumber'],
                )
            elif "promoEpisode" in data:
                self.subs = data['promoEpisode']['items']


class Highlight(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.Highlight.name:
            self.subs = data['elements']

            # Update title if necessary
            if self.title is None and len(self.subs) == 1:
                self.title = self.subs[0]['title']


class HighlightElement(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.HighlightElement.name:
            if 0 < len(data['links']):
                url = data['links'][0]['path']
                if data['links'][0]['type'] == "path":
                    local_link = data['context']['station'] if 'context' in data else ""
                    self.path = podcast_url(url, local_link)
                else:
                    self.path = podcast_url(url)
            self.subs = data['contents']
            self.image = (
                data['mainImage']['src'] if data['mainImage'] is not None else None
            )

            # Update title if necessary
            if self.title is None and len(self.subs) == 1:
                self.title = self.subs[0]['title']


class Brand(Item):
    def __init__(self, data):
        super().__init__(data)
        brand = data['slug'] if 'slug' in data else data['brand']
        url = podcast_url(brand.split("_")[0] + BRAND_EXTENSION + brand)
        page = requests.get(url).text
        data = json.loads(page)

        self.model = Model['Brand']
        self.station = data['stationName']
        self.now = data['now']['firstLine']['title']
        self.title = self.now + " (" + self.station + ")"
        self.artists = data['now']['secondLine']['title']
        self.duration = 0
        try:
            self.release = data['now']['song']['release']['title']
        except:
            self.release = None
        self.genre = data['now']['thirdLine']['title']
        self.image = None
        for key in ['mainImage", "visual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.image = data[key]['src']
        self.icon = None
        for key in ['squaredVisual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.icon = data[key]['src']
        self.path = data['now']['media']['sources'][0]['url']

class Slug(Item):
    def __init__(self, data):
        super().__init__(data)
        self.model = Model['Slug']
        name = data['slug']
        self.path = podcast_url(name)
        self.title = data['brand'] if 'brand' in data else name


class Expression(Item):
    def __init__(self, data):
        super().__init__(data)
        if data['model'] == Model.Expression.name:
            self.artists = ", ".join([g['name'] for g in (data['guest'] if "guest" in data else [])])
            self.release = strftime("%d-%m.%y", localtime(data['publishedDate'])) if "publishedDate" in data else ""
            self.duration = 0
            manifestations_audio = list([d for d in data['manifestations'] if d['model'] == "ManifestationAudio"])
            if 0 < len(manifestations_audio):
                manifestation = create_item(
                    next(filter(lambda d: d['principal'], manifestations_audio), data['manifestations'][0])
                )
                self.duration = manifestation.duration
                self.path = podcast_url(manifestation.path)


class Theme(Item):
    None


class EmbedImage(Item):
    None


class BrandPage:
    def __init__(self, data):
        self.title = data['stationName']
        self.image = None
        for key in ['mainImage", "visual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.image = data[key]['src']
        self.icon = None
        for key in ['squaredVisual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.icon = data[key]['src']
        self.path = data['now']['media']['sources'][0]['url']


def expand_json(data):
    parsed = json.loads(data)['nodes'][-1]['data']

    def expand_element(e):
        if isinstance(e, dict):
            return expand_dict(e)
        elif isinstance(e, tuple):
            return expand_tuple(e)
        elif isinstance(e, list):
            return expand_tuple(e)
        a = parsed[e]
        if isinstance(a, dict):
            return expand_dict(a)
        elif isinstance(a, tuple):
            return expand_tuple(a)
        elif isinstance(a, list):
            return expand_tuple(a)
        return a

    def expand_tuple(element):
        return [expand_element(v) for v in element]

    def expand_dict(element):
        return {k: expand_element(v) for k, v in list(element.items())}

    return expand_element(parsed[0])


def podcast_url(url, local=""):
    if url is None:
        return None
    print(url)
    return RADIOFRANCE_PAGE + local + "/" + url if url[:8] != "https://" else "" + url


# From plugin.video.orange.fr by f-lawe (https://github.com/f-lawe/plugin.video.orange.fr/)
def localize(string_id: int, **kwargs) -> str:
    """Return the translated string from the .po language files, optionally translating variables."""
    import xbmcaddon

    ADDON = xbmcaddon.Addon()
    if not isinstance(string_id, int) and not string_id.isdecimal():
        return string_id
    return ADDON.getLocalizedString(string_id)


def build_url(query):
    base_url = sys.argv[0]
    url = base_url + "?" + urlencode(query, quote_via=quote_plus)
    return url


if __name__ == "__main__":
    data = sys.stdin.read()
    data = expand_json(data)
    # print(json.dumps(data))
    # exit()

    item = create_item_from_page(data)
    print(str(item))

    subs = item.subs

    while 1 < len(sys.argv):
        index = int(sys.argv.pop())
        print("Using index: " + str(index))
        subs = create_item(subs[index]).elements

    for data in subs:
        sub_item = create_item(data)
        if len(sub_item.subs) == 0 and (sub_item.path is None or sub_item.path == ""):
            continue
        print(str(sub_item))

#!/usr/bin/python3

from urllib.parse import urlencode, quote_plus
import json
import sys
import requests
from enum import Enum
from time import localtime, strftime
from concurrent.futures import ThreadPoolExecutor
import itertools

RADIOFRANCE_PAGE = "https://www.radiofrance.fr"
BRAND_EXTENSION = "/api/live/webradios"

NOT_ITEM_FORMAT = ["TYPED_ELEMENT_NEWSLETTER_SUBSCRIPTION", "TYPED_ELEMENT_AUTOPROMO_IMMERSIVE"]

class Model(Enum):
    OTHER = 0
    THEME = 1
    CONCEPT = 2
    HIGHLIGHT = 3
    HIGHLIGHTELEMENT = 4
    EXPRESSION = 5
    MANIFESTATIONAUDIO = 6
    EMBEDIMAGE = 7
    PAGETEMPLATE = 8
    BRAND = 9
    TAG = 10
    SEARCH = 11
    ARTICLE = 12
    EVENT = 13
    SLUG = 14
    STATION = 15
    STATIONPAGE = 16
    GRID = 17
    PROGRAM = 18
    SLIDER = 19

class Format(Enum):
    SLIDER_CHAINE = 1

def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_key_src(key, data):
    if data is None:
        return None
    value = data.get(key, {})
    if value is not None and 'src' in value:
        return value['src']
    return None

def create_item_from_page(data):
    context = data.get('context', {})

    if "model" not in data:
        if "content" in data:
            data = data["content"]
        elif "layout" in data:
            data = data["layout"]
        elif "podcastsData" in data:
            data = data["podcastsData"]

    item = create_item(0, data, context)
    if not isinstance(item, Item):
        _, data, e = item
        print(json.dumps(data))
        raise(e)
    index = 0
    while len(item.subs) == 1:
        new_item = create_item(index, item.subs[0], context)
        if isinstance(new_item, Item):
            item = new_item
        else:
            break
        index += 1
    return item

def create_item(index, data, context = {}):
    model_map = {
        Model.OTHER.name: Other,
        Model.BRAND.name: Brand,
        Model.THEME.name: Theme,
        Model.CONCEPT.name: Concept,
        Model.HIGHLIGHT.name: Highlight,
        Model.HIGHLIGHTELEMENT.name: HighlightElement,
        Model.EXPRESSION.name: Expression,
        Model.MANIFESTATIONAUDIO.name: ManifestationAudio,
        Model.EMBEDIMAGE.name: EmbedImage,
        Model.PAGETEMPLATE.name: PageTemplate,
        Model.TAG.name: Tag,
        Model.ARTICLE.name: Article,
        Model.EVENT.name: Event,
        Model.SLUG.name: Slug,
        Model.STATIONPAGE.name: StationPage,
        Model.STATION.name: Station,
        Model.GRID.name: Grid,
        Model.PROGRAM.name: Program
    }
    format_map = {
        Format.SLIDER_CHAINE.name : Slider
    }

    try:
        if data.get('model', "").upper() in model_map:
            model_class = model_map[data['model'].upper()]
            item = model_class(data, index, context)
        elif data.get('format', "").upper() in format_map:
            format_class = format_map[data['format'].upper()]
            item = format_class(data, index, context)
        elif 'stationName' in data:
            item = StationDir(data, index, context)
        elif 'items' in data and 'concepts' in data['items'] and 'expressions_articles' in data['items']:
            item = Search(data, index, context)
        elif 'slug' in data:
            item = model_map['SLUG'](data, index, context)
        elif 'brand' in data and not data.get('format', "") in NOT_ITEM_FORMAT :
            item = model_map['BRAND'](data, index, context)
        elif 'grid' in data:
            item = model_map['GRID'](data, index, context)
        elif 'concept' in data and 'expression' in data:
            item = model_map['PROGRAM'](data, index, context)
        else:
            item = model_map['OTHER'](data, index, context)
    except Exception as e:
        return (None, data, e)

    item.index = index
    item.clean_subs()
    item.remove_singletons()
    return item

class Item:
    def __init__(self, data, index, context = {}):
        self.id = data.get('id', "x" * 8)
        self.context = context
        self.model = Model[data.get('model', "Other").upper()]
        url_station = ""
        if data.get('format', None) == "TYPED_ELEMENT_AUTOPROMO" and context.get('station', None) is not None:
            url_station = "/" + context.get('station')
        if isinstance(data.get('link', None), dict) and data['link'].get('type', "") !=  "mail":
            link = data.get('link')
            self.path = podcast_url(link.get('path',link.get('url',"")), url_station)
        else:
            self.path = podcast_url(data.get('path', data.get('href', None)))
        self.subs = []
        try:
            self.image = get_key_src('visual', data)
            self.icon = get_key_src('squaredVisual', data)
        except Exception as e:
            print(json.dumps(data), e)
            raise (e)
        self.pages = (1, 1)
        pagination = data.get('pagination', {'pageNumber': 1})
        self.pages = (pagination['pageNumber'], pagination.get('lastPage', pagination['pageNumber']))
        self.title = str(data.get('title', ""))
        self.index = index

    def clean_subs(self) :
        self.subs = list(filter(lambda i : i is not None, self.subs))

    def remove_singletons(self):
        if self.path is None and len(self.subs) == 1 :
            new_item = create_item(self.index, self.subs[0], self.context)
            if not isinstance(new_item, Item):
                _, data, e = new_item
                print(json.dumps(data))
                raise(e)
            self = new_item
        while len(self.subs) == 1 and self.subs[0] is not None:
            sub_item = create_item(self.index, self.subs[0], self.context)
            if not isinstance(sub_item, Item):
                _, data, e = sub_item
                print(json.dumps(data))
                raise(e)
            self.subs = sub_item.subs if isinstance(sub_item, Item) else []
            self.index += 1

    def __str__(self):
        return (f"{self.pages}{''.join([f'{self.index}. {self.title} [{self.model}] [{len(self.subs)}] ({self.path}) — {self.id[:8]}'])}")

    def is_folder(self):
        return self.model in [Model.THEME, Model.CONCEPT, Model.HIGHLIGHT, Model.HIGHLIGHTELEMENT, Model.PAGETEMPLATE, Model.TAG, Model.ARTICLE, Model.SLUG, Model.STATIONPAGE, Model.GRID, Model.SLIDER, Model.OTHER]

    def is_image(self):
        return self.model in [Model.EMBED_IMAGE]

    def is_audio(self):
        return not self.is_folder() and not self.is_image()

class Event(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.path = podcast_url(data['href'])

class StationDir(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.STATIONPAGE
        self.title = data['stationName']
        self.subs += [dict(data, **{'model': "Station"}), dict(data, **{'model': "StationPage"})]

class Station(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.STATION
        self.title = f"{data['stationName']}: {data['now']['secondLine']['title']}"
        self.artists = data['stationName']
        self.duration = None
        self.release = None
        self.path = data['now']['media']['sources'][0]['url'] if 0 < len(data['now']['media']['sources']) else None

class StationPage(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.STATIONPAGE
        self.title = data['stationName']
        self.path = podcast_url(data['stationName'])

class Grid(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.title = data['metadata']['seo']['title']
        self.model = Model.GRID
        self.subs = data['grid']['steps']

class Program(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data['concept'], index, context)
        self.model = Model.PROGRAM
        if 'expression' in data and data['expression'] is not None:
            self.subs += [data['expression'] | {'model': "Expression"}]

class Tag(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.path = podcast_url(data['path'])
        self.subs = data.get('documents', {'items': []})['items']
        document = data.get('documents', {})
        pagination = document.get('pagination', {'pageNumber': 1})
        self.pages = (pagination['pageNumber'], pagination.get('lastPage', pagination['pageNumber']))

class Search(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.subs = data['items']['concepts']['contents'] + data['items']['expressions_articles']['contents']

class Article(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)

class Other(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.subs = []
        if "items" in data:
            if isinstance(data['items'], dict):
                for k in ['concepts', 'personalities', 'expressions_articles']:
                    if k in data['items']:
                        self.subs += data['items'][k]['contents']
            elif isinstance(data['items'], list):
                self.subs += data['items']
            else:
                self.subs = data['items'] if "items" in data else []

class PageTemplate(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.path = podcast_url(data.get('slug', self.path))
        self.title = data.get('label', self.title)
        if data['model'].upper() == Model.PAGETEMPLATE.name:
            self.subs = [data.get('layout', None)]

class ManifestationAudio(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        if data['model'].upper() == Model.MANIFESTATIONAUDIO.name:
            self.path = podcast_url(data['url'])
            self.duration = int(data['duration'])
            self.release = strftime("%d-%m.%y", localtime(data['created']))

class Concept(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.CONCEPT
        expressions = data.get('expressions', {'pageNumber': 1})
        self.subs = expressions.get('items', data.get('promoEpisode', {'items': []})['items'])
        self.pages = (expressions['pageNumber'], expressions.get('lastPage', expressions['pageNumber']))

class Highlight(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        if data['model'].upper() == Model.HIGHLIGHT.name:
            self.subs = data.get('highlights')
            if self.title is None and len(self.subs) == 1:
                self.title = self.subs[0]['title']

class HighlightElement(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        if data['model'].upper() == Model.HIGHLIGHTELEMENT.name:
            if 0 < len(data['links']):
                url = data['links'][0]['path']
                if data['links'][0]['type'] == "path":
                    local_link = data['context']['station'] if 'context' in data else ""
                    self.path = podcast_url(url, local_link)
                else:
                    self.path = podcast_url(url)
            self.subs = data.get('contents',[])
            self.image = data['mainImage']['src'] if data['mainImage'] is not None else None
            if self.title is None and len(self.subs) == 1:
                self.title = self.subs[0]['title']

class Brand(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        brand = data.get('slug', data.get('brand', "franceinter"))
        url = podcast_url(brand.split("_")[0] + BRAND_EXTENSION + brand)
        data = fetch_data(url)

        self.model = Model.BRAND
        self.station = data['stationName']
        self.now = data['now']['firstLine']['title']
        self.title = f"{self.now} ({self.station})"
        self.artists = data['now']['secondLine']['title']
        self.duration = 0
        try:
            self.release = data['now']['song']['release']['title']
        except:
            self.release = None
        self.genre = data['now']['thirdLine']['title']
        self.image = None
        for key in ['mainImage', 'visual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.image = data[key]['src']
        self.icon = None
        for key in ['squaredVisual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.icon = data[key]['src']
        self.path = data['now']['media']['sources'][0]['url']

class Slug(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.SLUG
        name = data['slug']
        self.path = podcast_url(name)
        self.title = data.get('brand', name)

class Expression(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = Model.EXPRESSION
        self.artists = ", ".join([g['name'] for g in (data['guest'] if "guest" in data else [])])
        self.release = strftime("%d-%m.%y", localtime(data['publishedDate'])) if "publishedDate" in data else ""
        self.duration = 0
        manifestations_audio = list([d for d in data.get('manifestations', []) if d['model'] == "ManifestationAudio"])
        if 0 < len(manifestations_audio):
            manifestation = create_item(self.index, next(filter(lambda d: d['principal'], manifestations_audio), data['manifestations'][0]), self.context)
            self.duration = manifestation.duration
            self.path = podcast_url(manifestation.path)

class Slider(Item):
    def __init__(self, data, index, context = {}):
        super().__init__(data, index, context)
        self.model = model.SLIDER
        self.subs = data.get('items', [])

class Theme(Item):
    pass

class EmbedImage(Item):
    pass

class BrandPage:
    def __init__(self, data, index):
        self.title = data['stationName']
        self.image = None
        for key in ['mainImage', 'visual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.image = data[key]['src']
        self.icon = None
        for key in ['squaredVisual']:
            if key in data and data[key] is not None and "src" in data[key]:
                self.icon = data[key]['src']
        self.path = data['now']['media']['sources'][0]['url']

def expand_json(data):

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

    nodes = json.loads(data)['nodes']
    expanded = {}
    for node in nodes[::-1]:
        if 'data' in node:
            parsed = node['data']
            expanded = expand_element(parsed[0])
            if expanded.get('content', expanded.get('metadata', None)) is not None :
                break
            else:
                print(json.dumps(expanded))

    return expanded

def podcast_url(url, local=""):
    if url is None:
        return None
    return (RADIOFRANCE_PAGE \
            + local \
            + ("/" if 0 < len(url) and url[0] != "/" else "" ) \
            + url) \
            if url[:8] != "https://"  else url

def localize(string_id: int, **kwargs) -> str:
    import xbmcaddon
    ADDON = xbmcaddon.Addon()
    if not isinstance(string_id, int) and not string_id.isdecimal():
        return string_id
    return ADDON.getLocalizedString(string_id)

def build_url(query):
    base_url = sys.argv[0]
    url = base_url + "?" + urlencode(query, quote_via=quote_plus)
    return url

def combine(l):
    while True:
        try:
            yield [next(a) for a in l]
        except StopIteration:
            break

if __name__ == "__main__":
    data = sys.stdin.read()
    data = expand_json(data)
    # print(json.dumps(data))
    # exit(0)

    def repeat(item):
        while True:
            yield item

    def display(item):
        if isinstance(item, Item):
            if len(item.subs) != 0 or (item.path is not None and item.path != ""):
                print(item)
                if len(item.subs) == 1:
                    display(create_item(0, item.subs[0], context))
        else:
            (_, data, e) = item
            print(f"Error : {e} on {json.dumps(data)}")
            raise e

    item = create_item_from_page(data)
    context = data.get('context', {})
    subs = item.subs
    while 1 < len(sys.argv):
        index = int(sys.argv.pop())
        print(f"Using index: {index}")
        sub_item = create_item(0, subs[index], context)
        if not isinstance(sub_item, Item):
            (_, data, e) = sub_item
            print(f"Error : {e} on {json.dumps(data)}")
            raise e
        subs = sub_item.subs

    # print(json.dumps(subs))
    display(item)
    with ThreadPoolExecutor() as p:
        sub_items = list(p.map(create_item, itertools.count(), iter(subs), repeat(context)))
    list(map(display, sub_items))

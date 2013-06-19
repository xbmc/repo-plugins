
import utils
import utils.xbmc

import xbmc
import xbmcgui
import xbmcplugin

from fivehundredpx.client import FiveHundredPXAPI

_CONSUMER_KEY = 'LvUFQHMQgSlaWe3aRQot6Ct5ZC2pdTMyTLS0GMfF'
_RPP = int(xbmcplugin.getSetting(utils.xbmc.addon_handle, 'rpp'))
API = FiveHundredPXAPI()


class Image(object):
    def __init__(self, photo_json):
        self.name= photo_json['name']
        self.thumb_url = photo_json['images'][0]['url']
        self.url = photo_json['images'][1]['url']

    def __repr__(self):
        return str(self.__dict__)


def feature():
    params = utils.xbmc.addon_params
    feature = params['feature']
    category = params.get('category', None)
    page = int(params.get('page', 1))

    resp = API.photos(feature=feature, only=category, rpp=_RPP, consumer_key=_CONSUMER_KEY, image_size=[2, 4], page=page)

    for image in map(Image, resp['photos']):
        utils.xbmc.add_image(image)

    if resp['current_page'] != resp['total_pages']:
        next_page = page + 1
        url = utils.xbmc.encode_child_url('feature', feature=feature, category=category, page=next_page)
        utils.xbmc.add_dir('Next page', url)

    utils.xbmc.end_of_directory()


def search():
    def getTerm():
        kb = xbmc.Keyboard(heading='Search 500px')
        kb.doModal()
        return kb.getText()

    params = utils.xbmc.addon_params

    if 'term' not in params:
        term = getTerm()
        page = 1
    else:
        term = params['term']
        page = int(params['page'])

    resp = API.photos_search(term=term, rpp=_RPP, consumer_key=_CONSUMER_KEY, image_size=[2, 4], page=page)
    for image in map(Image, resp['photos']):
        utils.xbmc.add_image(image)

    if resp['current_page'] != resp['total_pages']:
        next_page = page + 1
        url = utils.xbmc.encode_child_url('search', term=term, page=next_page)
        utils.xbmc.add_dir('Next page', url)

    utils.xbmc.end_of_directory()


def features():
    features = (
        "editors",
        "popular",
        "upcoming",
        "fresh_today",
        "fresh_yesterday"
    )

    for feature in features:
        url = utils.xbmc.encode_child_url('categories', feature=feature)
        utils.xbmc.add_dir(feature, url)

    url = utils.xbmc.encode_child_url('search')
    utils.xbmc.add_dir('Search', url)

    utils.xbmc.end_of_directory()


def categories():
    categories = {
        'Uncategorized': 0,
        'Abstract': 10,
        'Animals': 11,
        'Black and White': 5,
        'Celebrities': 1,
        'City': 9,
        'Commercial': 15,
        'Concert': 16,
        'Family': 20,
        'Fashion': 14,
        'Film': 2,
        'Fine Art': 24,
        'Food': 23,
        'Journalism': 3,
        'Landscapes': 8,
        'Macro': 12,
        'Nature': 18,
        'Nude': 4,
        'People': 7,
        'Performing Arts': 19,
        'Sport': 17,
        'Still Life': 6,
        'Street': 21,
        'Transportation': 26,
        'Travel': 13,
        'Underwater': 22,
        'Urban': 27,
        'Wedding': 25,
    }

    params = utils.xbmc.addon_params
    feature = params['feature']

    url = utils.xbmc.encode_child_url('feature', feature=feature)
    utils.xbmc.add_dir('All', url)

    for category in sorted(categories):
        url = utils.xbmc.encode_child_url('feature', feature=feature, category=category)
        utils.xbmc.add_dir(category, url)

    utils.xbmc.end_of_directory()


try:
    modes = {
        'feature': feature,
        'categories': categories,
        'search': search,
    }

    params = utils.xbmc.addon_params
    mode_name = params['mode']
    modes[mode_name]()
except KeyError:
    features()

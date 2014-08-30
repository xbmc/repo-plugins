#!/usr/bin/python
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# plugin.video.tehnik: 
# By: deltha@gmail.com
#------------------------------------------------------------
# TehniK - 2.0.3
#------------------------------------------------------------

from xbmcswift2 import Plugin, xbmc

STRINGS = {
    'page': 30001,
    'itnc': 30100,
    'mobiles': 30101,
    'photovideo': 30102,
    'tutorials': 30103,
    'companies': 30104,
    'games': 30105,
    'search': 30200,
    'title': 30201
}

YOUTUBE_ITNC = (
{
        'name': 'Acsel Tech',
        'logo': 'acsel.png',
        'user': 'acselTech',
    }, {
        'name': 'Altex Reviews',
        'logo': 'altex.png',
        'user': 'AltexRomania',
    }, {
        'name': 'Domo Retail',
        'logo': 'domo.png',
        'user': 'DomoRetail',
    }, {
        'name': 'Emag',
        'logo': 'emag.png',
        'user': 'wwweMAGro',
    }, {
        'name': 'Cel Ro Tv',
        'logo': 'celtv.png',
        'user': 'celrotv',
    }, {
        'name': 'Go 4 It',
        'logo': 'go4it.png',
        'user': 'go4itro',
    }, {
        'name': 'Magazinele Flanco',
        'logo': 'flanco.png',
        'user': 'MagazineleFlanco',
    }, {
        'name': 'Media DOT Ro',
        'logo': 'mediadot.png',
        'user': 'MediaDOTRO',
    }, {
        'name': 'PC Garage',
        'logo': 'pc-garage-srl1.jpg',
        'user': 'PCGarageRO',
    }, {
        'name': 'Pro Store',
        'logo': 'prostore.png',
        'user': 'PROstoreRomania',
    }, {
        'name': 'Unboxarena',
        'logo': 'unboxarena.png',
        'user': 'Unboxarena',
    }, {
        'name': 'Z@na IT',
        'logo': 'zonait.png',
        'user': 'ArealIT',
    },
)

YOUTUBE_MOBILES = (
{
        'name': 'Arena IT',
        'logo': 'arenait.png',
        'user': 'arenaitnet',
    }, {
        'name': 'Gadget.Ro',
        'logo': 'gadgetro.png',
        'user': 'GadgetRoVideo',
    }, {
        'name': 'Gadget On',
        'logo': 'gadgeton.png',
        'user': 'DaniJurma',
    }, {
        'name': 'Gadget-Talk',
        'logo': 'gadget-talk.png',
        'user': 'GadgetTalkRO',
    }, {
        'name': 'GSMLand',
        'logo': 'gsmland.png',
        'user': 'GSMLandRo',
    }, {
        'name': 'Lab 501',
        'logo': 'lab501.jpg',
        'user': 'lab501ro',
    }, {
        'name': 'Market Online',
        'logo': 'marketonline.png',
        'user': 'MarketOnlineRO',
    }, {
        'name': 'Mobilissimo',
        'logo': 'mobilissimo.png',
        'user': 'mobilissimo',
    }, {
        'name': 'Voievozii',
        'logo': 'voievozii.png',
        'user': 'voievoziitehnici',
    }, {
        'name': 'Telefonul Tau',
        'logo': 'telefonultau.png',
        'user': 'telefonultau',
    }, {
        'name': 'The Phone Geeks',
        'logo': 'thephonegeeks.png',
        'user': 'watchandmatch',
    }, {
        'name': 'Playtech',
        'logo': 'playtech.png',
        'user': 'playtechRo',
    }, 
)

YOUTUBE_PHOTOVIDEO = (
{
        'name': 'F64 Studio',
        'logo': 'f64.png',
        'user': 'f64ro',
  }, {
        'name': 'Fotostart',
        'logo': 'fotostart.png',
        'user': 'FOTOSTART',
  }, {
        'name': 'Nikonisti Romania',
        'logo': 'nikonisti.png',
        'user': 'nikonistii',
    },
)

YOUTUBE_TUTORIALS = (
{
        'name': 'Videotutorial Ro',
        'logo': 'videotutorialro.png',
        'user': 'VideotutorialR0',
    },
)

YOUTUBE_COMPANIES = (
{
        'name': 'Allview Mobile',
        'logo': 'allview.png',
        'user': 'allviewmobile',
    }, {
        'name': 'Asus',
        'logo': 'asus.png',
        'user': 'UCLJ3bI_qlphy9iHNYzGkbzg',
    }, {
        'name': 'Bit Defender',
        'logo': 'bitdefender.png',
        'user': 'BitDefenderWorld',
    }, {
        'name': 'Canon Romania',
        'logo': 'canonromania.png',
        'user': 'CanonRomania',
    }, {
        'name': 'Evolio Romania',
        'logo': 'evolio.png',
        'user': 'EvolioRomania',
    }, {
        'name': 'HP Romania',
        'logo': 'hp.png',
        'user': 'HPRomania',
    }, {
        'name': 'Lenovo Romania',
        'logo': 'lenovo.png',
        'user': 'LenovoRomania',
    }, {
        'name': 'Nokia Romania',
        'logo': 'nokia.png',
        'user': 'NokiaRomania',
    }, {
        'name': 'Panasonic Romania',
        'logo': 'panasonic.png',
        'user': 'PanasonicRomania',
    }, {
        'name': 'PNI Electronics',
        'logo': 'pni.png',
        'user': 'PNIelectronics',
    }, {
        'name': 'Samsung',
        'logo': 'samsung.png',
        'user': 'SamsungTubeRomania',
    }, {
        'name': 'Schrack Technik',
        'logo': 'schrack.png',
        'user': 'SchrackTechnikRO',
    }, {
        'name': 'Sony',
        'logo': 'sony.png',
        'user': 'UC-CnlDAXt6MqB6ozXOSZp4w',
    },
)

YOUTUBE_GAMES = (
{
        'name': 'CreativeMonkeyzArmy',
        'logo': 'creativemonkeyz.png',
        'user': 'CreativeMonkeyzArmy',
    }, {
        'name': 'GamaGanda',
        'logo': 'gamaganda.png',
        'user': 'GamaGanda',
    }, {
        'name': 'Gamextv',
        'logo': 'gamextv.png',
        'user': 'gamextvro',
    }, {
        'name': 'Gaming HD',
        'logo': 'gaminghd.png',
        'user': 'HDGamingHD',
    }, {
        'name': 'PGLtv',
        'logo': 'pgl.png',
        'user': 'PGLeSport',
    }, {
        'name': 'Tiranianu Gaming',
        'logo': 'tira.png',
        'user': 'tiranianu009',
    }, {
        'name': 'War Arena Gaming',
        'logo': 'wararenagaming.png',
        'user': 'wararenagamingro',
    },
)

YOUTUBE_URL = (
    'plugin://plugin.video.youtube/?'
    'path=/root&feed=uploads&channel=%s'
)

plugin = Plugin()

@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('itnc'),
         'path': plugin.url_for('show_itnc')},
        {'label': _('mobiles'),
         'path': plugin.url_for('show_mobiles')},
        {'label': _('photovideo'),
         'path': plugin.url_for('show_photovideo')},
        {'label': _('tutorials'),
         'path': plugin.url_for('show_tutorials')},
        {'label': _('companies'),
         'path': plugin.url_for('show_companies')},
        {'label': _('games'),
         'path': plugin.url_for('show_games')},
    ]
    return plugin.finish(items)

@plugin.route('/itnc/')
def show_itnc():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_ITNC]
    return plugin.finish(items)

@plugin.route('/mobiles/')
def show_mobiles():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_MOBILES]
    return plugin.finish(items)

@plugin.route('/photovideo/')
def show_photovideo():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_PHOTOVIDEO]
    return plugin.finish(items)

@plugin.route('/tutorials/')
def show_tutorials():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_TUTORIALS]
    return plugin.finish(items)

@plugin.route('/companies/')
def show_companies():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_COMPANIES]
    return plugin.finish(items)

@plugin.route('/games/')
def show_games():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_GAMES]
    return plugin.finish(items)

def get_logo(logo):
    addon_id = plugin._addon.getAddonInfo('id')
    return 'special://home/addons/%s/resources/media/%s' % (addon_id, logo)

def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id

def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()

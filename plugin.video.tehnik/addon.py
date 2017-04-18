#!/usr/bin/python
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# plugin.video.tehnik:
# By: deltha@gmail.com
#------------------------------------------------------------
# TehniK - 2.0.7
#------------------------------------------------------------

from xbmcswift2 import Plugin

STRINGS = {
    'page': 30001,
    'itnc': 30100,
    'mobiles': 30101,
    'photovideo': 30102,
    'tutorials': 30103,
    'companies': 30104,
    'telecom': 30105,
    'games': 30106,
    'search': 30200,
    'title': 30201
}

YOUTUBE_ITNC = (
{
        'name': 'Altex Reviews',
        'logo': 'altex.png',
        'channel_id': 'UCeKDPIHminC91rxZpdoqLOA',
        'user': 'AltexRomania',
    }, {
        'name': 'Emag',
        'logo': 'emag.png',
        'channel_id': 'UC2u8VWZlMKdR3yACwEYUOgQ',
        'user': 'wwweMAGro',
    }, {
        'name': 'Magazinele Flanco',
        'logo': 'flanco.png',
        'channel_id': 'UCsYdFv7QHOOy4H0H1bMRT_A',
        'user': 'MagazineleFlanco',
    }, {
        'name': 'Media Galaxy',
        'logo': 'mediagalaxy.png',
        'channel_id': 'UCgXrD6KUtfljFw0dZuPt7VQ',
        'user': 'MediaGalaxy',
    }, {
        'name': 'Media Dot Ro',
        'logo': 'mediadot.png',
        'channel_id': 'UCZDnuO5F4kXmZ3I0ydg3U8w',
        'user': 'MediaDOTRO',
    }, {
        'name': 'PC Garage Video Reviews',
        'logo': 'pcgarage-red.png',
        'channel_id': 'UCO2eTgt3_AlVbK4jFokA-NA',
        'user': 'PCGarageRO',
    }, {
        'name': 'PC Garage TV',
        'logo': 'pc-garage-srl1.jpg',
        'channel_id': 'UCioQHDZMMkcq4703aNrp9UQ',
        'user': 'PCGarageTV',
    }, {
        'name': 'Zona IT',
        'logo': 'zonait.png',
        'channel_id': 'UCCUnAfa_A5XR5NyoPgErmlg',
        'user': 'ArealIT',
    },
)

YOUTUBE_MOBILES = (
{
        'name': 'Arena IT',
        'logo': 'arenait.png',
        'channel_id': 'UCxWoZ5i1puQLZPeURY5DajQ',
        'user': 'arenaitnet',
    }, {
        'name': 'Gadget.Ro',
        'logo': 'gadgetro.png',
        'channel_id': 'UChFVtLbhlxHlIwFwrK7-1gw',
        'user': 'GadgetRoVideo',
    }, {
        'name': 'Gadget-Talk',
        'logo': 'gadget-talk.png',
        'channel_id': 'UCZkBljLHKvZkoo4aKdJuExQ',
        'user': 'GadgetTalkRO',
    }, {
        'name': 'George Buhnici',
        'logo': 'gbuhnici.png',
        'channel_id': 'UCNz5n8PoSGYSwkOH_SMnl2A',
        'user': 'gbuhnici',
    }, {
        'name': 'Go 4 It',
        'logo': 'go4it.png',
        'channel_id': 'UCDyRWzRFgTrCxKB3Dr-y4Mg',
        'user': 'go4itro',
    }, {
        'name': 'GSMLand',
        'logo': 'gsmland.png',
        'channel_id': 'UCCwpDzejpm1hBYjZ91qOHAw',
        'user': 'GSMLandRo',
    }, {
        'name': 'Lab 501',
        'logo': 'lab501.jpg',
        'channel_id': 'UCGW-SJJWuNv4NRnVUuldbYQ',
        'user': 'lab501ro',
    }, {
        'name': 'Market Online',
        'logo': 'marketonline.png',
        'channel_id': 'UCJd5DaTI7FVkg4-aAc-tsbA',
        'user': 'MarketOnlineRO',
    }, {
        'name': 'Mobilissimo',
        'logo': 'mobilissimo.png',
        'channel_id': 'UChYnF1OycKQ-VoAuVpD9jYg',
        'user': 'mobilissimo',
    }, {
        'name': 'Playtech',
        'logo': 'playtech.png',
        'channel_id': 'UC_1cms0pNhUGbJZUjbIzO3A',
        'user': 'playtechRo',
    }, {
        'name': 'Telefonul Tau',
        'logo': 'telefonultau.png',
        'channel_id': 'UCz72pVnmoBVrBnIbM6zhN8g',
        'user': 'telefonultau',
    },
)

YOUTUBE_PHOTOVIDEO = (
{
        'name': 'F64 Studio',
        'logo': 'f64.png',
        'channel_id': 'UC6e3Vbt6mr-rWDkzSK2hCSw',
        'user': 'f64ro',
  }, {
        'name': 'Nikonisti Romania',
        'logo': 'nikonisti.png',
        'channel_id': 'UCL89IijjGc6XtknU8B_23sA',
        'user': 'nikonistii',
    },
)

YOUTUBE_TUTORIALS = (
{
        'name': 'CreativeMonkeyzArmy',
        'logo': 'creativemonkeyz.png',
        'channel_id': 'UCJRnlF9sHMvFkoizKqXVQdA',
        'user': 'CreativeMonkeyzArmy',
    },{
        'name': 'Videotutorial Ro',
        'logo': 'videotutorialro.png',
        'channel_id': 'UC70ZVoa5VqukRti8djz2roQ',
        'user': 'VideotutorialR0',
    },
)

YOUTUBE_COMPANIES = (
    {
        'name': 'Allview Mobile',
        'logo': 'allview.png',
        'channel_id': 'UCOGo7QtmSiHwR3YJ0Dr1auw',
        'user': 'allviewmobile',
    }, {
        'name': 'Asus Romania',
        'logo': 'asus.png',
        'channel_id': 'UCLJ3bI_qlphy9iHNYzGkbzg',
        'user': 'UCLJ3bI_qlphy9iHNYzGkbzg',
    }, {
        'name': 'Bit Defender',
        'logo': 'bitdefender.png',
        'channel_id': 'UCCuVBVczq1ShkwL-BXRU6UA',
        'user': 'BitDefenderWorld',
    }, {
        'name': 'Canon Romania',
        'logo': 'canonromania.png',
        'channel_id': 'UCu7GfIyU1dCFTHrEGnfHsuQ',
        'user': 'CanonRomania',
    }, {
        'name': 'Evolio Romania',
        'logo': 'evolio.png',
        'channel_id': 'UCZyc7nENKlmw5dyj5_-GlRg',
        'user': 'EvolioRomania',
    }, {
        'name': 'HP Romania',
        'logo': 'hp.png',
        'channel_id': 'UCqcEzOKaA4nc0gISklN0Ryw',
        'user': 'HPRomania',
    }, {
        'name': 'Lenovo Romania',
        'logo': 'lenovo.png',
        'channel_id': 'UCRxrekuulBTmjNcrd0K7Jtg',
        'user': 'LenovoRomania',
    }, {
        'name': 'Panasonic Romania',
        'logo': 'panasonic.png',
        'channel_id': 'UCjjAPnk3_X1LGdp_q2eeNJg',
        'user': 'PanasonicRomania',
    }, {
        'name': 'Philips TV Romania',
        'logo': 'philips.png',
        'channel_id': 'UCsfbmzqkTlVqXIRlHFA8kkw',
        'user': 'PhilipsTVRomania',
    }, {
        'name': 'PNI Electronics',
        'logo': 'pni.png',
        'channel_id': 'UCxja_B31Dj3TrhrYw1ymFhA',
        'user': 'PNIelectronics',
    }, {
        'name': 'Samsung',
        'logo': 'samsung.png',
        'channel_id': 'UCG9lzwwhR70vM1JdVQGGfjA',
        'user': 'SamsungTubeRomania',
    }, {
        'name': 'Toshiba Romania',
        'logo': 'toshiba.jpg',
        'channel_id': 'UCKptuTzAzZAr6UN6R26PwWw',
        'user': 'toshibaromania',
    }, {
        'name': 'Sony',
        'logo': 'sony.png',
        'channel_id': 'UCSDWiL-3tzO1yXLYOYU9lyQ',
        'user': 'sonyelectronics',
    },
)

YOUTUBE_TELECOM = (
{
        'name': 'Digi',
        'logo': 'digi.jpg',
        'channel_id': 'UC7NlfYYuSUzY9xhUiOTFF0w',
        'user': 'TheDigiVideo',
    }, {
        'name': 'Orange Romania',
        'logo': 'orange.jpg',
        'channel_id': 'UChfXOsAyyyDFVxhP2hgqP5w',
        'user': 'orangeromania',
    }, {
        'name': 'Telecom Tv',
        'logo': 'telecomtv.jpg',
        'channel_id': 'UC2AJd8MJsEvHQ4ZUTxGHEag',
        'user': 'ivaciu',
    }, {
        'name': 'Telekom Romania',
        'logo': 'telekom.jpg',
        'channel_id': 'UCHVuhHj_RaGp1Mblkj-bs0A',
        'user': 'telekomromania',
    }, {
        'name': 'Vodafone Buzz',
        'logo': 'vodafone.jpg',
        'channel_id': 'UCdQu6AvIaARgtqMtMQ42F1Q',
        'user': 'vodafonebuzz',
    }, {
        'name': 'Upc',
        'logo': 'upc.jpg',
        'channel_id': 'UChjix-wxtZq4HN_mzQYNO_g',
        'user': 'UChjix-wxtZq4HN_mzQYNO_g',
    },
)

YOUTUBE_GAMES = (
    {
        'name': 'GamaGanda',
        'logo': 'gamaganda.png',
        'channel_id': 'UCZpkjwyi1HRvDhYiUey1u_w',
        'user': 'GamaGanda',
    }, {
        'name': 'Gamextv',
        'logo': 'gamextv.png',
        'channel_id': 'UCdY3hmybN3THA--GLU2w1bw',
        'user': 'gamextvro',
    }, {
        'name': 'Gaming HD',
        'logo': 'gaminghd.png',
        'channel_id': 'UCW-thz5HxE-goYq8yPds1Gw',
        'user': 'HDGamingHD',
    }, {
        'name': 'War Arena Gaming',
        'logo': 'wararenagaming.png',
        'channel_id': 'UCMM64ps97PbMrpVsnzE2H9w',
        'user': 'wararenagamingro',
    },
)

YOUTUBE_URL ='plugin://plugin.video.youtube/channel/%s/?page=1'

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
        {'label': _('telecom'),
         'path': plugin.url_for('show_telecom')},
        {'label': _('games'),
         'path': plugin.url_for('show_games')},
    ]
    return plugin.finish(items)

@plugin.route('/itnc/')
def show_itnc():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_ITNC]
    return plugin.finish(items)

@plugin.route('/mobiles/')
def show_mobiles():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_MOBILES]
    return plugin.finish(items)

@plugin.route('/photovideo/')
def show_photovideo():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_PHOTOVIDEO]
    return plugin.finish(items)

@plugin.route('/tutorials/')
def show_tutorials():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_TUTORIALS]
    return plugin.finish(items)

@plugin.route('/companies/')
def show_companies():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_COMPANIES]
    return plugin.finish(items)

@plugin.route('/telecom/')
def show_telecom():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
    } for channel in YOUTUBE_TELECOM]
    return plugin.finish(items)

@plugin.route('/games/')
def show_games():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['channel_id'],
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

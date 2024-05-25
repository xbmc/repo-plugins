# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

import urlquick

from codequick import Listitem, Resolver, Route, Script

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# Replay
URL_REPLAY = 'https://playpuls.pl'
URL_PATH_KIDS = '/pulskids'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def list_programs(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_REPLAY + URL_PATH_KIDS, headers=GENERIC_HEADERS, max_age=-1)
    if resp.status_code != 200:
        return False
    html_programs = resp.parse()
    categories = html_programs.findall('.//div[@id="category-list"]/div/a')
    for cat in categories:
        item = Listitem()
        serial_desc = cat.find('./div/p')
        if serial_desc is None:
            continue
        serial_name = serial_desc.text
        item.label = serial_name
        img = cat.find('./img')
        if img is None:
            continue
        serial_image_url = URL_REPLAY + img.attrib['src']
        item.art['poster'] = serial_image_url
        serial_path = cat.attrib['href']
        item.set_callback(list_episodes, serial_path=serial_path, serial_name=serial_name, serial_image_url=serial_image_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_episodes(plugin, serial_path, serial_name, serial_image_url):
    resp = urlquick.get(URL_REPLAY + serial_path, headers=GENERIC_HEADERS, max_age=-1)
    if resp.status_code != 200:
        return False
    html_serial = resp.parse()

    episodes = html_serial.findall('.//div[@class="tvshow__item"]/a')
    number = 1
    for e in episodes:
        item = Listitem()
        item.label = serial_name + " " + str(number)
        number = number + 1

        img = e.find('./div/img')
        item.art['fanart'] = serial_image_url
        if img is not None:
            item.art['thumb'] = URL_REPLAY + img.attrib['src']

        item.set_callback(play_episode, episode_path=e.attrib['href'])
        item_post_treatment(item)
        yield item


@Resolver.register
def play_episode(plugin, episode_path):
    content = urlquick.get(URL_REPLAY + episode_path, headers=GENERIC_HEADERS, max_age=-1)
    if content.status_code != 200:
        plugin.notify(plugin.localize(30891), plugin.localize(30718), Script.NOTIFY_ERROR)
        return False
    html_serial = content.parse()

    m3u8_source = html_serial.find('.//source[@type="application/x-mpegURL"]')
    if m3u8_source is None:
        plugin.notify(plugin.localize(30891), plugin.localize(30718), Script.NOTIFY_ERROR)
        return False

    return resolver_proxy.get_stream_with_quality(plugin, m3u8_source.attrib['src'])

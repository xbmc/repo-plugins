# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING. If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html

import os
import urllib

from xbmcswift2 import Plugin

from resources.lib import utils
from resources.lib.scrapers.base import BaseScraper


PLUGIN_ID = 'plugin.video.thrasherskateboard'
MEDIA_URL = 'special://home/addons/{0}/resources/media/'.format(PLUGIN_ID)

plugin = Plugin()


@plugin.route('/download/<url>')
def download_video(url):
    """
    Downloads a video to the specified location in settings.  Opens
    addon settings if the setting is not yet configured
    """
    download_folder = plugin.get_setting('download_location')
    if not download_folder:
        plugin.open_settings()
        return

    video_url = utils.get_video_url(url)
    video_title = video_url.split('/')[-1]
    download_location = os.path.join(download_folder, video_title)

    plugin.notify("Downloading to %s" % download_location)
    urllib.urlretrieve(video_url, download_location)
    plugin.notify("Download complete.")


@plugin.route('/play/<url>')
def play_video(url):
    """
    Plays the passed in video
    """
    plugin.log.debug(url)
    vid_url = utils.get_video_url(url)
    plugin.log.debug(vid_url)
    plugin.log.info('Playing url: %s' % vid_url)
    plugin.set_resolved_url(vid_url)


@plugin.route('/category/<category>/<page>')
def show_category(category, page='1'):
    """
    Category page, lists all videos for the provided category
    """
    page = int(page)
    items, has_next = utils.get_items_for_category(category, plugin, page)

    kwargs = {
        'category': category,
    }
    items, has_pagination = utils.add_pagination(items, page, has_next, kwargs,
                                                 plugin,
                                                 route_name='show_category')

    if has_pagination:
        # need to manually call finish so xbmc knows not to store history
        # for the next/previous items.
        return plugin.finish(items, update_listing=True)
    else:
        return items


@plugin.route('/')
def categories():
    """
    The index view, which lists all categories
    """
    categories = (
        # (label, category)
        ('Most Recent', 'most_recent'),
        ('Classics', 'classics'),
        ('Double Rock', 'double_rock'),
        ('Events & Contests', 'events'),
        ('Firing Line', 'firing_line'),
        ('Greatest Hits', 'greatest_hits'),
        ('Hall of Meat', 'hall_of_meat'),
        ('King of the Road', 'king_of_the_road'),
        ('P-Stone Clips', 'p_stone'),
        ('Skateline', 'skateline'),
        ('Skatepark Round-Up', 'skatepark_round_up'),
        ('Skate Rock', 'skate_rock'),
    )
    items = [utils.create_item_for_category(
                name, category, MEDIA_URL, plugin)
             for name, category in categories]
    return items


if __name__ == '__main__':
    try:
        plugin.run()
    except Exception as e:
        msg = "Error: check logs.  %s" % (e.message,)
        plugin.notify(msg=msg, delay=8000)

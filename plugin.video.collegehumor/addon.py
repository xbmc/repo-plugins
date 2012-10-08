from xbmcswift import Plugin
import resources.lib.scraper as scraper

plugin = Plugin('CollegeHumor', 'plugin.video.collegehumor', __file__)


@plugin.route('/', default=True)
def show_categories():
    categories = scraper.getCategories()
    items = [{
        'label': category['title'],
        'url': plugin.url_for(
            'show_videos',
            category=category['link'],
            page='1',
        ),
    } for category in categories]
    return plugin.add_items(items)


@plugin.route('/category/<category>/<page>/')
def show_videos(category, page):
    videos, has_next_page = scraper.getVideos(category, page)
    items = [{
        'label': video['title'],
        'thumbnail': video['image'],
        'info': {
            'originaltitle': video['title'],
            #'tagline': video['tagline']
        },
        'url': plugin.url_for(
            'watch_video',
            url=video['link']
        ),
        'is_folder': False,
        'is_playable': True,
    } for video in videos]
    if has_next_page:
        next_page = str(int(page) + 1)
        items.append({
            'label': '>> %s %s >>' % (
                plugin.get_string(30001),
                next_page
            ),
            'url': plugin.url_for(
                'show_videos',
                category=category,
                page=next_page
            ),
        })
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (
                plugin.get_string(30001),
                prev_page
            ),
            'url': plugin.url_for(
                'show_videos',
                category=category,
                page=prev_page
            ),
        })
    return plugin.add_items(items)


@plugin.route('/watch/<url>/')
def watch_video(url):
    video_url = scraper.getVideoFile(url)
    return plugin.set_resolved_url(video_url)


if __name__ == '__main__':
    plugin.run()

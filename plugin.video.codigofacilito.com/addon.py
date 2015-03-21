from xbmcswift2 import Plugin, xbmc

from resources.lib import cf


plugin = Plugin()

@plugin.route('/')
def courses():
    courses = []
    for course in cf.get_courses():
        title = course['title']
        courses.append({
            'label': title,
            'path': plugin.url_for('course', url=course['url']),
            'thumbnail': course['thumbnail']
            })

    if len(courses) == 0:
        cf.alert(plugin.name, plugin.get_string(cf.T_ERROR_COURSES))
    
    return courses


@plugin.route('/course/<url>')
def course(url):
    videos = []
    for video in cf.get_course(url):
        videos.append({
            'label': video['title'],
            'path': plugin.url_for(
                'video', url=video['url']),
            'is_playable': True})

    if len(videos) == 0:
        cf.alert(plugin.name, plugin.get_string(cf.T_ERROR_VIDEOS))

    return videos


@plugin.route('/video/<url>')
def video(url):
    youtube_id = cf.get_video(url)
    return plugin.set_resolved_url(
        'plugin://plugin.video.youtube?action=play_video&videoid={0}'.format(
            youtube_id))


if __name__ == '__main__':
    plugin.run()

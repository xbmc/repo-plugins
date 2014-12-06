from xbmcswift2 import Plugin

from resources.lib import tnb


plugin = Plugin()


@plugin.route('/')
def categories():
    items = []
    for category in tnb.get_categories():
        title = category['title']
        items.append({
            'label': title,
            'path': plugin.url_for('topics', category=title)})

    return items


@plugin.route('/topics/<category>')
def topics(category):
    items = []
    for topic in tnb.get_topics(category):
        title = topic['title']
        items.append({
            'label': title,
            'path': plugin.url_for('lessons', lesson_id=topic['lesson_id']),
            'thumbnail': topic.get('thumbnail')
        })

    return items


@plugin.route('/lessons/<lesson_id>')
def lessons(lesson_id):
    items = []
    for lesson in tnb.get_lessons(lesson_id):
        items.append({
            'label': lesson['title'],
            'path': plugin.url_for(
                'video', lesson_id=lesson['lesson_id'],
                video_id=lesson['video_id']),
            'is_playable': True})

    return items


@plugin.route('/videos/<lesson_id>/<video_id>')
def video(lesson_id, video_id):
    youtube_id = tnb.get_video(lesson_id, video_id)
    return plugin.set_resolved_url(
        'plugin://plugin.video.youtube?action=play_video&videoid={0}'.format(
            youtube_id))


if __name__ == '__main__':
    plugin.run()

from xbmcswift2 import Plugin, xbmc

import urllib2, json

BASE_URL = 'http://codigofacilito.com'
SERVICE_URL = 'http://www.ezequielescobar.com/servicios/codigofacilito'

T_ERROR_TITLE = 30001
T_ERROR_SERVER = 30002
T_ERROR_COURSES = 30003
T_ERROR_VIDEOS = 30004

def log(message):
    xbmc.log("CODIGOFACILITO: " + str(message))

def alert(title, message):
    xbmc.executebuiltin("Notification(" + title + "," + message + ")")

def get_url(url):
    req = urllib2.Request(url)
    req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0')
    return urllib2.urlopen(req).read()

plugin = Plugin()

@plugin.route('/')
def courses():
    jurl = SERVICE_URL + '/courses.php'
    jsonCourses = json.loads(get_url(jurl));

    if (jsonCourses['status'] == 1 and jsonCourses['count'] > 0):
        courses = []
        for course in jsonCourses['courses']:
            courses.append({
                'label': course['name'],
                'path': plugin.url_for('course', url=course['url']),
                'thumbnail': BASE_URL + course['img']
                })

        return courses
    else:
        alert(plugin.name, plugin.get_string(T_ERROR_COURSES))


@plugin.route('/course/<url>')
def course(url):
    jurl = SERVICE_URL + '/videos.php?url='
    jsonVideos = json.loads(get_url(jurl + url));

    if (jsonVideos['status'] == 1 and jsonVideos['count'] > 0):
        videos = []
        for video in jsonVideos['videos']:
            videos.append({
                'label': video['name'],
                'path': plugin.url_for(
                    'video', url=video['url']),
                'is_playable': True})

        return videos
    else:
        alert(plugin.name, plugin.get_string(T_ERROR_VIDEOS))


@plugin.route('/video/<url>')
def video(url):
    vurl = SERVICE_URL + '/video.php?url='
    youtube_id = get_url(vurl + url);

    return plugin.set_resolved_url(
        'plugin://plugin.video.youtube/play/?video_id={0}'.format(
            youtube_id))


if __name__ == '__main__':
    plugin.run()

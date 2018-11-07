from xbmcswift2 import Plugin, xbmc

import urllib2, ssl
from bs4 import BeautifulSoup

BASE_URL = 'http://codigofacilito.com'

T_ERROR_TITLE = 30001
T_ERROR_SERVER = 30002
T_ERROR_COURSES = 30003
T_ERROR_VIDEOS = 30004
T_ERROR_CATEGORIES = 30005

def log(message):
    xbmc.log("CODIGOFACILITO: " + str(message))

def alert(title, message):
    xbmc.executebuiltin("Notification(" + title + "," + message + ")")

def get_url(url, secure = False):
    req = urllib2.Request(url)
    req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0')
    if (secure):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        return urllib2.urlopen(req, context=context).read()
    else:
        return urllib2.urlopen(req).read()

plugin = Plugin()

@plugin.route('/')
def categories():
    html = get_url(BASE_URL + "/courses")
    soup = BeautifulSoup(html, 'html.parser')
    str(soup)

    topDiv = soup.find("div", { "class" : "top-30 stripped" })
    rowDivs = topDiv.find_all("div", { "class" : "row center-xs " })

    if (len(rowDivs) > 0):
        categories = []
        for rows in rowDivs:
            category = rows.find("h3").text
            categories.append({
                'label': '[COLOR blue]' + category + '[/COLOR]',
                'path': '/'
            })
            cols = rows.find_all("div", { "class" : " col-xs-4" })
            for col in cols:
                link = col.find("h4").find("a")
                category = link.text
                categories.append({
                    'label': category,
                    'path': plugin.url_for('explore', url=link['href'])
                })

        return categories
    else:
        alert(plugin.name, plugin.get_string(T_ERROR_SERVER))

@plugin.route('/explore/<url>')
def explore(url):
    html = get_url(BASE_URL + url)
    soup = BeautifulSoup(html, 'html.parser')
    str(soup)

    categoryRowDivs = soup.find_all("article", { "class" : "col-course" })

    if (len(categoryRowDivs) > 0):
        courses = []

        for crow in categoryRowDivs:
            courseUrl = crow.find("a")['href']
            courseName = crow.find("h2").text
            premium = crow.find("img", { "alt" : "Thunder" })
            if premium is not None:
                courseName += " (PREMIUM)"
                courses.append({
                    'label': '[COLOR red]' + courseName + '[/COLOR]',
                    'path': '/'
                })
            else:
                courses.append({
                    'label': '[COLOR white]' + courseName + '[/COLOR]',
                    'path': plugin.url_for('course', url=courseUrl)
                })

        return courses
    else:
        alert(plugin.name, plugin.get_string(T_ERROR_CATEGORIES))

@plugin.route('/course/<url>')
def course(url):
    html = get_url(BASE_URL + url)
    soup = BeautifulSoup(html, 'html.parser')
    str(soup)

    courseName = soup.find("title").text
    courseLi = soup.find_all("li", { "class" : "border-bottom" })

    if (len(courseLi) > 0):
        videos = []
        videos.append({
                    'label': '[COLOR blue]' + courseName + '[/COLOR]',
                    'path': '/'
                })

        for li in courseLi:
            videoUrl = li.find("a")['href']
            videoName = li.find("div", { "class" : "box" }).text.strip()

            videos.append({
                'label': videoName,
                'path': plugin.url_for(
                    'video', url=videoUrl),
                'is_playable': True})

        return videos
    else:
        alert(plugin.name, plugin.get_string(T_ERROR_COURSES))

@plugin.route('/video/<url>')
def video(url):

    html = get_url(BASE_URL + url)
    soup = BeautifulSoup(html, 'html.parser')
    str(soup)
    videoId = soup.find("input", { "name" : "youtube_video_id" })['value']

    return plugin.set_resolved_url(
        'plugin://plugin.video.youtube/play/?video_id={0}'.format(
            videoId))


if __name__ == '__main__':
    plugin.run()

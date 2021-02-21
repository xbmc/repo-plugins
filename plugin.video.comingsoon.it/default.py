import datetime
import re
from phate89lib import rutils, kodiutils, staticutils

home = "https://www.comingsoon.it"
webutils = rutils.RUtils()
rutils.log = kodiutils.log
webutils.setUserAgent(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0")

# site logic


def getTheatersList(page=1, fullDetails=False):
    return getMoviesList("{home}/cinema/filmalcinema/?page={page}".format(home=home, page=page), fullDetails)


def getNextReleasesList(offsetDays=0, fullDetails=False):
    return getMoviesList("{home}/cinema/calendariouscite/?r={offsetDays}".format(home=home, offsetDays=offsetDays), fullDetails)


def getMoviesList(url, fullDetails=False):
    bpage = webutils.getSoup(url)
    if not bpage:
        return -1, []
    htmlmovies = bpage.find_all(
        True, attrs={"class": "cards cards-horiz-box box-office min film brd-c"})
    if not htmlmovies:
        return -1, []
    movies = []
    for htmlmovie in htmlmovies:
        if (htmlmovie.has_attr('href')):
            res = re.search(".*?\/.*?\/([0-9]+)\/scheda\/", htmlmovie['href'])
        else:
            a = htmlmovie.find('a')
            if a and a.has_attr('href'):
                res = re.search(".*?\/.*?\/([0-9]+)\/scheda\/", a['href'])
        if res:
            if (fullDetails):
                movie = getFullMovieDetails(res.group(1))
            else:
                movie = getBaseMovieDetails(htmlmovie.find('div', attrs={"class": 'testo plr0'}))
            movie['id'] = res.group(1)
            movie['image'] = 'https://mr.comingsoon.it/imgdb/locandine/big/{id}.jpg'.format(
                id=movie['id'])
            movies.append(movie)
    lastPage = -1
    i = bpage.find("i", attrs={"class": "fa fa-forward"})
    if i and len(i.parent['class']) > 0 and not 'disabled' in i.parent['class']:
        lastPage = i.parent['href'].split('=')[-1]
    return lastPage, movies


def getBaseMovieDetails(htmlmovie):
    movie = {}
    if not htmlmovie:
        return movie
    div = htmlmovie.find(True, 'titolo h2')
    if div:
        movie['title'] = div.string.strip()
    div = htmlmovie.find("div", attrs={"class": "descrizione p mbs"})
    if (div):
        movie['originaltitle'] = div.string[1:-1].strip()
    div = htmlmovie.find("div", attrs={"class": "titolo p mbs"})
    if (div):
        movie['originaltitle'] = div.string[1:-1].strip()
    infos = htmlmovie.find_all("div", attrs={"class": "p"})
    if (infos):
        for info in infos:
            if (info.b and info.span):
                if (info.b.string == 'Anno:'):
                    movie['year'] = info.span.string.strip()
                elif (info.b.string == 'Uscita:'):
                    movie['premiered'] = info.span.string.strip()
                elif (info.b.string == 'Genere:'):
                    movie['genre'] = info.span.get_text().strip().split(', ')
                elif (info.b.string == 'NAZIONALITA&#39;'):
                    movie['country'] = info.span.get_text().strip().split(', ')
                elif (info.b.string == 'Regia:'):
                    movie['director'] = info.span.get_text().strip().split(', ')
                elif (info.b.string == 'Cast:'):
                    movie['cast'] = info.span.get_text().strip().split(', ')
    div = htmlmovie.find('div', attrs={"class": "c p"})
    if div:
        movie['studio'] = div.string.strip()
    div = htmlmovie.find('div', attrs={"class": "voto p pbs"})
    if div:
        movie['rating'] = float(div.contents[1].strip().replace(',', '.'))*2

    return movie


def getFullMovieDetails(id):
    page = webutils.getSoup(
        "{home}/film/movie/{id}/scheda/".format(home=home, id=id), parser='html5lib')
    if not page:
        return {}
    frame = page.find("div", attrs={"class": "container pbm"})
    if not frame:
        return {}
    movie = {}
    res = frame.find("h1", attrs={"class": "titolo h1"})
    if res:
        movie['title'] = res.string.strip()
    res = frame.find("div", attrs={"class": "sottotitolo h3"})
    if res:
        movie['originaltitle'] = res.string[1:-1].strip()
    res = frame.find("div", attrs={"id": "_voto-pubblico"})
    if res:
        movie['userrating'] = float(res['data-rating'])*2
        res = res.find_next_sibling("div", attrs={"class": "voto mrl"})
        if res:
            movie['rating'] = float(res['data-rating'])*2
    res = frame.find("div", attrs={"class": "descrizione p"})
    if res:
        movie['plot'] = res.get_text()
    frame = page.find("div", attrs={"class": "container mobile mtl"})
    if not frame:
        return movie
    res = frame.find("div", attrs={"class": 'meta-l mbl'})
    if res:
        infos = res.find_all("div", attrs={"class": 'p'})
        if (infos):
            for info in infos:
                if (info.span):
                    field = info.b.string
                    movie['studio'] = []
                    if (field == 'Anno:'):
                        movie['year'] = info.span.get_text().strip()
                    # if (field == 'Data di uscita:'):
                    #     movie['premiered'] = info.span.get_text()
                    elif (field == 'Genere:'):
                        movie['genre'] = info.span.get_text().strip().split(', ')
                    elif (field == 'Paese:'):
                        movie['country'] = info.span.get_text().strip().split(', ')
                    elif (field == 'Regia:'):
                        movie['director'] = info.span.get_text().strip().split(', ')
                    elif (field == 'Attori:'):
                        movie['cast'] = info.span.get_text().strip().split(', ')
                    elif (field == 'Sceneggiatura:'):
                        movie['writer'] = info.span.get_text().strip().split(', ')
                    elif (field == 'Produzione:'):
                        movie['studio'].extend(info.span.get_text().strip().split(', '))
                    elif (field == 'Distribuzione:'):
                        movie['studio'].extend(info.span.get_text().strip().split(', '))
                    elif (field == 'Durata:'):
                        try:
                            movie['duration'] = int(info.span.string.strip().split(" ")[0])
                        except:
                            pass
    return movie


def extractFromLinks(item):
    res = []
    items = item.find_all('a')
    if items:
        for a in items:
            res.append(a.text)
    return res


def getMovieVideos(id):
    # url http://www.comingsoon.it/film/something/{movieid}/scheda/
    page = webutils.getSoup("http://www.comingsoon.it/film/movie/{id}/video/".format(id=id))
    if not page:
        return []
    videos = []
    # load the main video
    htmlvideos = page.find_all("a", attrs={"class": "cards brd-c mbl"})
    if htmlvideos:
        for htmlvideo in htmlvideos:
            vid = htmlvideo['href'].split('=')[-1]
            div = htmlvideo.find("div", attrs={"class": "titolo h3"})
            if div:
                videos.append({"id": vid,  "title": div.string,
                               "image": "http://mr.comingsoon.it/imgdb/video/{id}_big.jpg".format(id=vid)})
    return videos


def getVideoUrls(id):
    videourls = {}
    content = webutils.getText("http://www.comingsoon.it/VideoPlayer/embed/?ply=1&idv=" + str(id))
    if (content):
        res = re.search('vLwRes\:.*?\"(.*?)\"', content)
        if res:
            videourls['sd'] = "http://video.comingsoon.it/" + res.group(1)
        else:
            res = re.search('vStart\:.*?\"(.*?)\"', content)
            if res:
                videourls['sd'] = "http://video.comingsoon.it/" + res.group(1)
        res = re.search('vHiRes\:.*?\"(.*?)\"', content)
        if res:
            videourls['hd'] = "http://video.comingsoon.it/" + res.group(1)
    return videourls

# addon logic


def loadList():
    kodiutils.addListItem(kodiutils.LANGUAGE(32005), {"mode": "moviesintheaters"})
    kodiutils.addListItem(kodiutils.LANGUAGE(32006), {"mode": "moviescomingsoon"})
    kodiutils.endScript()


def addTheatersList(page=1):
    page = int(page)
    kodiutils.setContent('movies')
    maxPage, movies = getTheatersList(page, kodiutils.getSettingAsBool('fullDetails'))
    addMoviesList(movies)
    if page < int(maxPage):
        kodiutils.addListItem(kodiutils.LANGUAGE(
            32002), {"mode": "moviesintheaters", "page": page + 1})
    kodiutils.endScript()


def addNextReleasesList(offset=0):
    offset = int(offset)
    kodiutils.setContent('movies')
    maxPage, movies = getNextReleasesList(offset, kodiutils.getSettingAsBool('fullDetails'))
    addMoviesList(movies)
    if offset <= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(
            32003), {"mode": "comingweek", "offset": offset - 7})
    if offset >= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(
            32004), {"mode": "comingweek", "offset": offset + 7})
    kodiutils.endScript()


def addMoviesList(movies):
    for movie in movies:
        movie['mediatype'] = 'movie'
        kodiutils.addListItem(movie['title'], {"id": movie['id'], "mode": "videos"}, videoInfo=movie,
                              thumb=movie['image'], poster=movie['image'])


def loadDates(offset=0):
    offset = int(offset)
    d = datetime.date.today() + datetime.timedelta(offset)
    offset_days = 3 - d.weekday()
    nextthursday = d + datetime.timedelta(offset_days)
    for x in range(0, 9):
        kodiutils.addListItem(kodiutils.LANGUAGE(32007) + " " + str(nextthursday +
                                                                    datetime.timedelta(x * 7)), {"offset": offset + (x * 7), "mode": "comingweek"})
    if offset <= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(
            32001), {"mode": "moviescomingsoon", "offset": offset - 63})
    if offset >= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(
            32002), {"mode": "moviescomingsoon", "offset": offset + 63})
    kodiutils.endScript()


def loadVideos(id):
    kodiutils.setContent('videos')
    for video in getMovieVideos(id):
        kodiutils.addListItem(video['title'], {"id": video['id'], "mode": "videourl"}, thumb=video['image'], videoInfo={
                              'mediatype': 'video'}, isFolder=False)
    kodiutils.endScript()


def watchVideo(id):
    urls = getVideoUrls(id)
    if kodiutils.getSettingAsBool('PreferHD') and 'hd' in urls:
        kodiutils.setResolvedUrl(urls['hd'])
    elif ('sd' in urls):
        kodiutils.setResolvedUrl(urls['sd'])
    elif ('hd' in urls):
        kodiutils.setResolvedUrl(urls['sd'])
    kodiutils.log('No links found')
    kodiutils.setResolvedUrl(solved=False)


params = staticutils.getParams()
if not params or 'mode' not in params:
    loadList()
else:
    if params['mode'] == "moviesintheaters":
        addTheatersList(params.get('page', 1))
    elif params['mode'] == "moviescomingsoon":
        loadDates(params.get('offset', 0))
    elif params['mode'] == "comingweek":
        addNextReleasesList(params.get('offset', 0))
    elif params['mode'] == "videos":
        loadVideos(params['id'])
    elif params['mode'] == "videourl":
        watchVideo(params['id'])
    else:
        loadList()

import datetime, re
from phate89lib import rutils, kodiutils, staticutils

home = "http://www.comingsoon.it"
webutils=rutils.RUtils()
rutils.log=kodiutils.log
webutils.USERAGENT = "Comingsoon video addon"

#site logic

def getTheatersList(page = 1, fullDetails = False):
    return getMoviesList("{home}/cinema/filmalcinema/?page={page}".format(home=home,page=page), fullDetails)

def getNextReleasesList(offsetDays = 0, fullDetails = False):
    return getMoviesList("{home}/cinema/calendariouscite/?r={offsetDays}".format(home=home,offsetDays=offsetDays), fullDetails)

def getMoviesList(url, fullDetails = False):
    bpage = webutils.getSoup(url)
    if not bpage:
        return -1, []
    htmlmovies = bpage.find_all("a", attrs={"class": "col-xs-12 cinema"})
    if not htmlmovies:
        return -1, []
    movies = []
    for htmlmovie in htmlmovies:
        if (htmlmovie and htmlmovie.has_attr('href')):
            res = re.search(".*?\/.*?\/([0-9]+)\/scheda\/", htmlmovie['href'])
            if res:
                if (fullDetails):
                    movie = getFullMovieDetails(res.group(1))
                else:
                    movie = getBaseMovieDetails(htmlmovie)
                movie['id'] = res.group(1)
                movie['image']='https://mr.comingsoon.it/imgdb/locandine/big/{id}.jpg'.format(id=movie['id'])
                movies.append( movie )
    lastPage=-1
    i = bpage.find("i", attrs={"class": "fa fa-fast-forward"})
    if i and len(i.parent['class']) > 0 and not 'disattivato' in i.parent['class']:
        lastPage = i.parent['href'].split('=')[-1]
    return lastPage, movies

def getBaseMovieDetails(htmlmovie):
    movie = {}
    div = htmlmovie.find("div", attrs={"class": "h3 titolo cat-hover-color anim25"})
    if (div):
        movie['title'] = div.string
    div = htmlmovie.find("div", attrs={"class": "h5 sottotitolo"})
    if (div):
        movie['originaltitle'] = div.string
    ul = htmlmovie.find("ul", attrs={"class": "col-xs-9 box-descrizione"})
    if (ul):
        infos = ul.find_all('li')
        if (infos):
            for info in infos:
                if (info.span):
                    if (info.span.string == 'ANNO'):
                        movie['year'] = info.contents[1][1:].strip()
                    elif (info.span.string == 'DATA USCITA'):
                        movie['premiered'] = info.contents[1][1:].strip()
                    elif (info.span.string == 'GENERE'):
                        movie['genre'] = info.contents[1][1:].strip().replace(',', '/')
                    elif (info.span.string == 'NAZIONALITA&#39;'):
                        movie['country'] = info.contents[1][1:].strip().replace(',', '/')
                    elif (info.span.string == 'REGIA'):
                        movie['director'] = info.contents[1][1:].strip().replace(',', '/')
                    elif (info.span.string == 'CAST'):
                        movie['cast'] = info.contents[1][1:].strip().split(", ")
    return movie

def getFullMovieDetails(id):
    page = webutils.getSoup("{home}/film/movie/{id}/scheda/".format(home=home, id=id))
    if not page:
        return {}
    frame = page.find("div", attrs={"class": "contenitore-scheda col-xs-12"})
    if not frame:
        return {}
    movie = {}
    res = page.find("h1", attrs={"class": "titolo scheda col-sm-10"})
    if res:
            movie['title'] = res.string
    res = page.find("p", attrs={"class": "box-dati col-xs-12 h4"})
    if res:
            movie['originaltitle'] = res.string
    res = frame.find("div", attrs={"id": "voto-pubblico"})
    if res:
            movie['userrating'] = float(res['data-rating'])*2
    res = frame.find("div", attrs={"class": "voto voto-comingsoon col-xs-12 col-sm-4 h6"})
    if res:
            movie['rating'] = float(res['data-rating'])
    res = frame.find("div", attrs={"class": "voto voto-comingsoon col-xs-12 col-sm-4 h6"})
    if res:
            movie['rating'] = float(res['data-rating'])*2
    res = frame.find("div", attrs={"class": "contenuto-scheda-destra col-xs-8"})
    if res:
            movie['plot'] = res.contents[-4].string
    res = frame.find("div", attrs={"class": "box-descrizione"})
    if res:
        uls = res.find_all('ul')
        if uls:
            for ul in uls:
                infos = ul.find_all('li')
                if (infos):
                    for info in infos:
                        if (info.span):
                            field = info.span.string
                            info.span.extract()
                            movie['studio'] = ''
                            if (field == 'ANNO'):
                                movie['year'] = info.text.strip()[2:]
                            if (field == 'DATA USCITA'):
                                movie['premiered'] = info.time['datetime']
                            elif (field == 'GENERE'):
                                movie['genre'] = info.text.strip()[2:].replace(', ', ' / ')
                            elif (field == 'PAESE'):
                                movie['country'] = info.text.strip()[2:].replace(', ', ' / ')
                            elif (field == 'REGIA'):
                                movie['director'] = info.text.strip()[2:].replace(', ', ' / ')
                            elif (field == 'ATTORI'):
                                movie['cast'] = info.text.strip()[2:].split(", ")
                            elif (field == 'SCENEGGIATURA'):
                                movie['writer'] = info.text.strip()[2:].replace(', ', ' / ')
                            elif (field == 'PRODUZIONE'):
                                movie['studio'] += info.text.strip().rstrip(':')[2:].replace(', ', ' / ') + ' / '
                            elif (field == 'DISTRIBUZIONE'):
                                movie['studio'] += info.text.strip().rstrip(':')[2:].replace(', ', ' / ') + ' / '
                            elif (field == 'DURATA'):
                                try:
                                    movie['duration'] = int(info.text.strip()[2:].split(" ")[0])
                                except:
                                    pass
    return movie

def getMovieVideos(id):
    page = webutils.getSoup("http://www.comingsoon.it/film/movie/{id}/video/".format(id=id)) # url http://www.comingsoon.it/film/something/{movieid}/scheda/
    if not page:
        return []
    videos = []
    #load the main video
    htmlvideo = page.find("link", attrs={"rel": "canonical"})
    if htmlvideo:
        firstvid = htmlvideo['href'].split('=')[-1]
        nome = ""
        div = page.find("div", attrs={"class": "h5 descrizione"})
        if div:
            nome = div.string
        videos.append( { "id": firstvid,  "title": nome, "image": "http://mr.comingsoon.it/imgdb/video/{id}_big.jpg".format(id=firstvid) } )
    #search other videos
    htmlrows = page.find_all("div", attrs={"class": "video-player-xl-articolo video-player-xl-sinistra"})
    if htmlrows:
        for htmlrow in htmlrows:
            htmlvideos = htmlrow.find_all('a')
            if htmlvideos:
                for htmlvideo in htmlvideos:
                    vid = htmlvideo['href'].split('=')[-1]
                    if vid != firstvid:
                        div = htmlvideo.find("div", attrs={"class": "h6 descrizione"})
                        if div:
                            videos.append( { "id": vid,  "title": div.string, "image": "http://mr.comingsoon.it/imgdb/video/{id}_big.jpg".format(id=vid) } )
    return videos

def getVideoUrls(id):
    videourls = {}
    content =  webutils.getText("http://www.comingsoon.it/VideoPlayer/embed/?ply=1&idv=" + str(id))
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

#addon logic

def loadList():
    kodiutils.addListItem(kodiutils.LANGUAGE(32005), {"mode": "moviesintheaters"})
    kodiutils.addListItem(kodiutils.LANGUAGE(32006), {"mode": "moviescomingsoon"})
    kodiutils.endScript()

def addTheatersList(page = 1):
    page = int(page)
    kodiutils.setContent('movies')
    maxPage, movies = getTheatersList(page, kodiutils.getSettingAsBool('fullDetails'))
    addMoviesList(movies)
    if page < maxPage:
        kodiutils.addListItem(kodiutils.LANGUAGE(32002), {"mode": "moviesintheaters", "page": page + 1 })
    kodiutils.endScript()

def addNextReleasesList(offset = 0):
    offset=int(offset)
    kodiutils.setContent('movies')
    maxPage, movies = getNextReleasesList(offset, kodiutils.getSettingAsBool('fullDetails'))
    addMoviesList(movies)
    if offset <= 0:
    	kodiutils.addListItem(kodiutils.LANGUAGE(32003), {"mode": "comingweek", "offset": offset - 7 })
    if offset >= 0:
    	kodiutils.addListItem(kodiutils.LANGUAGE(32004), {"mode": "comingweek", "offset": offset + 7 })
    kodiutils.endScript()

def addMoviesList(movies):
    for movie in movies:
        movie['mediatype']='movie'
        kodiutils.addListItem(movie['title'], {"id": movie['id'], "mode": "videos" }, videoInfo=movie, 
            thumb=movie['image'])

def loadDates(offset = 0):
    offset = int(offset)
    d = datetime.date.today() + datetime.timedelta(offset)
    offset_days = 3 - d.weekday()
    nextthursday = d + datetime.timedelta(offset_days)
    for x in range(0,9):
        kodiutils.addListItem(kodiutils.LANGUAGE(32007) + " " + str(nextthursday + datetime.timedelta(x * 7)), {"offset": offset + (x * 7), "mode": "comingweek" })
    if offset <= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(32001), {"mode": "moviescomingsoon", "offset": offset - 63 })
    if offset >= 0:
        kodiutils.addListItem(kodiutils.LANGUAGE(32002), {"mode": "moviescomingsoon", "offset": offset + 63 })
    kodiutils.endScript()

def loadVideos(id):
    kodiutils.setContent('videos')
    for video in getMovieVideos(id):
        kodiutils.addListItem(video['title'], {"id": video['id'], "mode": "videourl" }, thumb=video['image'], videoInfo={'mediatype': 'video'}, isFolder=False)
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

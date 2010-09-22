# Moviemazer XBMC Addon
# written by Tristan Fischer (sphere)
#
# If you have suggestions or problems: write me.
#
# Mail: sphere@dersphere.de
#
# Special Thanks to the website www.moviemaze.de

# Import standard stuff

import urllib2
import re
import os
import sys
import time


# Import XBMC Stuff

import xbmcplugin
import xbmcgui
import xbmcaddon

# Creating some default variables and objects

mainurl = 'http://www.moviemaze.de'
requestheader = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9'

_id = os.path.basename(os.getcwd())
_cachedir = 'special://profile/addon_data/' + _id + '/cache'

Addon = xbmcaddon.Addon(_id)
Setting = Addon.getSetting
Language = Addon.getLocalizedString
Handle = int(sys.argv[1])

# Functions for getting a list of dicts containing movie headers like ID and title

def getTopTen():
    returnmovies = []
    fullurl = mainurl + '/media/trailer/'
    link = getCachedURL(fullurl, 'mainpage.cache', Setting('cache_movies_list'))
    matchtopten = re.compile('<tr><td valign="top" align="right"><b>([0-9]+)</b></td><td width=100% style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a> <span class="small_grey">\(([^<]+)\)</span></td></tr>').findall(link)
    for rank, movieid, urlend, title, trailerkind in matchtopten:
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend,
                 'rank': rank}
        returnmovies.append(movie)
    return returnmovies


def getRecent():
    returnmovies = []
    fullurl = mainurl + '/media/trailer/'
    link = getCachedURL(fullurl, 'mainpage.cache', Setting('cache_movies_list'))
    matchtrecentupdates = re.compile('<td(?: valign="top" style="text-align:left;"><b style="white-space: nowrap;">([^<]*)</b)?></td><td width=100% style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a> <span class="small_grey">\(([^<]+)\)</span></td></tr>').findall(link)
    for date, movieid, urlend, title, trailerkind in matchtrecentupdates:
        if date != '':
            lastdate = date
        else:
            date = lastdate
        datearray = date.split(' ')
        months_de_short = ['', 'Jan', 'Feb', 'M\xe4z', 'Apr', 'Mai', 'Juni', 'Juli', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
        try: date = datearray[0]+ str(months_de_short.index(datearray[1])).zfill(2) +  '.2010' #fixme: this could be made better, no idea how :)
        except: date = date + ' 2010'
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend,
                 'date': date}
        returnmovies.append(movie)
    return returnmovies


def getCurrent():
    returnmovies = []
    fullurl = mainurl + '/media/trailer/'
    link = getCachedURL(fullurl, 'mainpage.cache', Setting('cache_movies_list'))
    matchtacttrailers = re.compile('<tr><td(?: valign="top"><b>[A-Z0-9]</b)?></td><td style="text-align:left;"><a href="/media/trailer/([0-9]+),(?:[0-9]+?,)?([^",]+?)">([^<]+)</a></td></tr>').findall(link)
    for movieid, urlend, title in matchtacttrailers:
        movie = {'movieid': movieid,
                 'title': title,
                 'urlend': urlend}
        returnmovies.append(movie)
    return returnmovies


# Function to get a dict of detailed movie information like coverURL, plot and genres

def getMovieInfo(movieid, urlend='movie.html'):
    returnmovie = {'movieid': movieid,
                   'title': '',
                   'otitle': '',
                   'coverurl': '',
                   'plot': '',
                   'genres': '',
                   'date': ''}
    fullurl = mainurl + '/media/trailer/' + movieid + ',15,' + urlend
    cachefile = 'id' + movieid + '.cache'
    link = getCachedURL(fullurl, cachefile, Setting('cache_movie_info'))
    titlematch = re.compile('<h1>(.+?)</h1>.*<h2>\((.+?)\)</h2>', re.DOTALL).findall(link)
    for title, otitle in titlematch:
        returnmovie.update({'title': title, 'otitle': otitle})
    covermatch = re.compile('src="([^"]+?)" width="150"').findall(link)
    for coverurl in covermatch:
        returnmovie.update({'coverurl': mainurl+coverurl})
    plotmatch = re.compile('WERDEN! -->(.+?)</span>').findall(link)
    for plot in plotmatch:
        plot = re.sub('<[^<]*?/?>','' , plot)
        returnmovie.update({'plot': plot})
    releasedatematch = re.compile('Dt. Start:</b> ([0-9]+.+?)<img').findall(link)
    for releasedateugly in releasedatematch:
        datearray = releasedateugly.split(' ')
        months_de_long = ['', 'Januar', 'Februar', 'M\xe4rz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
        date = datearray[0]+ str(months_de_long.index(datearray[1])).zfill(2) + '.' + datearray[2]
        returnmovie.update({'date': date}) #fixme: date is not shown...
    genresmatch = re.compile('<b style="font-weight:bold;">Genre:</b> (.+?)<br />', re.DOTALL).findall(link)
    for allgenres in genresmatch:
        returnmovie.update({'genres': allgenres})
    return returnmovie


# Function to get a list of dicts which contains trailer- URL, resolution, releasedate

def GetMovieTrailers(movieid, urlend='movie.html'):
    returntrailers = []
    fullurl = mainurl + '/media/trailer/' + movieid + ',15,' + urlend
    cachefile = 'id' + movieid + '.cache'
    link = getCachedURL(fullurl, cachefile, Setting('cache_movie_info'))
    matchtrailerblock = re.compile('<table border=0 cellpadding=0 cellspacing=0 align=center width=100%><tr><td class="standard">.+?<b style="font-weight:bold;">(.+?)</b><br />\(([0-9:]+) Minuten\)(.+?</tr></table></td></tr></table><br /></td></tr></table><br />)', re.DOTALL).findall(link)
    for trailername, duration, trailerblock in matchtrailerblock:
        matchlanguageblock = re.compile('alt="Sprache: (..)">(.+?)>([^<]+)</td></tr></table></td>', re.DOTALL).findall(trailerblock)
        for language, languageblock, date in matchlanguageblock:
            datearray = date.split(' ')
            months_de_short = ['', 'Jan', 'Feb', 'M\xe4rz', 'Apr', 'Mai', 'Juni', 'Juli', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
            try: date = datearray[0]+ str(months_de_short.index(datearray[1])).zfill(2) +  '.2010' #fixme: this could be made better, no idea how :)
            except: date = '' #fixme: unknown -> trans
            matchtrailer = re.compile('>([0-9]+ x [0-9]+)<.+?generateDownloadLink\("([^"]+)"\)').findall(languageblock)
            for resolution, trailerurl in matchtrailer:
                trailer = {'trailername': trailername,
                           'language': language,
                           'resolution': resolution,
                           'date': date,
                           'trailerurl': mainurl+trailerurl}
                returntrailers.append(trailer)
    return returntrailers


# Functions to show things on a xbmc screen

def showCategories():
    addDir(Language(30003),3,'') #Current
    addDir(Language(30001),1,'') #TopTen
    addDir(Language(30002),2,'') #Recent
    return True


def showTopTen():
    toptenmovies = getTopTen()
    showMovies(toptenmovies)
    return True

def showRecent():
    recentmovies = getRecent()
    showMovies(recentmovies)
    return True

def showCurrent():
    currentmovies = getCurrent()
    showMovies(currentmovies)
    return True

def showMovies(movies):
    counter = 0    
    ProgressDialog = xbmcgui.DialogProgress()
    ProgressDialog.create(Language(30020), str(len(movies)) + ' ' + Language(30021))
    ProgressDialog.update(0)
    for movie in movies:
        movieinfo = getMovieInfo(movieid = movie['movieid'], urlend = movie['urlend'])
        addMovie(title = movieinfo['title'],
                 movieid = movieinfo['movieid'],
                 coverurl = movieinfo['coverurl'],
                 plot = movieinfo['plot'],
                 otitle = movieinfo['otitle'],
                 genres = movieinfo['genres'],
                 releasedate = movieinfo['date'])
        counter += 1
        ProgressDialog.update(100 * counter / len(movies),
                              str(len(movies)) + ' ' + Language(30021), # xx movies have to be cached
                              Language(30022) + ': ' + movieinfo['title'].decode('utf-8', 'ignore')) # Loading : yy
        if ProgressDialog.iscanceled(): break
    ProgressDialog.close()


def addDir(dirname, mode, iconimage):
    u = sys.argv[0]+'?mode='+str(mode)
    liz = xbmcgui.ListItem(dirname,
                           iconImage = 'DefaultVideo.png',
                           thumbnailImage = iconimage)
    liz.setInfo(type = 'Video',
                infoLabels = {'Title': dirname})
    ok = xbmcplugin.addDirectoryItem(handle = Handle,
                                     url = u,
                                     listitem = liz,
                                     isFolder = True)


def addMovie(title, movieid, coverurl='', plot='', otitle='', genres='', releasedate='', rating=''):
    u = sys.argv[0] + '?mode=' + str(mode) + '&movieid=' + movieid
    liz = xbmcgui.ListItem(title,
                           iconImage = 'DefaultVideo.png',
                           thumbnailImage = coverurl)
    liz.setInfo(type = 'Video',
                infoLabels = {'Title': title,
                             'Premiered': releasedate, #fixme: why this doesn't work?
                             'Tagline': Language(30030) + ': ' + releasedate,
                             'Date' : releasedate, #fixme: why this doesn't work?
                             'Plot': plot,
                             'Studio': otitle, #fixme: there is no label for "original title"
                             'Genre': genres})
    if rating != '':
        liz.setInfo(type = 'Video', infoLabels = {'Rating': rating})
    ok = xbmcplugin.addDirectoryItem(handle = Handle,
                                     url = u,
                                     listitem = liz,
                                     isFolder = False)


# Function to show an XBMC Dialog.select and ask to choose a trailer

def askTrailers(movieid):
    movietrailers = GetMovieTrailers(movieid)
    movieinfo = getMovieInfo(movieid)
    backlabel = '--> ' + Language(30011) + ' <--' #Back, there is no 'cancel' in Dialog.select :(
    trailercaptionlist = [backlabel]
    trailerurllist = ['']
    for trailer in movietrailers:
        trailercaption = trailer['trailername'] + ' - ' + trailer['language'] + ' - ' + trailer['resolution'] + ' (' + trailer['date'] + ')'
        trailercaptionlist.append(trailercaption)
        trailerurllist.append(trailer['trailerurl'])
    Dialog = xbmcgui.Dialog()
    if len(trailercaptionlist) > 1:
        chosentrailer = Dialog.select(Language(30010), trailercaptionlist) #Choose a Trailer
        if chosentrailer != 0:
            playTrailer(trailerurl = trailerurllist[chosentrailer],
                        title = movieinfo['title'],
                        studio = trailercaptionlist[chosentrailer],
                        coverurl = movieinfo['coverurl'])
    else:
        ok = Dialog.ok(movieinfo['title'], Language(30012)) #No Trailer found :(
    return False


# Function to play a Trailer

def playTrailer(trailerurl, title='', studio='', coverurl=''):
    liz = xbmcgui.ListItem(label = title,
                           iconImage = 'DefaultVideo.png',
                           thumbnailImage = coverurl)
    liz.setInfo(type = 'Video',
                infoLabels = {'Title': title, 'Studio': studio})
    xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play(trailerurl, liz)
    return False


# Helper Functions

def getCachedURL(url, filename, timetolive=1):
    cachefilefullpath = _cachedir + '/' + filename
    timetolive = int(timetolive) * 60 * 60  # timetolive settings are in hours!
    if (not os.path.isdir(_cachedir)):
        os.makedirs(_cachedir)
    try: cachefiledate = os.path.getmtime(cachefilefullpath)
    except: cachefiledate = 0
    if (time.time() - (timetolive)) > cachefiledate:
        req = urllib2.Request(url)
        req.add_header('User-Agent', requestheader)
        sock = urllib2.urlopen(req)
        link = sock.read()
        encoding = sock.headers['Content-type'].split('charset=')[1]
        outfile = open(cachefilefullpath,'w')
        outfile.write(link)
        outfile.close()
    else:
        sock = open(cachefilefullpath,'r')
        link = sock.read()
    sock.close()
    return link


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?','')
        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

# Addon Standard Stuff - here the addon starts

params = get_params()

try:
    movieid = params['movieid']
except:
    movieid = ''

try:
    mode = int(params['mode'])
except:
    mode = None


if movieid != '':
    isdir = askTrailers(movieid)

elif mode == 1:
    isdir = showTopTen()

elif mode == 2:
    isdir = showRecent()
    
elif mode == 3:
    isdir = showCurrent()

else:
    isdir = showCategories()


if isdir:
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(Handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(Handle)

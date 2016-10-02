"""
Parser of Kodi (XBMC) addon to manage deejay.it's Reloaded shows.

This is the parser module that takes care of reading Radio Deejay's website,
extracting the necessary information and return it to the main module.
"""
import re
import urllib2
from BeautifulSoup import BeautifulSoup
import datetime
#import xbmc

NOW = datetime.datetime.now()
ANNO = NOW.year
MESE = NOW.month
GIORNO = NOW.day


def month_to_num(date):
    """
    Translate the month name (string) to its corresponding number.
    Strings are written only in Italian since this module is used to parse
    Radio Deejay's website (www.deejay.it).
    Input
        The month name, epxressed in Italian, e.g. Dicembre
    Output
        The corresponding month number, e.g. 12
    """
    return{
    'Gennaio' : 1,
    'gennaio' : 1,
    'Febbraio' : 2,
    'febbraio' : 2,
    'Marzo' : 3,
    'marzo' : 3,
    'Aprile' : 4,
    'aprile' : 4,
    'Maggio' : 5,
    'maggio' : 5,
    'Giugno' : 6,
    'giugno' : 6,
    'Luglio' : 7,
    'luglio' : 7,
    'Agosto' : 8,
    'agosto' : 8,
    'Settembre' : 9,
    'settembre' : 9,
    'Ottobre' : 10,
    'ottobre' : 10,
    'Novembre' : 11,
    'novembre' : 11,
    'Dicembre' : 12,
    'dicembre' : 12
    }[date]


def translate_date(ep_title):
    """
    Translate the date in the episode's title and return it in the format used
    by Kodi.
    Input
        ep_title is the episode's title, such as Puntata del 3 Gennaio 2014.
        But it could also be Puntata del 3 Gennaio
    Output
        translated_date formatted as dd.mm.YYYY
    Fallback, in case the title is not understood, is 19.12.1982. This should
    be the first day on which a DJ, Gerry Scotty in this case, was speaking.
    """
    #ep_title is, normally, Puntata del 3 Gennaio 2014
    hit = re.findall(r"(Puntata*)*([0-9]{1,2}) (\S*)\s*([0-9]{4})*",
        ep_title,
        re.MULTILINE)
    if hit:
        mese = month_to_num(hit[0][2])
        giorno = hit[0][1]
        if hit[0][3]:
            anno = hit[0][3]
        else:
            anno = ANNO
        data_ep = str(anno)+str(mese).rjust(2, '0')+giorno.rjust(2, '0')
        #Sometimes the year is not given, this part checks whether the returned
        #date is in the future and eventually adjusts it.
        #This works under the hypotesis that the website never returns a date
        #in the future
        today = str(ANNO)+str(MESE).rjust(2, '0')+str(GIORNO).rjust(2, '0')
        if data_ep > today:
            data_ep = str(int(data_ep[0:4])-1) + data_ep[4:]
        translated_date = data_ep[6:8]+'.'+data_ep[4:6]+'.'+data_ep[0:4]
    else:
        #19 dicembre 1982: primo intervento del Gerry Scotti speaker
        translated_date = '19.12.1982'
    return translated_date

def get_img(soup):
    player = soup.find('div', {'id': 'playerCont'})
    if not player:
#            xbmc.log('fanArt: div id playerCont not found', 1)
        img = None
    else:
        hit = re.findall("image=(.*.jpg)",
            player.iframe['src'])
        if not hit:
#                xbmc.log('fanArt: regex does not match', 1)
            img = None
        else:
            img = hit[0]
#                xbmc.log('fanArt:'+img, 1)
    return img


def get_reloaded_list_in_page(url, reloaded_list):
    """
    Return all the available reloaded shows from a single webpage.
    The list is appended to an array of tuples carrying:
    (Program name,
        Thumbnail URL,
        Last episode,
        Date)
    Input
        url of the webpage, e.g.:
        http://www.deejay.it/schede-reloaded/page/2/?section=radio
        reloaded_list, an array of tuples carrying the list of shows returned
        by another parsing operation
    Output
        The above-mentioned array of tuples.
    Single element example:
    ('Deejay chiama Italia',
        http://www.deejay.it/wp-content/uploads/2013/05/DJCI-150x150.jpg',
        'http://www.deejay.it/audio/20141212-4/412626/',
        '19.12.1982')
    """

    soup = BeautifulSoup(urllib2.urlopen(url))
    prog_list = soup.find('ul', {'class': 'block-grid four-up mobile-two-up'}).findAll('li')
    for prog in prog_list:
        # This is needed for issue #14, sometimes the show is has got no
        # picture. In this case we fall back to DeeJay grayscale logo.
        if prog.img:
            url_immagine = prog.img['src']
        else:
            url_immagine = 'http://www.deejay.it/wp-content/themes/deejay/images/logo.png'

        reloaded_list.append(
            (prog.a['title'].encode('utf-8').strip(),
                url_immagine,
                prog.a['href'],
                translate_date(prog.hgroup.span.string))
            )
    nextpage = soup.find('a', {'class': 'nextpostslink'})
    if not nextpage:
        nextpageurl = ''
    else:
        nextpageurl = nextpage['href']

    return reloaded_list, nextpageurl


def get_reloaded_list():
    """
    Crawl over all the pages to return the complete list of reloaded shows.
    Include shows that are not available any more from the web interface, such
    as Dee Giallo.
    This returns an array of tuples containing the following info for all the
    reloaded shows:
    (Program name,
        Thumbnail URL,
        Last episode,
        Date)
    Input:
        None
    Output
        The above-mentioned array
    E.g.:
    ('Deejay chiama Italia',
        'http://www.deejay.it/wp-content/uploads/2013/05/DJCI-150x150.jpg',
        'http://www.deejay.it/audio/20141212-4/412626/',
        '12.12.2014')
    """
    url = "http://www.deejay.it/reloaded/radio/"
    #hardcoded url
    lista, nextpageurl = get_reloaded_list_in_page(url, [])
    while nextpageurl:
        lista, nextpageurl = get_reloaded_list_in_page(nextpageurl, lista)
    # Appending Dee Giallo
    # Dee Giallo is now (27 Sep 2015) back in the list returned by the website.
    # lista.append(
    #     ('Dee Giallo',
    #         'http://www.deejay.it/wp-content/themes/deejay/images/logo.png',
    #         'http://www.deejay.it/audio/20130526-4/269989/',
    #         '26.05.2013'
    #         )
    #     )
    return lista


def get_podcast_list():
    """
    Retrieve the list of podcast from the website
    This returns an array of tuples containing the following info for all the
    shows with podcasts:
        (titolo,
            pic,
            indirizzo,
            dataAstrale,
            podcast [array of tuples (titolo, indirizzo)]
    Input:
        None
    Output
        The above-mentioned array
    E.g.:
    (TBD)
    """
    url = "http://www.deejay.it/podcast/radio/"
    #hardcoded url
    soup = BeautifulSoup(urllib2.urlopen(url))
    podcast_section = soup.find('div', {'class': 'article-list'})
    if podcast_section:
        lista = []
        article_list = podcast_section.findAll('article')
        for show in article_list:
            podcast = []
            episodi = show.findAll('li')
            for episodio in episodi:
                podcast.append(
                    (episodio.find('a')['title'],   #titolo
                        episodio.find('a')['href']) #indirizzo
                    )
            lista.append(
                (show.find('a')['title'],   #titolo
                show.find('img')['src'],    #pic
                show.find('a')['href'],     #indirizzo
                translate_date(show.find('span', {'class': 'hour'}).text),
                podcast)                    #array di podcast
            )
        return lista
    else:
        return None


def get_episodi_reloaded(url, oldimg):
    """
    Return all the available episodes of the selected reloaed show. A single
    webpage is parsed.
    Input
        url is the site's page that lists all the available episodes. E.g.:
        i) http://www.deejay.it/audio/20141215-10/412901/ or
        ii) http://www.deejay.it/audio/page/13/?reloaded=dee-giallo
        oldimg is a string carrying the path of the picture to be used as
        fanArt. This must be extracted from type i) pages and passed when
        parsing type ii) pages from which you can't retrieve such info.
    Output
    lista_episodi an array of tuples carrying the episode's details:
    (link to the webpage where you play the episode to be used by get_epfile(),
        Date,
        Episode's title)
    nextpageurl is the URL of the next page listing the older episodes of the
    show, if any.
    img, that is the fanArt URL to be used for every episode of the Reloaded.
    """
    soup = BeautifulSoup(urllib2.urlopen(url))
    #If the fanArt URL is already know there is no need to re-extract it since
    #it is a show-wise property and not episode-specific.
    if oldimg is not None:
        img = oldimg[0]
    else:
        img = get_img(soup)

    new_url = soup.find('span', {'class': 'small-title'})
    # This is as the user pressed on Archivio+
    if new_url:
        soup = soup = BeautifulSoup(urllib2.urlopen(new_url.a['href']))
    lista_episodi = []
    episodi = soup.find('ul', {'class': 'lista'}).findAll('li')

    if episodi:
        for episodio in episodi:
            lista_episodi.append(
                (
                    episodio.a['href'],
                    translate_date(episodio.a['title']),
                    episodio.a['title'])
                )

    #Passo finale: aggiungi il link alla pagina successiva
    nextpage = soup.find('a', {'class': 'nextpostslink'})
    if not nextpage:
        nextpageurl = ''
    else:
        nextpageurl = nextpage['href']
    return lista_episodi, nextpageurl, img


def get_episodi_podcast(url, oldimg):
    """
    Return all the available episodes of the selected podcast show. A single
    webpage is parsed.
    Input
        url is the site's page that lists all the available episodes. E.g.:
        i) http://www.deejay.it/audio/20141215-10/412901/ or
        ii) http://www.deejay.it/audio/?podcast=ciao-belli
        oldimg is a string carrying the path of the picture to be used as
        fanArt. This must be extracted from type i) pages and passed when
        parsing type ii) pages from which you can't retrieve such info.
    Output
    lista_episodi an array of tuples carrying the episode's details:
    (link to the webpage where you play the episode to be used by get_epfile(),
        Date,
        Episode's title)
    nextpageurl is the URL of the next page listing the older episodes of the
    show, if any.
    img, that is the fanArt URL to be used for every episode of the Reloaded.
    """
    soup = BeautifulSoup(urllib2.urlopen(url))
    #If the fanArt URL is already know there is no need to re-extract it since
    #it is a show-wise property and not episode-specific.
    if oldimg is not None:
        img = oldimg[0]
    else:
        img = get_img(soup)

    new_url = soup.find('span', {'class': 'small-title'})
    # This is as the user pressed on Archivio+
    if new_url:
        soup = soup = BeautifulSoup(urllib2.urlopen(new_url.a['href']))
    lista_episodi = []
    episodi = soup.find('ul', {'class': 'lista podcast-archive'}).findAll('li')
    if episodi:
        data_ep = '19.12.1982'
        # The date is defined only for the first podcast episode of the day; we
        # have to store it across loop iterations. If nothing is found then
        # 19.12.1982 is returned.
        for episodio in episodi:
            tmp = episodio.find('span', {'class': 'small-title red'})
            if tmp is not None:
                data_ep = translate_date(tmp.text)
            lista_episodi.append(
                (
                    episodio.a['href'],
                    data_ep,
                    episodio.a['title'])
                )

    #Passo finale: aggiungi il link alla pagina successiva
    nextpage = soup.find('a', {'class': 'nextpostslink'})
    if not nextpage:
        nextpageurl = ''
    else:
        nextpageurl = nextpage['href']
    return lista_episodi, nextpageurl, img


def get_epfile(url):
    """
    Return the file (mp3) URL to be read from the website to play the selected
    reloaded episode.
    Input
        the webpage URL of the episode to be played.
        E.g.: http://www.deejay.it/audio/20130526-4/269989/
    Output
        the URL of the mp3 (rarely a wma) file to be played to listen to the
        selected episode. E.g.:
        http://flv.kataweb.it/deejay/audio/dee_giallo/deegiallolosmemoratodicollegno.mp3
        Returns an empty string if the file cannot be found.
    """
    soup = BeautifulSoup(urllib2.urlopen(url))
    fileurl = soup.find('div', {'id': 'playerCont'})

    if not fileurl:
        return ''
    else:
        hit = re.findall("file=(.*.mp3)&",
            fileurl.iframe['src'])
        if not hit:
            return ''
        else:
            return hit[0]


#    ---------------------------------------------------
# PROGRAMMI = get_reloaded_list()
# for p in PROGRAMMI:
#    print p

#p = PROGRAMMI[17][2]
#print p

#eps = get_episodi('http://www.deejay.it/audio/page/13/?reloaded=dee-giallo','')
#eps = get_episodi('http://www.deejay.it/audio/20141215-10/412901/')
#eps = get_episodi_reloaded('http://www.deejay.it/audio/poesie-10/418750/', None)
#eps = get_episodi('http://www.deejay.it/audio/20141223-2/414155/', 'pippo')
# for e in eps:
#    print e

#fileurl = get_epfile('http://www.deejay.it/audio/20130527-3/269977/')
#print fileurl

#dataAstrale = translate_date('15 Dicembre')
#print dataAstrale

# LISTA = get_podcast_list()
# prog = LISTA[15]

# DCI = get_episodi_podcast('http://www.deejay.it/audio/?podcast=deejay-chiama-italia', None)
# for ep in DCI:
#     print ep

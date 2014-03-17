import re
import urllib2


def get_reloaded_list():
    url = "http://www.deejay.it/reloaded/radio/"
    page = urllib2.urlopen(url).read()
    response = []

    #trova la lista programmi
    prog_list = re.findall('^.*<a\shref="(http://www\.deejay\.it/audio/.*)".*title="(.+)".*<span>.*$',
                           page,
                           re.MULTILINE)

    #Tupla: (nome show , icona , url ultimo episodio)
    for prog in prog_list:
        #per ogni programma aggiungi l'icona
        response.append((prog[1],
                         re.search('^\s*<img\ssrc="(http://www\.deejay\.it/wp-content/uploads/.+)".*\salt="' + prog[1],
                                   page,
                                   re.MULTILINE).group(1),
                         prog[0]))

    return response


def get_episodi(url):
    page = urllib2.urlopen(url).read()
    new_url = re.findall('^.*a\shref="(http.+audio\?.+)".*title.*rchivio.*$',
                         page,
                         re.MULTILINE)
    if new_url:
        url = new_url[0]
        page = urllib2.urlopen(url).read()

    #programma: TUPLA contente titolo e URL, dall'URL devi caricare ogni pagina per trovare l'indirizzo del file audio
    #<a title="Puntata del 10 Dicembre 2012" href="http://www.deejay.it/audio/20121210-3/271333/"></a>
    episodi = re.findall('^\s*<a\shref="(.*/audio.*)"\s+title="(.*)".*$',
                         page,
                         re.MULTILINE)

    show_reloaded = re.findall('http://www.deejay.it/audio[/page/\d]*\?reloaded=(.*)',
                               url)[0]

    #print 'reloaded: '+show_reloaded
    #print page
    #Passo finale: aggiungi il link alla pagina successiva
    #<a href='http://www.deejay.it/audio/page/2/?reloaded=dee-giallo' class='nextpostslink'></a>

    nextpage = re.findall(
        '<a href=\'(http://www.deejay.it/audio/page/\d+/\?reloaded=' + show_reloaded + ')\' class=\'nextpostslink\'>',
        page,
        re.MULTILINE)
    if nextpage:
        nextpage = nextpage[0]
    else:
        nextpage = ''

    #    print 'nextpage: '+nextpage

    return episodi, nextpage


def get_epfile(url):
    page = urllib2.urlopen(url).read()
    fileurl = re.findall('^.*(http.*\.mp3)\s*</p>.*$',
                         page,
                         re.MULTILINE)
    return fileurl[0]


programmi = get_reloaded_list()

#   ---------------------------------------------------
#for p in programmi:
#    print p

#p = programmi[17][2]
#print p
#eps = get_episodi(p)

#eps = get_episodi('http://www.deejay.it/audio/page/14/?reloaded=dee-giallo')
#print eps[0][0]

#fileurl = get_epfile('http://www.deejay.it/audio/20130527-3/269977/')
#print fileurl

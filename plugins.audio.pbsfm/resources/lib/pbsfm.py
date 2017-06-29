import urllib2
import json


def get_audio():
    url = "http://www.rrr.org.au/programs/archive/"
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    url = soup.findAll(['program_archives'] and ['a'])
    urls = url[24:37]
    title = soup.findAll(['program_archives'] and ['p'])
    titles = title[4:37]
    
    output = []
    output_title = []
    for t in titles:
        output.append(t.text)
    for o in output:
        if not re.search('\d+', o):
            if not re.search('&', o):
                output_title.append(o)

    output_url = []
    for u in urls:
        if 'High' in u:
            output_url.append(u)

    output_final = []
    for i in range(len(output_url)):
        try:
            url_list = output_url[i]['href']
            title_list = output_title[i]
            output_final.append({'url': url_list, 'title': title_list})
        except IndexError:
            pass
    
    return output_final

    

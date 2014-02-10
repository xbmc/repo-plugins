import requests
from BeautifulSoup import BeautifulSoup
import re

ABC_URL= "http://abc.net.au/radionational"

def get_podcasts(url_id):
    """
    returns playable podcasts links from ABC website
    """
    url = ABC_URL + url_id
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    urls = soup.findAll('a', 'ico-download')
    titles = soup.findAll('h3', 'title')

    title_out = []
    for title in titles:
        title_out.append(re.sub('&#039;', "'", title.text))

    output = []
    for i in range(len(title_out)):
		url = urls[i]['href']
		title = title_out[i]
		output.append({'url': url, 'title': title})
   
    return output


def podcasts_get(url):
    """
    returns playable podcasts depending on arg
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    urls = soup.findAll('a', 'ico-download')
    titles = soup.findAll('h3', 'title')
    
    titles_out = []
    for title in titles:
        titles_out.append(re.sub('&#039;', "'", title.text))

    output = []
    for i in range(len(titles_out)):
        try:
            url = urls[i]['href']
            title = titles_out[i]
            output.append({'url': url, 'title': title})
        except IndexError:
            pass

    return output


def get_programs(url_id):
    """
    returns program info from ABC website
    """
    url = ABC_URL + url_id
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    urls = soup.findAll(href=re.compile("/radionational/programs/"))
    programs = []
    for i in range(len(urls)):
        path = urls[i]['href']
        path_final = "http://www.abc.net.au" + path
        title = re.sub('&#039;', "'", urls[i].text)
        programs.append({'url': path_final, 'title': title})
        program_final = programs[40:131]
    
    return program_final


def get_subjects(url_id):
    """
    returns subject info from ABC website
    """
    url = ABC_URL + url_id
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    urls = soup.findAll(href=re.compile("/radionational/subjects/"))
    programs = []

    for i in range(len(urls)):
        path = urls[i]['href']
        path_final = "http://www.abc.net.au" + path
        title = re.sub('&#039;', "'", urls[i].text)
        programs.append({'url': path_final, 'title': title})
        sorted_programs = sorted(programs, key=lambda item: item['title'])
        programs_final = programs[10:30]
    
    return programs_final


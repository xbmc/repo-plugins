import requests
from BeautifulSoup import BeautifulSoup
import re

ABC_URL= "http://abc.net.au/radionational/rntv"

def get_podcasts():
    """
    returns videos from radionational - RNTV website
    """
    url = ABC_URL
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    
    urls = soup.findAll('a' , 'external')
    titles = soup.findAll('h3', 'title')
    thumbs = soup.findAll('img')
    infos = soup.findAll('p')
    
    info_out = []
    for info in infos:
        if len(info.text) > 50:
            info_out.append(info.text)
    
    
    thumb_sec = thumbs[1:37]
    thumb_out = []
    for thumb in thumb_sec:
        thumb_out.append(thumb['src'])


    title_out = []
    for title in titles:
        title_out.append(re.sub('&#039;', "'",title.text))
    

    path = []
    for u in urls:
        if 'youtube' in str(u):
            path.append(u['href'])

    path_out = []
    for i in path:
        path_out.append(i[-11:])
   
    
    output = []
    for x in range(len(title_out)):
        items = {
            'title': title_out[x],
            'thumb': thumb_out[x],
            'url': path_out[x],
            'description': info_out[x],
        } 
        output.append(items)

    return output


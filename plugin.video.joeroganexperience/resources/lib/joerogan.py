import urllib
import urllib2
import re
import os
import traceback
from BeautifulSoup import BeautifulSoup
import resources.lib.utils as utils

def pull_video_list(page_no):
    """
    Gets the list of thumbnails, video URLs and titles from the video site and display the list

    @param string url - Main URL of uStream page (without page number)
    @param int page_no - Page number to get

    @returns dictionary
    """     
    
    # Get the page number and add it to the URL (to allow moving through the video pages)
    url = "http://blog.joerogan.net" + "/page/" + str(page_no)

    videos = []

    # Create a new soup instance and assign a video list html to a variable
    soup = BeautifulSoup(utils.getHtml(url))

    # Get all the divs with the podcast content
    result = soup.find('tr', id='bodyrow').find('td', id='middle').findAll('div', id=re.compile('post-\d+'))

    # For each div
    for r in result:
        
        video = {}
        
        # Get the title
        video['title'] = r.find('div', 'post-headline').h2.a.string

        try:
            
            # Get the main divs
            div = r.find('div', 'post-bodycopy clearfix')
            
        except:
            
            print traceback.format_exc()
            
        else:
            
            try:
            
                # Get the video URL
                video['url'] = div.center.a['href']
            
            except:
            
                try:
            
                    video['url'] = r.find('div', 'post-bodycopy clearfix').center.iframe['src']
            
                except:
            
                    continue
            
            try:
            
                # Get the thumbnail
                video['thumb'] = div.center.img['src']
            
            except:
            
                video['thumb'] = ''
        
        if re.search(r'vimeo', video['url']):
            
            video['src'] = 'vimeo'
            
            # Extract clip ID from the URL, method varying depending on whether it's player.vimeo.com or vimeo.com/id
            if re.search(r'player.vimeo.com/video', video['url']):
            
                url_section = video['url'].split('/')
                clip_id = url_section[4]
                clip_id = clip_id.split('?')[0]
            
            else:
            
                url_section =  video['url'].split('/')
                clip_id = url_section[3]
            
            video['id'] = clip_id
        
        elif re.search(r'ustream', video['url']):
        
            # get src and id if video is ustream
            video['src'] = 'ustream'
            video['id'] = video['url'].replace('http://www.ustream.tv/recorded/', '')
        
        else:
        
            continue
        
        # output details of scraped video to log
        utils.log('Video found: %s' % video['title'])
        utils.log('URL: %s' % video['url'])
        utils.log('Source: %s' % video['src'])
        utils.log('VideoID: %s' % video['id'])
        utils.log('Thumb: %s' % video['thumb'])
        
        # add video to videolist
        videos.append(video)

    return videos

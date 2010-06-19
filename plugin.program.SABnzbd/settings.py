import xbmcplugin
import sys
__settings__ = sys.modules[ "__main__" ].__settings__

#Not used anymore - Enter your username and password in the plugin options
#username_newzbin = ''
#password_newzbin = ''

category_list = ['default','Unknown', 'Anime', 'Apps', 'Books', 'Consoles', 'Emulation', 'Games',
        'Misc', 'Movies', 'Music', 'PDA', 'Resources', 'TV']

'''
dictionary containing the names and RSS feeds for the initial page, feel free to add your own.
The '#' character is a comment in python, delete it to use commented out feeds
'''
#if you use newzbin, add custom rss feeds here
newzbin_rss = [
{'name':'Newzbin - Search', 'url':'http://www.newzbin.com/search/query/?q=%s&area=-1&fpn=p&searchaction=Go&areadone=-1&feed=rss'},
{'name':'Newzbin - TV (Latest)', 'url':'http://www.newzbin.com/browse/category/p/tv/?feed=rss'}, 
{'name':'Newzbin - Movies (Latest)', 'url':'http://www.newzbin.com/browse/category/p/movies/?feed=rss'},
{'name':'Newzbin - Music (Latest)', 'url':'http://www.newzbin.com/browse/category/p/music/?feed=rss'},
#{'name':'Newzbin - Games (Latest)', 'url':'http://www.newzbin.com/browse/category/p/games/?feed=rss'},
#{'name':'Newzbin - Consoles (Latest)', 'url':'http://www.newzbin.com/browse/category/p/consoles/?feed=rss'},
]

binsearch_rss = [{'name':'Binsearch - TV (Latest)', 'url':'http://rss.binsearch.net/rss.php?max=50&g=alt.binaries.multimedia', 'category':'tv'},
{'name':'Binsearch - Movies Divx (Latest)', 'url':'http://rss.binsearch.net/rss.php?max=50&g=alt.binaries.movies.divx', 'category':'movies'},]

nzbs_rss = [
{'name':'NZBs.org - TV (Latest)', 'url':'http://nzbs.org/rss.php?type=1&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'tv'},
{'name':'NZBs.org - Movies (x264)', 'url':'http://nzbs.org/rss.php?catid=4&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'movies'},
{'name':'NZBs.org - Movies (XVID)', 'url':'http://nzbs.org/rss.php?catid=2&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'movies'},
{'name':'NZBs.org - Music', 'url':'http://nzbs.org/rss.php?catid=5&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'music'},
{'name':'NZBs.org - Music Videos', 'url':'http://nzbs.org/rss.php?catid=10&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'musicvideos'},
{'name':'NZBs.org - Movies Search', 'url':'http://nzbs.org/rss.php?q=%s&type=2&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'movies'},
{'name':'NZBs.org - Movies Search', 'url':'http://nzbs.org/rss.php?q=%s&type=1&num=50&dl=1&i=' + __settings__.getSetting('nzbs_id') + '&h=' + __settings__.getSetting('nzbs_hash'), 'category':'tv'},
]

'''nzbsrus_rss = [
{'name':'NZBSRUS (Latest)', 'url':'http://www.nzbsrus.com/rssfeed.php'},
]'''

nzbindex_rss = [
{'name':'NZBIndex - Search', 'url':'http://www.nzbindex.nl/rss/?searchitem=%s&x=0&y=0&age=30&group=&min_size=&max_size=&poster='},
]

""" ADD CUSTOM RSS FEEDS HERE """
#add other rss feeds here, just copy an existing one and change the name and url
other_rss = [
{'name':'NZBmatrix - TV (HD)', 'url':'http://services.nzbmatrix.com/rss.php?subcat=41', 'category':'tv'},
{'name':'NZBmatrix - TV (All)', 'url':'http://services.nzbmatrix.com/rss.php?cat=TV', 'category':'tv'},
{'name':'NZBmatrix - Movies (HD-x264)', 'url':'http://services.nzbmatrix.com/rss.php?subcat=42', 'category':'movies'},
{'name':'NZBmatrix - Movies (HD-BRrip)', 'url':'http://services.nzbmatrix.com/rss.php?subcat=54', 'category':'movies'},
{'name':'NZBmatrix - Movies (HD-XVID)', 'url':'http://services.nzbmatrix.com/rss.php?subcat=2', 'category':'movies'},
{'name':'NZBmatrix - Music (Latest)', 'url':'http://services.nzbmatrix.com/rss.php?cat=Music', 'category':'music'},
]

sabnzbd_rss = [
{'name':'SABnzbd - Queue', 'url':''}, #leave the url blank for this one
]

#ignore below
rss_dict = []
if __settings__.getSetting( "newzbin_show" ) == "true":
    rss_dict.extend(newzbin_rss)
if __settings__.getSetting( "binsearch_show" ) == "true":
    rss_dict.extend(binsearch_rss)
if __settings__.getSetting( "nzbs_show" ) == "true":
    rss_dict.extend(nzbs_rss)
'''if __settings__.getSetting( "nzbsrus_show" ) == "true":
    rss_dict.extend(nzbsrus_rss)'''
if __settings__.getSetting( "nzbindex_show" ) == "true":
    rss_dict.extend(nzbindex_rss)
if __settings__.getSetting( "custom_show" ) == "true":
    rss_dict.extend(other_rss)
rss_dict.extend(sabnzbd_rss)


#!/usr/bin/python

import pprint
from libhr3channel import *
from libhr3http import *
from libhr3show import *
from libhr3hessenschau import *
from libhr3utils import *

if __name__ == "__main__":
    context = ChannelContext(None)
    
    pprint.pprint(context)

    index = 0
    id = getShowId(context, index)
    print('Show Id: ' + id)
    
    loader = ChannelLoader()
    loader.loadEpisodeList(context, index)
    print("==============================================")

    pprint.pprint(context)
    print("==============================================")

    index = 0;

    if len(context['episodes']) > 0:
        url = context['episodes'][index]['link']
        if not id == 'live':
            loader.loadEpisode(url)
        else:
            url = loader.getLiveUrl(context['episodes'][0]['link'])
            print url

    
    

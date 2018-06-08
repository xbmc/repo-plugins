#!/usr/bin/python

import pprint
from libplayer.channel import *
from libplayer.http import *
from libplayer.magazine import *
from libplayer.hessenschau import *
from libplayer.utils import *

maxrange = 4

if __name__ == "__main__":
    context = ChannelContext(None)
    context['debug'] = True
    pprint.pprint(context)
    errorStack = list()

    for index in range(0, maxrange):
        id = getShowId(context, index)
        print('')
        print('***********************************************')
        print('Show Id: ' + id)
        
        loader = ChannelLoader()
        loader.loadEpisodeList(context, index)
        print("==============================================")
    
        pprint.pprint(context['episodes'])
        print("==============================================")
    
        index = 0;
    
        if len(context['episodes']) > 0:
            url = context['episodes'][index]['link']
            if not id == 'live':
                url = getVideoLink(url)
                print url
            else:
                url = loader.resolveLiveUrl(context, context['episodes'][0]['link'])
                print url
        else:
            errorStack.append(id + ' No episodes found')
    
    

import sys

def create_context_menu(getLS, url = None, favorites_action = None, talkID = None):
    context_menu = []
    context_menu += [(getLS(30097), 'Action(queue)')]
    if url != None:
        context_menu += [(getLS(30096), 'RunPlugin(%s?downloadVideo=%s)' % (sys.argv[0], url))]
    if favorites_action == "add":
        context_menu += [(getLS(30090), 'RunPlugin(%s?addToFavorites=%s)' % (sys.argv[0], talkID))]
    elif favorites_action == "remove":
        context_menu += [(getLS(30093), 'RunPlugin(%s?removeFromFavorites=%s)' % (sys.argv[0], talkID))]
    return context_menu

# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib, urlparse
import json
import threading
import re
from Queue import Queue

import os,sys

from default import addon, addon_path, itemsPerPage, urlMain, subredditsFile, int_CommentTreshold
from default import pluginhandle, WINDOW, forceViewMode, viewMode, comments_viewMode, album_viewMode, autoplayAll, autoplayUnwatched, TitleAddtlInfo, DoNotResolveLinks
from utils import xbmc_busy, log, translation, addDir, addDirR
from reddit import reddit_request

default_frontpage    = addon.getSetting("default_frontpage")
no_index_page        = addon.getSetting("no_index_page") == "true"
main_gui_skin        = addon.getSetting("main_gui_skin")

cxm_show_comment_link     = addon.getSetting("cxm_show_comment_link") == "true"
cxm_show_comments         = addon.getSetting("cxm_show_comments") == "true"
cxm_show_go_to            = addon.getSetting("cxm_show_go_to") == "true"
cxm_show_new_from         = addon.getSetting("cxm_show_new_from") == "true"
cxm_show_add_shortcuts    = addon.getSetting("cxm_show_add_shortcuts") == "true"
cxm_show_filter_subreddit = addon.getSetting("cxm_show_filter_subreddit") == "true"
cxm_show_filter_domain    = addon.getSetting("cxm_show_filter_domain") == "true"
cxm_show_open_browser     = addon.getSetting("cxm_show_open_browser") == "true"
cxm_show_reddit_save      = addon.getSetting("cxm_show_reddit_save") == "true"
cxm_show_youtube_items    = addon.getSetting("cxm_show_youtube_items") == "true"

def index(url,name,type_):
    from utils import xstr, samealphabetic, hassamealphabetic
    from reddit import load_subredditsFile, parse_subreddit_entry, create_default_subreddits, assemble_reddit_filter_string, ret_sub_info, ret_settings_type_default_icon


    if not os.path.exists(subredditsFile):  #if not os.path.exists(subredditsFile):
        create_default_subreddits()

    subredditsFile_entries=load_subredditsFile()

    subredditsFile_entries.sort(key=lambda y: y.lower())

    addtl_subr_info={}

    xbmcplugin.setContent(pluginhandle, "mixed") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos

    next_mode='listSubReddit'

    for subreddit_entry in subredditsFile_entries:

        addtl_subr_info=ret_sub_info(subreddit_entry)

        entry_type, subreddit, alias, shortcut_description=parse_subreddit_entry(subreddit_entry)

        icon=default_icon='' #addon_path+"/resources/skins/Default/media/"+ret_settings_type_default_icon(entry_type)

        url= assemble_reddit_filter_string("",subreddit, "yes")

        if subreddit.lower() in ["all","popular"]:
            addDir(subreddit, url, next_mode, icon, subreddit, { "plot": translation(30009) } )  #Displays the currently most popular content from all of reddit
        else:
            if addtl_subr_info: #if we have additional info about this subreddit

                title=xstr(addtl_subr_info.get('title'))+'\n'
                display_name=xstr(addtl_subr_info.get('display_name'))
                if samealphabetic( title, display_name): title=''


                header_title=xstr(addtl_subr_info.get('header_title'))
                public_description=xstr( addtl_subr_info.get('public_description'))

                if samealphabetic( header_title, public_description): public_description=''
                if samealphabetic(title,public_description): public_description=''


                if entry_type=='subreddit':
                    display_name='r/'+display_name
                shortcut_description='[COLOR cadetblue][B]%s[/B][/COLOR]\n%s[I]%s[/I]\n%s' %(display_name,title,header_title,public_description )

                icon=addtl_subr_info.get('icon_img')
                banner=addtl_subr_info.get('banner_img')
                header=addtl_subr_info.get('header_img')  #usually the small icon on upper left side on subreddit screen

                icon=next((item for item in [icon,banner,header] if item ), '') or default_icon

                addDirR(alias, url, next_mode, icon,
                        type_=subreddit,
                        listitem_infolabel={ "plot": shortcut_description },
                        file_entry=subreddit_entry,
                        banner_image=banner )
            else:
                addDirR(alias, url, next_mode, icon, subreddit, { "plot": shortcut_description }, subreddit_entry )

    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSubreddit', "", "", { "plot": translation(30006) } ) #"Customize this list with your favorite subreddit."
    addDir("[B]- "+translation(30005)+"[/B]", "",'searchReddits', "", "", { "plot": translation(30010) } ) #"Search reddit for a particular post or topic

    xbmcplugin.endOfDirectory(pluginhandle)

GCXM_hasmultiplesubreddit=False
GCXM_hasmultipledomain=False
GCXM_hasmultipleauthor=False
GCXM_subreddit_key=''

def listSubReddit(url, name, subreddit_key):
    from guis import progressBG
    from utils import post_is_filtered_out, set_query_field
    from reddit import has_multiple
    global GCXM_hasmultiplesubreddit,GCXM_hasmultipledomain,GCXM_hasmultipleauthor,GCXM_subreddit_key
    log("listSubReddit subreddit=%s url=%s" %(subreddit_key,url) )

    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "movies") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos

    loading_indicator=progressBG('Loading...')
    loading_indicator.update(8,'Retrieving '+subreddit_key)

    content = reddit_request(url)
    loading_indicator.update(11,subreddit_key  )

    if not content:
        loading_indicator.end() #it is important to close xbmcgui.DialogProgressBG
        return

    page_title="[COLOR cadetblue]%s[/COLOR]" %subreddit_key

    xbmcplugin.setPluginCategory(pluginhandle, page_title)

    info_label={ "plot": translation(30013) }  #Automatically play videos
    if autoplayAll:       addDir("[B]- "+translation(30016)+"[/B]", url, 'autoPlay', "", "ALL", info_label)
    if autoplayUnwatched: addDir("[B]- "+translation(30017)+"[/B]" , url, 'autoPlay', "", "UNWATCHED", info_label)

    threads = []
    q_liz = Queue()   #output queue (listitem)

    content = json.loads(content)

    posts_count=len(content['data']['children'])
    filtered_out_posts=0

    GCXM_hasmultiplesubreddit=has_multiple('subreddit', content['data']['children'])
    GCXM_hasmultipledomain=has_multiple('domain', content['data']['children'])
    GCXM_hasmultipleauthor=has_multiple('author', content['data']['children'])
    GCXM_subreddit_key=subreddit_key
    for idx, entry in enumerate(content['data']['children']):
        try:
            if post_is_filtered_out( entry.get('data') ):
                filtered_out_posts+=1
                continue

            t = threading.Thread(target=reddit_post_worker, args=(idx, entry,q_liz), name='#t%.2d'%idx)
            threads.append(t)
            t.start()

        except Exception as e:
            log(" EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )

    break_counter=0 #to avoid infinite loop
    expected_listitems=(posts_count-filtered_out_posts)
    if expected_listitems>0:
        loading_indicator.set_tick_total(expected_listitems)
        last_queue_size=0
        while q_liz.qsize() < expected_listitems:
            if break_counter>=100:
                break

            if last_queue_size < q_liz.qsize():
                items_added=q_liz.qsize()-last_queue_size
                loading_indicator.tick(items_added)
            else:
                break_counter+=1

            last_queue_size=q_liz.qsize()
            xbmc.sleep(50)

    for idx, t in enumerate(threads):

        t.join(timeout=20)

    xbmc_busy(False)

    if q_liz.qsize() != expected_listitems:
        log('some threads did not return a listitem')

    li=[ liz for idx,liz in sorted(q_liz.queue) ]  #list of (url, listitem[, isFolder]) as a tuple

    with q_liz.mutex:
        q_liz.queue.clear()

    xbmcplugin.addDirectoryItems(pluginhandle, li)

    loading_indicator.end() #it is important to close xbmcgui.DialogProgressBG

    try:

        after=content['data']['after']

        o = urlparse.urlparse(currentUrl)
        current_url_query = urlparse.parse_qs(o.query)

        nextUrl=set_query_field(currentUrl, field='after', value=after, replace=True)  #(url, field, value, replace=False):


        count=current_url_query.get('count')

        if current_url_query.get('count')==None:

            count=itemsPerPage
        else:

            try: count=int(current_url_query.get('count')[0]) + int(itemsPerPage)
            except ValueError: count=itemsPerPage

        nextUrl=set_query_field(nextUrl,'count', count, True)

        info_label={ "plot": translation(30004) + '[CR]' + page_title}
        addDir(translation(30004), nextUrl, 'listSubReddit', "", subreddit_key,info_label)   #Next Page
    except Exception as e:
        log('    Exception: '+ str(e))

    subreddit_key=subreddit_key.replace(' ','+')
    viewID=WINDOW.getProperty( "viewid-"+subreddit_key )


    if viewID:
        log("  custom viewid %s for %s " %(viewID,subreddit_key) )
        xbmc.executebuiltin('Container.SetViewMode(%s)' %viewID )
    else:
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

    xbmcplugin.endOfDirectory(handle=pluginhandle,
                              succeeded=True,
                              updateListing=False,   #setting this to True causes the ".." entry to quit the plugin
                              cacheToDisc=True)

def reddit_post_worker(idx, entry, q_out):
    import datetime
    from utils import strip_emoji, pretty_datediff, clean_str
    from reddit import determine_if_video_media_from_reddit_json, ret_sub_icon

    show_listVideos_debug=True
    credate = ""
    is_a_video=False
    title_line2=""
    t_on = translation(30071)  #"on"

    t_pts='c'
    thumb_w=0; thumb_h=0

    try:

        kind=entry.get('kind')  #t1 for comments  t3 for posts
        data=entry.get('data')
        post_id=data.get('name')
        if data:
            if kind=='t3':
                title = clean_str(data,['title'])
                description=clean_str(data,['media','oembed','description'])
                post_selftext=clean_str(data,['selftext'])

                description=post_selftext+'[CR]'+description if post_selftext else description
            else:
                title=clean_str(data,['link_title'])
                description=clean_str(data,['body'])

            title = strip_emoji(title) #an emoji in the title was causing a KeyError  u'\ud83c'

            commentsUrl = urlMain+clean_str(data,['permalink'])


            try:
                aaa = data.get('created_utc')
                credate = datetime.datetime.utcfromtimestamp( aaa )
                now_utc = datetime.datetime.utcnow()
                pretty_date=pretty_datediff(now_utc, credate)
                credate = str(credate)
            except (AttributeError,TypeError,ValueError):
                credate = ""

            subreddit=clean_str(data,['subreddit'])
            author=clean_str(data,['author'])
            domain=clean_str(data,['domain'])

            num_comments = data.get('num_comments',0)

            d_url=clean_str(data,['url'])
            link_url=clean_str(data,['link_url'])
            media_oembed_url=clean_str(data,['media','oembed','url'])

            media_url=next((item for item in [d_url,link_url,media_oembed_url] if item ), '')


            thumb=clean_str(data,['thumbnail'])


            if not thumb.startswith('http'): #in ['nsfw','default','self']:  #reddit has a "default" thumbnail (alien holding camera with "?")
                thumb=""

            if thumb=="":
                thumb=clean_str(data,['media','oembed','thumbnail_url']).replace('&amp;','&')

            if thumb=="":  #use this subreddit's icon if thumb still empty
                try: thumb=ret_sub_icon(subreddit)
                except: pass

            try:

                preview=data.get('preview')['images'][0]['source']['url'].encode('utf-8').replace('&amp;','&')

                try:
                    thumb_h = float( data.get('preview')['images'][0]['source']['height'] )
                    thumb_w = float( data.get('preview')['images'][0]['source']['width'] )
                except (AttributeError,TypeError,ValueError):
                    thumb_w=0; thumb_h=0

            except Exception as e:

                thumb_w=0; thumb_h=0; preview="" #a blank preview image will be replaced with poster_url from make_addon_url_from() for domains that support it

            is_a_video = determine_if_video_media_from_reddit_json(data)

            over_18=data.get('over_18')

            title_line2=""


            title_line2 = "[I][COLOR dimgrey]%s %s [COLOR cadetblue]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(pretty_date,t_on, subreddit,num_comments, t_pts)

            if show_listVideos_debug : log("  POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))


            tuple_for_addDirectoryItems=addLink(title=title,
                    title_line2=title_line2,
                    iconimage=thumb,
                    previewimage=preview,
                    preview_w=thumb_w,
                    preview_h=thumb_h,
                    domain=domain,
                    description=description,
                    credate=credate,
                    reddit_says_is_video=is_a_video,
                    commentsUrl=commentsUrl,
                    subreddit=subreddit,
                    media_url=media_url,
                    over_18=over_18,
                    posted_by=author,
                    num_comments=num_comments,
                    post_index=idx,
                    post_id=post_id
                    )

            q_out.put( [idx, tuple_for_addDirectoryItems] )
    except Exception as e:
        log( '  #reddit_post_worker EXCEPTION:' + repr(sys.exc_info()) +'--'+ str(e) )

def addLink(title, title_line2, iconimage, previewimage,preview_w,preview_h,domain,description, credate, reddit_says_is_video, commentsUrl, subreddit, media_url, over_18, posted_by="", num_comments=0,post_index=1,post_id=''):
    from domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type

    post_title=title
    il_description=""
    n=""  #will hold red nsfw asterisk string
    isFolder=True
    thumb_url=''

    h="[B]" + domain + "[/B]: "
    if over_18:
        mpaa="R"
        n = "[COLOR red]*[/COLOR] "

        il_description = "[COLOR red][NSFW][/COLOR] "+ h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
    else:
        mpaa=""
        n=""
        il_description = h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

    if TitleAddtlInfo:     #put the additional info on the description if setting set to single line titles

        post_title=n+title+"[CR][LIGHT]"+title_line2+'[/LIGHT]'
    else:
        post_title=n+title
        il_description=title_line2+"[CR]"+il_description

    il={"title": post_title, "plot": il_description, "plotoutline": il_description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": domain, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

    liz=xbmcgui.ListItem(label=post_title)

    liz.setInfo(type='video', infoLabels=il)

    if iconimage in ["","nsfw", "default"]:

        iconimage=thumb_url

    preview_ar=0.0
    if (preview_w==0 or preview_h==0) != True:
        preview_ar=float(preview_w) / preview_h


    if previewimage: needs_preview=False
    else:            needs_preview=True  #reddit has no thumbnail for this link. please get one


    if DoNotResolveLinks:
        ld=None
        DirectoryItem_url=sys.argv[0]\
            +"?url="+ urllib.quote_plus(media_url) \
            +"&name="+urllib.quote_plus(title) \
            +"&mode=play"
        setProperty_IsPlayable='true'
        isFolder=False
        title_prefix=''
    else:
        ld=parse_reddit_link(media_url,reddit_says_is_video, needs_preview, False, preview_ar  )

        if needs_preview and ld:
            queried_preview_image= next((i for i in [ld.poster,ld.thumb] if i ), '')
            previewimage=queried_preview_image
            iconimage=ld.thumb

        arg_name=title
        arg_type=previewimage


        DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld,
                                                                                                                        media_url,
                                                                                                                        arg_name,
                                                                                                                        arg_type,
                                                                                                                        script_to_call="",
                                                                                                                        on_autoplay=False,
                                                                                                                        img_w=preview_w,
                                                                                                                        img_h=preview_h)
    if title_prefix:
        liz.setLabel( title_prefix+' '+post_title )

    liz.setProperty('IsPlayable', setProperty_IsPlayable)
    liz.setInfo('video', {"title": liz.getLabel(), } )

    liz.setArt({"thumb": iconimage, "poster":previewimage, "banner":iconimage, "fanart":previewimage, "landscape":previewimage, })
    entries = build_context_menu_entries(num_comments, commentsUrl, subreddit, domain, media_url, post_id) #entries for listbox for when you type 'c' or rt-click

    liz.addContextMenuItems(entries)


    return (DirectoryItem_url,liz,isFolder)  #tuple for addDirectoryItems

def build_context_menu_entries(num_comments,commentsUrl, subreddit, domain, link_url, post_id):
    from reddit import assemble_reddit_filter_string, subreddit_in_favorites, this_is_a_user_saved_list
    from utils import colored_subreddit

    s=(subreddit[:12] + '..') if len(subreddit) > 12 else subreddit     #crop long subreddit names in context menu
    colored_subreddit_short=colored_subreddit( s )
    colored_subreddit_full=colored_subreddit( subreddit )
    colored_domain_full=colored_subreddit( domain, 'tan',False )
    entries=[]


    if cxm_show_open_browser:
            entries.append( ( translation(30509),  #Open in browser
                              "XBMC.RunPlugin(%s?mode=openBrowser&url=%s)" % ( sys.argv[0],  urllib.quote_plus( link_url ) ) ) )

    if cxm_show_comment_link or cxm_show_comments:
        if num_comments > 0:

            if cxm_show_comment_link:
                entries.append( ( translation(30052) , #Show comment links
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            if cxm_show_comments:
                entries.append( ( translation(30050) ,  #Show comments
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )

        else:
            entries.append( ( translation(30053) ,  #No comments
                          "xbmc.executebuiltin('Action(Close)')" ) )

    if GCXM_hasmultiplesubreddit and cxm_show_go_to:
        entries.append( ( translation(30051)+" %s" %colored_subreddit_full ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit,True)  ) ) ) )

    if cxm_show_new_from:

        entries.append( ( translation(30055)+" %s" %colored_subreddit_short ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit+'/new',True)  ) ) ) )

    if cxm_show_add_shortcuts:
        if not subreddit_in_favorites(subreddit):

            entries.append( ( translation(30056) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addSubreddit&url=%s)" % ( sys.argv[0], subreddit ) ) )

    if cxm_show_filter_subreddit:
            entries.append( ( translation(30057) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], subreddit, 'subreddit' ) ) )
    if cxm_show_filter_domain:
            entries.append( ( translation(30057) %colored_domain_full ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], domain, 'domain' ) ) )

    from reddit import reddit_refresh_token
    if reddit_refresh_token and cxm_show_reddit_save:
        if this_is_a_user_saved_list(GCXM_subreddit_key):

            entries.append( ( translation(30059) ,
                                  "XBMC.RunPlugin(%s?mode=reddit_save&url=%s&name=%s)" % ( sys.argv[0], '/api/unsave/', post_id ) ) )
        else:
            entries.append( ( translation(30058) ,
                                  "XBMC.RunPlugin(%s?mode=reddit_save&url=%s&name=%s)" % ( sys.argv[0], '/api/save/', post_id ) ) )

    if cxm_show_youtube_items:

        from domains import ClassYoutube
        match=re.compile( ClassYoutube.regex, re.I).findall( link_url )  #regex='(youtube.com/)|(youtu.be/)|(youtube-nocookie.com/)|(plugin.video.youtube/play)'
        if match:

            entries.append( ( translation(30048) ,
                                "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listRelatedVideo&url=%s&type=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(link_url), 'channel' ) ) )
            entries.append( ( translation(30049) ,
                                "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listRelatedVideo&url=%s&type=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(link_url), 'related' ) ) )

    return entries

def listLinksInComment(url, name, type_):
    from domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type
    from utils import markdown_to_bbcode, unescape
    from guis import progressBG

    log('listLinksInComment:%s:%s' %(type_,url) )


    directory_items=[]
    author=""
    ShowOnlyCommentsWithlink=False

    if type_=='linksOnly':
        ShowOnlyCommentsWithlink=True

    url=urllib.quote_plus(url,safe=':/?&')
    if '?' in url:
        url=url.split('?', 1)[0]+'.json?'+url.split('?', 1)[1]
    else:
        url+= '.json'

    loading_indicator=progressBG(translation(30024))
    loading_indicator.update(0,'Retrieving comments')

    content = reddit_request(url)
    if not content:
        loading_indicator.end()
        return

    loading_indicator.update(10,'Parsing')
    content = json.loads(content)

    del harvest[:]

    r_linkHunter(content[0]['data']['children'])

    try:submitter=content[0]['data']['children'][0]['data']['author']
    except: submitter=''

    try:post_title=content[0]['data']['children'][0]['data']['title']
    except:post_title=''

    r_linkHunter(content[1]['data']['children'])

    comment_score=0

    loading_indicator.set_tick_total(len(harvest))

    for i, h in enumerate(harvest):
        try:

            comment_score=h[0]

            link_url=h[2]
            desc100=h[3].replace('\n',' ')[0:100] #first 100 characters of description

            kind=h[6] #reddit uses t1 for user comments and t3 for OP text of the post. like a poster describing the post.
            d=h[5]   #depth of the comment

            tab=" "*d if d>0 else "-"

            from urlparse import urlparse
            domain = '{uri.netloc}'.format( uri=urlparse( link_url ) )

            author=h[7]
            DirectoryItem_url=''

            if comment_score < int_CommentTreshold:
                continue


            ld=parse_reddit_link(link_url=link_url, assume_is_video=False, needs_preview=True, get_playable_url=True )

            if kind=='t1':
                list_title=r"[COLOR cadetblue]%3d[/COLOR] %s" %( h[0], tab )
            elif kind=='t3':
                list_title=r"[COLOR cadetblue]Title [/COLOR] %s" %( tab )

            plot=h[3].replace('](', '] (')
            plot= markdown_to_bbcode(plot)
            plot=unescape(plot)  #convert html entities e.g.:(&#39;)

            liz=xbmcgui.ListItem(label=list_title +': '+ desc100)

            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": plot, "studio": domain, "votes": str(comment_score), "director": author  } )
            isFolder=False

            if link_url:
                DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, link_url)

                liz.setProperty('IsPlayable', setProperty_IsPlayable)
                liz.setProperty('url', DirectoryItem_url)  #<-- needed by the xml gui skin
                liz.setPath(DirectoryItem_url)

                if domain:
                    plot= "  [COLOR greenyellow][%s] %s"%(domain, plot )  + "[/COLOR]"
                else:
                    plot= "  [COLOR greenyellow][%s]"%( plot ) + "[/COLOR]"
                liz.setLabel(list_title+plot)

                if ld:
                    liz.setArt({"thumb": ld.poster, "poster":ld.poster, "banner":ld.poster, "fanart":ld.poster, "landscape":ld.poster   })

            if DirectoryItem_url:

                directory_items.append( (DirectoryItem_url, liz, isFolder,) )

            else:

                if not ShowOnlyCommentsWithlink:
                    result=h[3].replace('](', '] (')
                    result=markdown_to_bbcode(result)
                    liz=xbmcgui.ListItem(label=list_title + desc100)
                    liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": domain, "votes": str(h[0]), "director": author } )
                    liz.setProperty('IsPlayable', 'false')

                    directory_items.append( ("", liz, False,) )

        except Exception as e:
            log('  EXCEPTION:' + str(e) )


        loading_indicator.tick(1, desc100)
    loading_indicator.end()

    xbmcplugin.setContent(pluginhandle, "movies")    #files, songs, artists, albums, movies, tvshows, episodes, musicvideos
    xbmcplugin.setPluginCategory(pluginhandle,'Comments')

    xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
    xbmcplugin.endOfDirectory(pluginhandle)

    if comments_viewMode:
        xbmc.executebuiltin('Container.SetViewMode(%s)' %comments_viewMode)


harvest=[]
def r_linkHunter(json_node,d=0):
    from utils import clean_str

    prog = re.compile('<a href=[\'"]?([^\'" >]+)[\'"]>(.*?)</a>')
    for e in json_node:
        link_desc=""
        link_http=""
        author=""
        created_utc=""
        e_data=e.get('data')
        score=e_data.get('score',0)
        if e['kind']=='t1':     #'t1' for comments   'more' for more comments (not supported)

            try: replies=e_data.get('replies')['data']['children']
            except (AttributeError,TypeError): replies=""

            post_text=clean_str(e_data,['body'])
            post_text=post_text.replace("\n\n","\n")

            post_html=clean_str(e_data,['body_html'])

            created_utc=e_data.get('created_utc','')

            author=clean_str(e_data,['author'])


            result = prog.findall(post_html)
            if result:

                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

                for link_http,link_desc in result:
                    harvest.append((score, link_desc, link_http, link_desc, post_html, d, "t1",author,created_utc,)   )
            else:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

            d+=1 #d tells us how deep is the comment in
            r_linkHunter(replies,d)
            d-=1

        if e['kind']=='t3':     #'t3' for post text (a description of the post)
            self_text=clean_str(e_data,['selftext'])
            self_text_html=clean_str(e_data,['selftext_html'])

            result = prog.findall(self_text_html)
            if len(result) > 0 :
                harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc, )   )

                for link_http,link_desc in result:
                    harvest.append((score, link_desc, link_http, link_desc, self_text_html, d, "t3",author,created_utc, )   )
            else:
                if len(self_text) > 0: #don't post an empty titles
                    harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc,)   )



if __name__ == '__main__':
    pass

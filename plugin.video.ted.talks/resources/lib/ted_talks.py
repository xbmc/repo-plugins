import itertools
import os
import sys
import time
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs

from . import menu_util
from . import plugin
from . import settings
from . import ted_talks_scraper
from .model.fetcher import Fetcher
from .model.rss_scraper import NewTalksRss
from .model.search_scraper import Search
from .model.speakers_scraper import Speakers
from .model.topics_scraper import Topics

class UI:

    def __init__(self, fetcher, ted_talks):
        self.fetcher = fetcher
        self.ted_talks = ted_talks

    def endofdirectory(self, sortMethod='title', updateListing=False):
        # set sortmethod to something xbmc can use
        if sortMethod == 'title':
            sortMethod = xbmcplugin.SORT_METHOD_LABEL
        elif sortMethod == 'date':
            sortMethod = xbmcplugin.SORT_METHOD_DATE
        elif sortMethod == 'none':
            sortMethod = xbmcplugin.SORT_METHOD_NONE

        # Sort methods are required in library mode.
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod)
        # let xbmc know the script is done adding items to the list.
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), updateListing=updateListing)

    def addItem(self, title, mode, url=None, img='', args={}, video_info={}, isFolder=True, total_items=0):
        # Create action url
        args['mode'] = mode
        if url:
            args['url'] = url

        args = [k + '=' + urllib.parse.quote_plus(v.encode('ascii', 'ignore')) for k, v in args.items()]
        action_url = sys.argv[0] + '?' + "&".join(args)

        li = xbmcgui.ListItem(label=title, offscreen=True)
        li.setArt({'icon': img, 'thumb': img})
        video_info = dict((k, v) for k, v in video_info.items() if k in ['date', 'plot', 'mediatype'])
        li.setInfo('video', video_info)
        if 'duration' in video_info:
            # To set with second granularity must do this rather than via setInfo
            li.addStreamInfo('video', {'duration' : video_info['duration']})
        if not isFolder:
            li.setProperty('IsPlayable', 'true')  # let xbmc know this can be played, unlike a folder.
            context_menu = menu_util.create_context_menu(getLS=plugin.getLS)
            li.addContextMenuItems(context_menu, replaceItems=False)
        else:
            li.addContextMenuItems([], replaceItems=False)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=action_url, listitem=li, isFolder=isFolder, totalItems=total_items)

    def playVideo(self, url, icon):

        plugin.report('%s = %s' % ('url', str(url)), level='debug')

        subs_language = settings.get_subtitle_languages()
        playlist, title, subs, info_labels = self.ted_talks.get_video_details(url=url, subs_language=subs_language)

        playlist_file = os.path.join(xbmcvfs.translatePath("special://temp/"), 'ted_talks.m3u8')
        with open(playlist_file, 'w', encoding='utf-8') as fh:
            fh.write(playlist)

        li = xbmcgui.ListItem(title, path=playlist_file, offscreen=True)
        li.setArt({'icon': icon, 'thumb': icon})
        li.setInfo(type='Video', infoLabels=info_labels)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

        subs_file = os.path.join(xbmcvfs.translatePath("special://temp/"), 'ted_talks_subs.srt')
        with open(subs_file, 'w', encoding='utf-8') as fh:
            if subs:
                fh.write(subs)
            else:
                pass # Write empty file as subs will persist and appear for the next video.
            
        # Up to 30s to start
        start_time = time.time()
        player = xbmc.Player()
        while not player.isPlaying() and time.time() - start_time < 10:
            pass

        if not player.isPlaying():
            # No user message: user was probably already notified of a problem with the stream.
            plugin.report('Could not show subtitles: timed out waiting for player to start.')
            return
        else:
            if subs:
                player.setSubtitles(subs_file)
                player.showSubtitles(True)
            else:
                player.showSubtitles(False)

    def navItems(self, navItems, mode):
        if navItems['next']:
            self.addItem(plugin.getLS(30020), mode, navItems['next'])
        if navItems['previous']:
            self.addItem(plugin.getLS(30021), mode, navItems['previous'])

    def showCategories(self):
        self.addItem(plugin.getLS(30001), 'newTalksRss', video_info={'Plot':plugin.getLS(30031)})
        self.addItem(plugin.getLS(30002), 'speakers', video_info={'Plot':plugin.getLS(30032)})
        self.addItem(plugin.getLS(30004) + "...", 'search', video_info={'Plot':plugin.getLS(30034)})
        self.addItem(plugin.getLS(30007), 'topics', video_info={'Plot':plugin.getLS(30033)})
        self.endofdirectory()

    def newTalksRss(self):
        newTalks = NewTalksRss(plugin.report)
        for talk in newTalks.get_new_talks():
            self.addItem(title=talk['title'], mode='playVideo', url=talk['link'], img=talk['thumb'], video_info=talk, isFolder=False)
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        self.endofdirectory(sortMethod='date')

    def speakerVids(self, url):
        talks_generator = Speakers(self.fetcher.get_HTML).get_talks_for_speaker(url)
        for title, link, img in talks_generator:
            self.addItem(title, 'playVideo', link, img, isFolder=False)
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        self.endofdirectory()


class Action(object):
    '''
    Some action that can be executed by the user.
    '''

    def __init__(self, mode, required_args, logger=None, get_HTML=None, *args, **kwargs):
        self.mode = mode
        self.required_args = set(required_args)
        self.logger = logger
        self.get_HTML = get_HTML

    def run(self, args):
        good = self.required_args.issubset(list(args.keys()))
        if good:
            self.run_internal(args)
        else:
            self.report_problem(args)

    def report_problem(self, args):
        # The theory is that this might happen for a favorite from another version;
        # though we can't be sure about the cause hence vagueness in friendly message.
        friendly_message = "Action '%s' failed. Try re-creating the item." % (self.mode)
        self.logger("%s\nBad arguments: %s" % (friendly_message, args), friendly_message)


class PlayVideoAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(PlayVideoAction, self).__init__('playVideo', ['url'], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        self.ui.playVideo(args['url'], args['icon'] if 'icon' in args else None)


class NewTalksAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(NewTalksAction, self).__init__('newTalksRss', [], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        self.ui.newTalksRss()


class SpeakersAction(Action):

    def __init__(self, ui, get_HTML, *args, **kwargs):
        super(SpeakersAction, self).__init__('speakers', [], *args, **kwargs)
        self.ui = ui
        self.get_HTML = get_HTML

    def run_internal(self, args):
        page_count = Speakers(self.get_HTML).get_speaker_page_count()
        pages_per_group = 4
        for i in range(1, page_count // pages_per_group + 1):
            label = '%s-%s' % ((i - 1) * pages_per_group + 1, i * pages_per_group)
            self.ui.addItem(label, 'speakerGroup', label, isFolder=True)
        remainder = page_count % pages_per_group
        if remainder != 0:
            label = '%s-%s' % (page_count - remainder, page_count)
            self.ui.addItem(label, 'speakerGroup', label, isFolder=True)
        self.ui.endofdirectory(sortMethod='none')


class SpeakerGroupAction(Action):

    def __init__(self, ui, get_HTML, *args, **kwargs):
        super(SpeakerGroupAction, self).__init__('speakerGroup', ['url'], *args, **kwargs)
        self.ui = ui
        self.get_HTML = get_HTML

    def run_internal(self, args):
        pages = args['url']
        pages = pages.split('-')
        pages = list(range(int(pages[0]), int(pages[1]) + 1))
        generator = Speakers(self.get_HTML).get_speakers_for_pages(pages)
        pages_count = next(itertools.islice(generator, 1))
        for title, link, img in generator:
            self.ui.addItem(title, 'speakerVids', link, img=img, isFolder=True, total_items=120)

        if pages[-1] < pages_count:
            label = '%s-%s' % (pages[-1] + 1, min(pages_count, pages[-1] * 2 - pages[0]))
            self.ui.addItem(label + '...', 'speakerGroup', label, isFolder=True)
        xbmcplugin.setContent(int(sys.argv[1]), 'artists')
        self.ui.endofdirectory(sortMethod='none')


class SpeakerVideosAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(SpeakerVideosAction, self).__init__('speakerVids', ['url'], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        self.ui.speakerVids(args['url'])


class TopicsAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(TopicsAction, self).__init__('topics', [], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        topics = Topics(self.get_HTML, self.logger)
        for title, topic in topics.get_topics():
            self.ui.addItem(title, 'topicVids', args={ 'topic': topic }, isFolder=True)
        xbmcplugin.setContent(int(sys.argv[1]), 'artists')
        self.ui.endofdirectory()


class TopicVideosAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(TopicVideosAction, self).__init__('topicVids', ['topic'], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        topics = Topics(self.get_HTML, self.logger)
        for title, link, img, speaker in topics.get_talks(args['topic']):
            self.ui.addItem(title, 'playVideo', link, img, isFolder=False, video_info={ 'author': speaker, 'mediatype': "video" })
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        self.ui.endofdirectory()


class SearchActionBase(Action):

    def __init__(self, ui, *args, **kwargs):
        super(SearchActionBase, self).__init__(*args, **kwargs)
        self.ui = ui

    def __add_items__(self, search_term, page, current_items, update_listing):
        talks_generator = Search(self.get_HTML).get_talks_for_search(search_term, page)
        remaining_talks = next(itertools.islice(talks_generator, 1))
        search_results = list(itertools.chain(current_items, talks_generator))
        for title, link, img in search_results:
            self.ui.addItem(title, 'playVideo', link, img, isFolder=False, video_info={ 'mediatype': "video" })
        if remaining_talks:
            self.ui.addItem(plugin.getLS(30022), 'searchMore', args={'search_term': search_term, 'page': str(page + 1)})
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        self.ui.endofdirectory(sortMethod='none', updateListing=update_listing)

        return search_results


class SearchAction(SearchActionBase):

    def __init__(self, *args, **kwargs):
        # Well this is a mess. More research needed...
        super(SearchAction, self).__init__(*(args + ('search', [])), **kwargs)

    def run_internal(self, args):
        keyboard = xbmc.Keyboard(settings.get_current_search(), plugin.getLS(30004))
        keyboard.doModal()

        if not keyboard.isConfirmed():
            return

        search_term = keyboard.getText()
        settings.set_current_search(search_term)
        self.__add_items__(search_term, 1, [], False)


class SearchMoreAction(SearchActionBase):

    def __init__(self, *args, **kwargs):
        # Well this is a mess. More research needed...
        super(SearchMoreAction, self).__init__(*(args + ('searchMore', ['search_term', 'page'])), **kwargs)

    def run_internal(self, args):
        search_term = args['search_term']
        page = int(args['page'])
        self.__add_items__(search_term, page + 1, [], False)


class Main:

    def __init__(self, args_map):
        self.args_map = args_map
        self.fetcher = Fetcher(plugin.report)
        self.ted_talks = ted_talks_scraper.TedTalks(self.fetcher, plugin.report)

    def run(self):
        ui = UI(self.fetcher, self.ted_talks)
        if 'mode' not in self.args_map:
            ui.showCategories()
        else:
            modes = [
                PlayVideoAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                NewTalksAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                SearchAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                SearchMoreAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                SpeakersAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                SpeakerGroupAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                SpeakerVideosAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                TopicsAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML),
                TopicVideosAction(ui, logger=plugin.report, get_HTML=self.fetcher.get_HTML)
            ]
            modes = dict([(m.mode, m) for m in modes])
            mode = self.args_map['mode']
            if mode in modes:
                modes[mode].run(self.args_map)
            else:
                # Bit of a hack (cough)
                Action(mode, [], plugin.report).report_problem(self.args_map)

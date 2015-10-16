import sys
import urllib
import ted_talks_scraper
import plugin
import settings
from model.fetcher import Fetcher
from model.rss_scraper import NewTalksRss
from model.speakers_scraper import Speakers
from model.util import resizeImage
from model.search_scraper import Search
from model.topics_scraper import Topics
import menu_util
import os
import time
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import itertools


class UI:

    def __init__(self, get_HTML, ted_talks):
        self.get_HTML = get_HTML
        self.ted_talks = ted_talks
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

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
        args['mode'] = mode;
        if url:
            args['url'] = url
        if img:
            img = resizeImage(img)
            args['icon'] = img
        args = [k + '=' + urllib.quote_plus(v.encode('ascii', 'ignore')) for k, v in args.iteritems()]
        action_url = sys.argv[0] + '?' + "&".join(args)

        li = xbmcgui.ListItem(label=title, iconImage=img, thumbnailImage=img)
        video_info = dict((k, v) for k, v in video_info.iteritems() if k in ['date', 'plot'])
        if video_info:
            li.setInfo('video', video_info)
        if 'duration' in video_info:
            # To set with second granularity must do this rather than via setInfo
            li.addStreamInfo('video', { 'duration' : video_info['duration'] })
        if not isFolder:
            li.setProperty("IsPlayable", "true")  # let xbmc know this can be played, unlike a folder.
            context_menu = menu_util.create_context_menu(getLS=plugin.getLS)
            li.addContextMenuItems(context_menu, replaceItems=True)
        else:
            li.addContextMenuItems([], replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=action_url, listitem=li, isFolder=isFolder, totalItems=total_items)

    def playVideo(self, url, icon):
        subs_language = settings.get_subtitle_languages()
        title, url, subs, info_labels = self.ted_talks.getVideoDetails(url=url, video_quality=settings.video_quality, subs_language=subs_language)
        li = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon, path=url)
        li.setInfo(type='Video', infoLabels=info_labels)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        if subs:
            # If not we either don't want them, or should have displayed a notification.
            subs_file = os.path.join(xbmc.translatePath("special://temp"), 'ted_talks_subs.srt')
            fh = open(subs_file, 'w')
            try:
                fh.write(subs.encode('utf-8'))
            finally:
                fh.close()
                player = xbmc.Player()
            # Up to 30s to start
            start_time = time.time()
            while not player.isPlaying() and time.time() - start_time < 30:
                time.sleep(1)
            if player.isPlaying():
                xbmc.Player().setSubtitles(subs_file);
            else:
                # No user message: user was probably already notified of a problem with the stream.
                plugin.report('Could not show subtitles: timed out waiting for player to start.')

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
        self.endofdirectory(sortMethod='date')

    def speakerVids(self, url):
        talks_generator = Speakers(self.get_HTML).get_talks_for_speaker(url)
        for title, link, img in talks_generator:
            self.addItem(title, 'playVideo', link, img, isFolder=False)
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
        good = self.required_args.issubset(args.keys())
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
        for i in range(1, page_count / pages_per_group + 1):
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
        pages = range(int(pages[0]), int(pages[1]) + 1)
        generator = Speakers(self.get_HTML).get_speakers_for_pages(pages)
        pages_count = itertools.islice(generator, 1).next()
        for title, link, img in generator:
            self.ui.addItem(title, 'speakerVids', link, img=img, isFolder=True, total_items=120)

        if pages[-1] < pages_count:
            label = '%s-%s' % (pages[-1] + 1, min(pages_count, pages[-1] * 2 - pages[0]))
            self.ui.addItem(label + '...', 'speakerGroup', label, isFolder=True)
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
        self.ui.endofdirectory()


class TopicVideosAction(Action):

    def __init__(self, ui, *args, **kwargs):
        super(TopicVideosAction, self).__init__('topicVids', ['topic'], *args, **kwargs)
        self.ui = ui

    def run_internal(self, args):
        topics = Topics(self.get_HTML, self.logger)
        for title, link, img, speaker in topics.get_talks(args['topic']):
            self.ui.addItem(title, 'playVideo', link, img, isFolder=False, video_info={ 'author': speaker })
        self.ui.endofdirectory()


class SearchActionBase(Action):

    def __init__(self, ui, *args, **kwargs):
        super(SearchActionBase, self).__init__(*args, **kwargs)
        self.ui = ui

    def __add_items__(self, search_term, page, current_items, update_listing):
        talks_generator = Search(self.get_HTML).get_talks_for_search(search_term, page)
        remaining_talks = itertools.islice(talks_generator, 1).next()
        search_results = list(itertools.chain(current_items, talks_generator))
        for title, link, img in search_results:
            self.ui.addItem(title, 'playVideo', link, img, isFolder=False)
        if remaining_talks:
            self.ui.addItem(plugin.getLS(30022), 'searchMore', args={'search_term': search_term, 'page': str(page + 1)})
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
        self.get_HTML = Fetcher(plugin.report, xbmc.translatePath).getHTML
        self.ted_talks = ted_talks_scraper.TedTalks(self.get_HTML, plugin.report)

    def run(self):
        ui = UI(self.get_HTML, self.ted_talks)
        if 'mode' not in self.args_map:
            ui.showCategories()
        else:
            modes = [
                PlayVideoAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                NewTalksAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                SearchAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                SearchMoreAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                SpeakersAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                SpeakerGroupAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                SpeakerVideosAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                TopicsAction(ui, logger=plugin.report, get_HTML=self.get_HTML),
                TopicVideosAction(ui, logger=plugin.report, get_HTML=self.get_HTML)
            ]
            modes = dict([(m.mode, m) for m in modes])
            mode = self.args_map['mode']
            if mode in modes:
                modes[mode].run(self.args_map)
            else:
                # Bit of a hack (cough)
                Action(mode, [], plugin.report).report_problem(self.args_map)

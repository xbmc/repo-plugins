"""
Management of recent searches

Copyright (c) 2018, Leo Moll
SPDX-License-Identifier: MIT
"""

import os
import json
import time
import resources.lib.appContext as appContext
import resources.lib.extendedSearchModel as ExtendedSearchModel

from contextlib import closing
from operator import itemgetter
from codecs import open
# pylint: disable=import-error
import xbmcplugin
import resources.lib.ui.filmlistUi as FilmlistUi


class ExtendedSearch(object):
    """
    The recent searches class

    Args:
        plugin(MediathekView): the plugin object

        extendedsearch(bool): if `True` the class
            stores extended searches

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`
    """

    """
    ActivateWindow(window[,dir,return]) -- 
    ReplaceWindow(window,dir) --  This is the same as ActivateWindow() but it doesn't update the window history list,
    Container.Refresh
    Container.Update     Update current listing. Send Container.Update(path,replace) to reset the path history. 
    
    """

    def __init__(self, plugin, pDatabase, pAction, pSearchId):
        self.plugin = plugin
        self.database = pDatabase;
        self.handle = plugin.addon_handle
        self.sortmethods = [xbmcplugin.SORT_METHOD_TITLE]
        self.recents = []
        self.action = pAction
        self.searchId = pSearchId
        self.datafile = os.path.join(
            appContext.MVSETTINGS.getDatapath(),
            'searchConfig.json'
        )
        self.path = appContext.MVSETTINGS.getDatapath()
        self.logger = appContext.MVLOGGER.get_new_logger('ExtendedSearch')
        self.notifier = appContext.MVNOTIFIER
        #
        self.recents = []
        self._load()
        #

    def show(self):
        """ populate UI with extended search elements """
        self.logger.debug('show action: {} searchId:{}', self.action, self.searchId)
        start = time.time()
        #
        if self.action == "SHOW":
            self.showList()
            self.plugin.setViewId(self.plugin.resolveViewId('MAIN'))
        elif self.action == "RUN":
            data = self._getModelById(self.searchId);
            # self.database.extendedSearchQuery(data, FilmUI(self.plugin))
            ui = FilmlistUi.FilmlistUi(self.plugin)
            ui.generate(self.database.extendedSearch(data))

        elif self.action == "NEW":
            (txt, confirm) = self.notifier.get_entered_text(heading=30419)
            if confirm:
                x = ExtendedSearchModel.ExtendedSearchModel(txt)
                self.recents.append(x.toDict())
                self._save()
                self._load()
                #
                cmd = 'Container.update({}, replace)'.format(
                                self.plugin.build_url({
                                    'mode': "extendedSearchScreen",
                                    'extendedSearchAction': 'EDIT',
                                    'searchId' : x.getId()
                                })
                            )
                self.plugin.end_of_directory(True, False, False)
                self.plugin.run_builtin(cmd)
            self.plugin.setViewId(self.plugin.resolveViewId('MAIN'))

        elif self.action == "EDIT":
            data = self._getModelById(self.searchId);
            self.showEntry(data)
            self.plugin.setViewId(self.plugin.resolveViewId('MAIN'))

        elif self.action == "DELETE":
            self.recents.remove(self._getItemById(self.searchId))
            self._save()
            #
            cmd = 'Container.refresh({})'.format(
                            self.plugin.build_url({
                                'mode': "extendedSearchScreen",
                                'extendedSearchAction': 'SHOW'
                            })
                        )
            # def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=False):
            self.plugin.end_of_directory(True, False, False)
            self.plugin.run_builtin(cmd)
            self.plugin.setViewId(self.plugin.resolveViewId('MAIN'))

        if self.action[:5] == 'EDIT-':
            #
            cmd = 'Container.update({}, replace)'.format(
                self.plugin.build_url({
                    'mode': "extendedSearchScreen",
                    'extendedSearchAction': 'EDIT',
                    'searchId' : self.searchId
                })
            )
            #
            dataModel = self._getModelById(self.searchId)
            #
            if self.action == "EDIT-NAME":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getNameAsString(), heading=30419)
                if confirm:
                    dataModel.setName(txt)

            elif self.action == "EDIT-TITLE":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getTitleAsString(), heading=30412)
                if confirm:
                    dataModel.setTitle(txt)

            elif self.action == "EDIT-SHOW":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getShowAsString(), heading=30411)
                if confirm:
                    dataModel.setShow(txt)

            elif self.action == "EDIT-DESCRIPTION":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getDescriptionAsString(), heading=30413)
                if confirm:
                    dataModel.setDescription(txt)

            elif self.action == "EDIT-CHANNEL":
                channelList = self.database.getChannelList()
                #
                preselect = []
                for i, channelName in enumerate(channelList):
                    for selectedChannelName in dataModel.getChannel():
                        if selectedChannelName == channelName:
                            preselect.append(i)
                #
                selectedIdxList = self.notifier.get_entered_multiselect(heading=30414, options=channelList, preselect=preselect)
                if selectedIdxList is not None:
                    selectedChannels = []
                    for idx in selectedIdxList:
                        selectedChannels.append(channelList[idx])
                    dataModel.setChannel("|".join(selectedChannels))

            elif self.action == "EDIT-MINLENGTH":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getMinLengthAsString(), heading=30418)
                if confirm:
                    dataModel.setMinLength(txt)

            elif self.action == "EDIT-NOFUTURE":
                selectedIdx = self.notifier.get_entered_select(heading=30417, list=[self.plugin.language(30409), self.plugin.language(30410)], preselect=int(dataModel.getIgnoreTrailerAsString()))
                if selectedIdx is not None and selectedIdx > -1:
                    dataModel.setIgnoreTrailer(selectedIdx)

            elif self.action == "EDIT-BLACKLIST":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getExcludeTitleAsString(), heading=30415)
                if confirm:
                    dataModel.setExcludeTitle(txt)

            elif self.action == "EDIT-MAXROWS":
                (txt, confirm) = self.notifier.get_entered_text(deftext=dataModel.getMaxResultsAsString(), heading=30115)
                if confirm:
                    dataModel.setMaxResults(txt)
            #
            #
            self._saveModel(dataModel)
            #
            self.plugin.end_of_directory(True, False, False)
            self.plugin.run_builtin(cmd)
        self.logger.debug('show processed: {} sec', time.time() - start)

    def showList(self):
        """ populate all elements from extended search """
        self.logger.debug('showList')
        start = time.time()
        #
        self.plugin.add_folder_item(
            30931,
            {'mode': "extendedSearchScreen", 'extendedSearchAction': 'NEW'},
            icon=os.path.join(self.plugin.path, 'resources', 'icons', 'search-m.png')
        )
        #
        for entry in self.recents:
            self.plugin.add_folder_item(
                entry['name'],
                {
                    'mode': "extendedSearchScreen",
                    'searchId': entry['id'],
                    'extendedSearchAction': 'RUN'
                },
                [
                    (
                        self.plugin.language(30933),
                        'Container.update({})'.format(
                            self.plugin.build_url({
                                'mode': "extendedSearchScreen",
                                'searchId': str(entry['id']),
                                'extendedSearchAction': 'EDIT'
                            })
                        )
                    ),
                    (
                        self.plugin.language(30932),
                        'Container.update({})'.format(
                            self.plugin.build_url({
                                'mode': "extendedSearchScreen",
                                'searchId': str(entry['id']),
                                'extendedSearchAction': 'DELETE'
                            })
                        )
                    )
                ],
                icon=os.path.join(
                    self.plugin.path,
                    'resources',
                    'icons',
                    'results-m.png'
                )
            )
        #
        self.plugin.end_of_directory()
        #
        self.logger.debug('showList processed: {} sec', time.time() - start)

    def showEntry(self, extSearchModel):
        #
        self.logger.debug('showEntry')
        start = time.time()
        #
        self.plugin.add_folder_item(
            30934,
            {'mode': "extendedSearchScreen", 'extendedSearchAction': 'RUN', 'searchId': extSearchModel.getId()},
            icon=os.path.join(self.plugin.path, 'resources', 'icons', 'search-m.png')
        )
        #
        self.plugin.add_folder_item(
                self.plugin.getCaption(30401) + " : " + extSearchModel.getName(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-NAME'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30403) + " : " + extSearchModel.getShowAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-SHOW'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30402) + " : " + extSearchModel.getTitleAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-TITLE'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30404) + " : " + extSearchModel.getDescriptionAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-DESCRIPTION'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30405) + " : " + extSearchModel.getChannelAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-CHANNEL'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30408) + " : " + extSearchModel.getExcludeTitleAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-BLACKLIST'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30406) + " : " + extSearchModel.getMinLengthAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-MINLENGTH'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.add_folder_item(
                self.plugin.getCaption(30115) + " : " + extSearchModel.getMaxResultsAsString(),
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-MAXROWS'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        if extSearchModel.isIgnoreTrailer():
            languageString = self.plugin.language(30410)
        else:
            languageString = self.plugin.language(30409)

        self.plugin.add_folder_item(
                self.plugin.getCaption(30407) + " : " + languageString,
                {
                    'mode': "extendedSearchScreen",
                    'searchId': extSearchModel.getId(),
                    'extendedSearchAction': 'EDIT-NOFUTURE'
                },
                None,
                icon=os.path.join(self.plugin.path, 'resources', 'icons', 'control-m.png')
            )
        self.plugin.end_of_directory()
        self.logger.debug('showEntry processed: {} sec', time.time() - start)

######################################

    def _getItemById(self, pId):
        for entry in self.recents:
            if int(entry['id']) == int(pId):
                return entry
        return None

    def _getModelById(self, pId):
        for entry in self.recents:
            if int(entry['id']) == int(pId):
                x = ExtendedSearchModel.ExtendedSearchModel("")
                x.fromDict(entry)
                return x
        return None

    def _load(self):
        """ Loads the recent searches list """
        self.logger.debug('_load')
        start = time.time()
        #
        listOfItems = []
        try:
            with closing(open(self.datafile, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, list):
                    listOfItems = sorted(data, key=itemgetter('when'), reverse=True)
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to load last searches file {}: {}', self.datafile, err)
        self.recents = listOfItems
        #
        self.logger.debug('_load processed: {} sec', time.time() - start)

    def _save(self):
        """ Saves the recent searches list """
        self.logger.debug('_save')
        start = time.time()
        #
        data = sorted(self.recents, key=itemgetter('when'), reverse=True)
        try:
            with closing(open(self.datafile, 'w', encoding='utf-8')) as json_file:
                json.dump(data, json_file)
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to write last searches file {}: {}', self.datafile, err)
        #
        self.logger.debug('_save processed: {} sec', time.time() - start)
        #
        return self

    def _saveModel(self, extendedSearchModel):
        self.logger.debug('_saveModel')
        start = time.time()
        #
        data = self._getItemById(extendedSearchModel.getId())
        self.recents.remove(data)
        data = extendedSearchModel.toDict()
        self.recents.append(data)
        self._save()
        #
        self.logger.debug('_saveModel processed: {} sec', time.time() - start)

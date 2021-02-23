"""
Management of recent searches

Copyright (c) 2018, Leo Moll
SPDX-License-Identifier: MIT
"""

import time
import resources.lib.appContext as appContext


class ExtendedSearchModel(object):
    """
    """

    def __init__(self, pName):
        self.logger = appContext.MVLOGGER.get_new_logger('ExtendedSearchModel')
        self.settings = appContext.MVSETTINGS
        self.id = int(time.time())
        self.name = pName
        self.channel = []
        self.title = []
        self.setShow(pName)
        self.showId = []
        self.showStartLetter = []
        self.exactMatchForShow = 0
        self.description = []
        self.excludeTitle = []
        self.setExcludeTitle(self.settings.getBlacklist())
        self.minLength = 0
        self.setMinLength((self.settings.getMinLength()))
        self.ignoreTrailer = 1
        self.setIgnoreTrailer(self.settings.getNoFutur())
        self.maxResults = 0
        self.setMaxResults(self.settings.getMaxResults())
        self.recentOnly = 0
        self.when = self.id
        #
        #
        """
        self.recents = [
                { 
                    "id" : 1, 
                    "name" : "",
                    "channel" : [ "ARD" , "WDR" ],
                    "title" : ["something"],
                    "show" : ["something"],
                    "showId" : [ "XXY" ],
                    "showStartLetter" : []
                    "description" : ["bla" ],
                    "excludeTitle" : ["bla"],
                    "minLength" : 60,
                    "ignoreTrailer" : 1,
                    "maxResults" : 1000,
                    "exactMatchForShow" : 0
                    "recentOnly" : 0
                    "when" : 1312312
                }
            ]
        """

    ################
    # RESET
    ################
    def reset(self):
        self.name = ''
        self.channel = []
        self.title = []
        self.show = []
        self.showId = []
        self.showStartLetter = []
        self.exactMatchForShow = 0
        self.description = []
        self.excludeTitle = []
        self.minLength = 0
        self.ignoreTrailer = 0
        self.maxResults = 0
        self.recentOnly = 0

    ################
    # GET
    ################

    def getId(self):
        return self.id;

    def getName(self):
        return self.name;

    def getChannel(self):
        return self.channel

    def getShow(self):
        return self.show

    def getShowId(self):
        return self.showId

    def getShowStartLetter(self):
        return self.showStartLetter

    def getTitle(self):
        return self.title

    def getDescription(self):
        return self.description

    def getExcludeTitle(self):
        return self.excludeTitle

    def getMinLength(self):
        return self.minLength

    def isIgnoreTrailer(self):
        return self.ignoreTrailer == 1

    def getMaxResults(self):
        return self.maxResults

    def isExactMatchForShow(self):
        return self.exactMatchForShow == 1

    def isRecentOnly(self):
        return self.recentOnly == 1

    ################
    # GET
    ################

    def getIdAsString(self):
        return self.id;

    def getNameAsString(self):
        return self.name;

    def getChannelAsString(self):
        return ', '.join(self.channel)

    def getShowAsString(self):
        return '|'.join(self.show)

    def getShowIdAsString(self):
        return '|'.join(self.showId)

    def getShowStartLetterAsString(self):
        return '|'.join(self.showStartLetter)

    def getTitleAsString(self):
        return '|'.join(self.title)

    def getDescriptionAsString(self):
        return '|'.join(self.description)

    def getExcludeTitleAsString(self):
        return '|'.join(self.excludeTitle)

    def getMinLengthAsString(self):
        return str(self.minLength)

    def getIgnoreTrailerAsString(self):
        return str(self.ignoreTrailer)

    def getMaxResultsAsString(self):
        return str(self.maxResults)

    def getExactMatchForShowAsString(self):
        return str(self.exactMatchForShow)

    def getRecentOnlyAsString(self):
        return str(self.recentOnly)

    ################
    # SET
    ################
    def setId(self, pValue):
        self.id = pValue

    def setName(self, pValue):
        self.name = pValue;

    def setChannel(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.channel = pValue

    def setShow(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.show = pValue

    def setShowId(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.showId = pValue

    def setShowStartLetter(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.showStartLetter = pValue

    def setTitle(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.title = pValue

    def setDescription(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.description = pValue

    def setExcludeTitle(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.excludeTitle = pValue

    def setMinLength(self, pValue):
        pValue = self.convertToNumber(pValue)
        self.minLength = pValue

    def setIgnoreTrailer(self, pValue):
        self.ignoreTrailer = 1 if self.convertToBoolean(pValue) else 0

    def setMaxResults(self, pValue):
        self.maxResults = self.convertToNumber(pValue)

    def setExactMatchForShow(self, pValue):
        self.exactMatchForShow = 1 if self.convertToBoolean(pValue) else 0

    def setRecentOnly(self, pValue):
        self.recentOnly = 1 if self.convertToBoolean(pValue) else 0

    def setWhen(self, pValue):
        self.when = pValue

    #
    ##################################
    #
    def convertToNumber(self, pValue, pNoneValue=0):
        rtValue = None
        if pValue == None:
            rtValue = pNoneValue
        elif type(pValue) == int or type(pValue) == float:
            rtValue = pValue
        elif pValue == '':
            rtValue = 0
        elif not(pValue.isnumeric()):
            rtValue = 0
        else:
            rtValue = int(pValue)
        return rtValue

    def convertToBoolean(self, pValue, pNoneValue=False):
        rtValue = None
        if pValue == None:
            rtValue = pNoneValue
        elif type(pValue) == bool:
            rtValue = pValue
        elif (type(pValue) == int or type(pValue) == float) and pValue == 0:
            rtValue = False
        elif (type(pValue) == int or type(pValue) == float) and pValue == 1:
            rtValue = True
        elif pValue == '':
            rtValue = False
        elif pValue == '1':
            rtValue = True
        elif pValue == '0':
            rtValue = False
        else:
            rtValue = pNoneValue
        return rtValue

    #
    ##################################
    #
    def generateRecentCondition(self):
        sql = ""
        if self.isRecentOnly():
            sql = "( ( UNIX_TIMESTAMP() - {} ) <= {} )".format(
                "aired" if self.settings.getRecentMode() == 0 else "dtCreated",
                self.settings.getMaxAge()
            )
        return sql

    #
    def generateIgnoreTrailer(self):
        sql = ""
        if self.isIgnoreTrailer():
            sql += "( aired < UNIX_TIMESTAMP() )"
        return sql

    #
    def generateMinLength(self):
        sql = ""
        if self.getMinLength() > 0:
            sql += '( duration >= %d )' % (self.getMinLength() * 60)
        return sql

    #
    def generateMaxRows(self):
        sql = ""
        if (self.getMaxResults() > 0):
            sql += 'LIMIT ' + self.getMaxResultsAsString()
        return sql

    #
    #
    #
    def generateChannel(self):
        sql = ""
        params = []
        if (len(self.getChannel()) > 0):
            sql += '( channel in ('
            for conditionString in self.getChannel():
                sql += '?,'
                params.append(conditionString)
            sql = sql[0:-1]
            sql += '))'
        return (sql, params)

    #
    def generateExclude(self):
        sql = ""
        params = []
        if (len(self.getExcludeTitle()) > 0):
            sql += '('
            for conditionString in self.getExcludeTitle():
                exp = '%' + conditionString + '%'
                params.append(exp)
                params.append(exp)
                sql += ' title not like ? and showname not like ? and'
            sql = sql[0:(len(sql) - 3)]
            sql += ")"
        return (sql, params)

    #
    def generateShowTitleDescription(self):
        sql = ""
        params = []
        if (len(self.getShow()) > 0 and not(self.isExactMatchForShow())) or len(self.getTitle()) > 0 or len(self.getDescription()) > 0:
            sql += ' ('
            if (len(self.getShow()) > 0 and not(self.isExactMatchForShow())):
                for conditionString in self.getShow():
                    exp = '%' + conditionString + '%'
                    params.append(exp)
                    sql += ' showname like ? or'
            #
            if (len(self.getTitle()) > 0):
                for conditionString in self.getTitle():
                    exp = '%' + conditionString + '%'
                    params.append(exp)
                    sql += ' title like ? or'
            #
            if (len(self.getDescription()) > 0):
                for conditionString in self.getDescription():
                    exp = '%' + conditionString + '%'
                    params.append(exp)
                    sql += ' description like ? or'
            #
            if sql[-2:] == 'or':
                sql = sql[0:(len(sql) - 2)]
            sql += ')'
        return (sql, params)

    #
    def generateShow(self):
        sql = ""
        params = []
        if (len(self.getShow()) > 0 and self.isExactMatchForShow()):
            sql += '( showname in ('
            for conditionString in self.getShow():
                sql += '?,'
                params.append(conditionString)
            sql = sql[0:-1]
            sql += '))'
        return (sql, params)

    #
    def generateShowId(self):
        sql = ""
        params = []
        if (len(self.getShowId()) > 0):
            sql += '( showId in ('
            for conditionString in self.getShowId():
                sql += '?,'
                params.append(conditionString)
            sql = sql[0:-1]
            sql += '))'
        return (sql, params)

    #
    def generateShowStartLetter(self):
        sql = ""
        params = []
        if (len(self.getShowStartLetter()) > 0):
            sql += "( CASE WHEN SUBSTR(showname,1,1) between 'A' and 'Z' THEN SUBSTR(showname,1,1) WHEN SUBSTR(showname,1,1) between '0' and '9' THEN '0' ELSE '#' END in ("
            for conditionString in self.getShowStartLetter():
                sql += '?,'
                params.append(conditionString)
            sql = sql[0:-1]
            sql += '))'
        return (sql, params)

    #
    ################
    # serialize for json
    ################
    #
    def getCacheKey(self):
        return 'C' + self.getChannelAsString() + \
            'S' + self.getShowAsString() + \
            'SID' + self.getShowIdAsString() + \
            'L' + self.getShowStartLetterAsString() + \
            'T' + self.getTitleAsString() + \
            'D' + self.getDescriptionAsString() + \
            'E' + self.getExcludeTitleAsString() + \
            'L' + self.getMinLengthAsString() + \
            'F' + self.getIgnoreTrailerAsString() + \
            'M' + self.getMaxResultsAsString() + \
            'N' + self.getExactMatchForShowAsString() + \
            'R' + self.getRecentOnlyAsString()

    #
    def toDict(self):
        return {
            "id" : self.id,
            "name" : self.name,
            "channel" : self.channel,
            "title" : self.title,
            "show" : self.show,
            "showId" : self.showId,
            "description" : self.description,
            "excludeTitle" : self.excludeTitle,
            "minLength" : self.minLength,
            "ignoreTrailer" : self.ignoreTrailer,
            "maxResults" : self.maxResults,
            "exactMatchForShow" : self.exactMatchForShow,
            "recentOnly" : self.recentOnly,
            "when" : self.when
            }

    def fromDict(self, aObject):
        self.id = aObject["id"]
        self.name = aObject["name"]
        self.channel = aObject["channel"]
        self.title = aObject["title"]
        self.show = aObject["show"]
        self.showId = aObject["showId"]
        self.description = aObject["description"]
        self.excludeTitle = aObject["excludeTitle"]
        self.minLength = aObject["minLength"]
        self.ignoreTrailer = aObject["ignoreTrailer"]
        self.maxResults = aObject["maxResults"]
        self.exactMatchForShow = aObject["exactMatchForShow"]
        self.recentOnly = aObject["recentOnly"]
        self.when = aObject["when"]
        return self

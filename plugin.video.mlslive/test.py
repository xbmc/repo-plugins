#!/usr/bin/python

import mlslive, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option('-g', '--game', type='string', dest='game',
                  help="Game to display")
parser.add_option('-l', '--list-weeks', action='store_true', dest='weeks',
                  help='List weeks')
parser.add_option('-w', '--week', type='string', dest='week',
                  help="List games of the week")
parser.add_option('-o', '--offset', type='int', dest='offset', default=0,
                  help="Week offset (from present)")
parser.add_option('-c', '--channel', type='string', dest='channel',
                  help="List channel (with no value) or channel contents")

(options, args) = parser.parse_args()

if options.user == None:
    print "ERROR: please specify a username (call with -h for help)"
    sys.exit(1)
elif options.password == None:
    print "ERROR: please specify a password (call with -h for help)"
    sys.exit(1)


my_mls = mlslive.MLSLive()


if not my_mls.login(options.user, options.password):
    print "Unable to authenticte with MLS live. please set username and password."
    sys.exit(1)

# my_mls.getGames(values['week']):

if options.weeks:
    weeks = my_mls.getWeeks()
    for week in sorted(weeks.keys()):
        print "'" + weeks[week] + "'"
    sys.exit()
if options.week != None:
    weeks = my_mls.getWeeks()
    for wkey in weeks.keys():
        if weeks[wkey] == options.week:
            week_url = wkey

    if not week_url == None: 
        print week_url
        games = my_mls.getGames(week_url)
        for game in games:
            print game['gameID'] + " " + my_mls.getGameString(game, "vs")
    sys.exit()
elif options.channel == None:
    print "Video Channels:"
    """
    channels = my_mls.getVideoChannels()
    for channel in channels:
        print '\t' + channel['channelID'] + ') ' + channel['name']
    """
else:
    videos = my_mls.getChannelVideos(options.channel)
    for video in videos:
        print video['clipID'] + ') ' + video['title']
    sys.exit()

if options.game != None:

    # get the games again :( (in the plugin we don't actually do this)
    print my_mls.getGameLiveStream(options.game)
    sys.exit(0)
    """
    games = my_mls.getGames(options.offset)
    game = None
    for g in games:
        if g['gameID'] == options.game:
            game = g
            break

    if game == None:
        print "ERROR: Unable to find game"
        sys.exit(1)

    # get the streams
    if my_mls.isGameLive(game):
        stream = my_mls.getGameLiveStream(options.game)
        print stream
    elif not my_mls.isGameUpcoming(game):
        streams = my_mls.getFinalStreams(options.game)
        for key in streams.keys():
            print my_mls.adjustArchiveString(my_mls.getGameString(game, "at"), key)
            print '\t' + streams[key] + '\n'
    else:
        print "Game is still upcoming"

    sys.exit(0)
    """
week_uri = my_mls.getCurrentWeekURI()
games = my_mls.getGames(week_uri)
teams = my_mls.getTeams()

for game in games:

    print game['gameID'] + ": " + my_mls.getGameString(game, "at").decode('utf-8')


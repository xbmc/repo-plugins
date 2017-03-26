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
parser.add_option('-m', '--month', type='string', dest='month',
                  help="List games of the month")
parser.add_option('-x', '--x-forward-for', type='string', dest='xff',
                  help="X-Forward-For header value")
parser.add_option('-c', '--clubs', action='store_true', dest='clubs',
                  help="List clubs")

(options, args) = parser.parse_args()


my_mls = mlslive.MLSLive()

if options.clubs:
    clubs = my_mls.getClubs()
    if clubs == None:
        print "Unable to get clubs"
        sys.exit(1)
    for club in clubs:
        if club['isMLS']:
            print "{0}) {1}".format(club['id'], club['name']['full'])

    sys.exit(0)

if options.user != None and options.password != None:
    if not my_mls.login(options.user, options.password, options.xff):
        print "*** Unable to authenticte with MLS live. please set username and password."
        sys.exit(1)
    else:
        print "Logon successful..."

if options.game == None:
    games = my_mls.getGames(xff = options.xff)

    if games == None:
        print "ERROR: Unable to get games list"
        sys.exit(1)

    for game in games:
        game_str = my_mls.getGameString(game, '{1} at {0}')
        print '\t{0}) {1}'.format(game['optaId'], game_str) 
else:
    streams = my_mls.getStreams(options.game, options.xff)
    if streams == None:
        print "Unable to get streams..."
        sys.exit(1)

    print streams

    # just choose the first stream for testing purposes
    media = streams[0]
    try:
        streams = my_mls.getStreamURIs(media, options.xff)
    except RuntimeError as ex:
        print "'{0}'".format(str(ex)[:12])
        sys.exit(1)

    if streams == None:
        print "Unable to get stream uris..."
        sys.exit(1)

    for stream in streams.keys():
        print stream + ' ' + streams[stream]
    stream = streams['6000000']
    details = stream.split('|')
    ffmpeg_fmt = '-headers "Authorization: {0}" -user_agent "{1}" {2}'
    print ffmpeg_fmt.format(details[1].split('&')[1].split('=')[1],
                            details[1].split('&')[0].split('=')[1],
                            details[0])
sys.exit(0)

#!/usr/bin/python

import mlslive, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option("-g", "--game", type='string', dest='game',
                  help="Game to display")
parser.add_option("-o", "--offset", type='int', dest='offset', default=0,
                  help="Week offset (from present)")

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

if options.game != None:

    # get the games again :( (in the plugin we don't actually do this)
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

print "OFfset = " + str(options.offset)
#games = my_mls.getGames()
games = my_mls.getGames(options.offset)
teams = my_mls.getTeams()

for game in games:

    print game['gameID'] + ": " + my_mls.getGameString(game, "at") 


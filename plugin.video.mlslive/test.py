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

(options, args) = parser.parse_args()

if options.user == None:
    print "ERROR: please specify a username (call with -h for help)"
    sys.exit(1)
elif options.password == None:
    print "ERROR: please specify a password (call with -h for help)"
    sys.exit(1)


my_mls = mlslive.MLSLive()

if not my_mls.login(options.user, options.password):
    print "*** Unable to authenticte with MLS live. please set username and password."
    sys.exit(1)
else:
    print "*** Logon successful"

if options.month:
    # print the months games
    for game in my_mls.getGames(options.month):
        print game['id'] + ') ' + my_mls.getGameString(game, "at")
        if 'cpp' in game.keys():
            print '\t' + game['cpp']
elif options.game != None:
    # get the games again :( (in the plugin we don't actually do this)
    print my_mls.getGameLiveStream(options.game)


    sys.exit(0)


sys.exit(0)

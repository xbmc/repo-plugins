#!/usr/bin/python
import sys, snnow
from cookies import Cookies
from optparse import OptionParser

# parse the options
parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option('-i', '--id', type='int', dest='id',
                  help="Channel ID")

(options, args) = parser.parse_args()

if not options.user:
    print "ERROR: Please specify user name.\n"
    parser.print_help()
    sys.exit(1)
elif not options.password:
    print "ERROR: Please specify a pasword\n"
    parser.print_help()
    sys.exit(1)

sn = snnow.SportsnetNow()
channels = sn.getChannels()
abbr = None

print options.id
print channels

for channel in  channels:

    if options.id:
        if options.id == channel['id']:
            abbr = channel['abbr']

    print str(channel['id']) + ') ' + channel['name'] + ' (' + \
          channel['abbr'] + ')'

if abbr:
    sn.authorize(options.user, options.password)
    stream = sn.getChannel(options.id, abbr)
    if stream:
        print stream
    else:
        print "Unable to get stream"
    
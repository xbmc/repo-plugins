#!/bin/bash

# Prevent loading two or more tabs due to LIRC still being enabled in XBMC / KODI
CHROME_STARTED=`ps -ef | grep google | grep chrome | grep -v "grep" | wc -l`
if [ $CHROME_STARTED -gt 0 ]; then
	exit 1;
fi

# lets find out if irxevent actually exist before we try to call them.
command -v irxevent >/dev/null 2>&1
IRXEVENT=$?

if [ $IRXEVENT -eq 0 ]; then
	killall irxevent >/dev/null 2>&1
fi

# http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $IRXEVENT -eq 0 ]; then
	irxevent -d $DIR/netflix.lirc &
else
	echo "irxevent is not installed, can't do remote control"	
fi

/usr/bin/google-chrome "$@" &
CHROME_PID=$!

# wait for google-chrome to be killed before killing irxevent below. 
wait $CHROME_PID

if [ $IRXEVENT -eq 0 ]; then
	killall irxevent >/dev/null 2>&1
fi


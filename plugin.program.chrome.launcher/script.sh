#!/bin/bash
openbox &
/usr/bin/google-chrome "$@" &
wait %2
kill %1
#!/bin/bash
DIR=plugin.video.espn_3
cd ..
zip -r plugin.video.espn_3.zip $DIR -x $DIR/.git/\* -x $DIR/bugs/\* -x $DIR/\*.pyo -x $DIR/\*.pyc -x $DIR/.idea/\*

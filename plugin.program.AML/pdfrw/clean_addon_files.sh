#!/bin/bash
#
# Clean uneeded files to pack addon ZIP for release.
#
echo "Cleaning pyo files"
find -name '*.pyo' -print -exec rm '{}' ';'
echo "Cleaning pyc files"
find -name '*.pyc' -print -exec rm '{}' ';'

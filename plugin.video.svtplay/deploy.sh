#!/bin/bash

# Use this script to deploy to the XBMC/Kodi
# plugins repo.

if [ "$#" -ne 1 ]; then
  echo "Missing argument for deploy dir!"
  echo "Usage: deploy.sh /my/dir/repo-plugins/plugin.video.svtplay/"
  exit 1
fi

if [ ! -d "$1" ]; then
  echo "Directory $1 does not exist!"
  exit 1
fi

# Exit on error
set -e

echo "Deploying to $1"
DEPLOY_DIR=$1

EXCLUDED_FILES="deploy.sh \
              .gitignore \
              __pycache__ \
              .vscode \
              .travis.yml \
              requirements.txt \
              ISSUE_TEMPLATE.md \
              CONTRIBUTING.md"

FILES=`git ls-files`

for FILE in $FILES; do
  if [[ $EXCLUDED_FILES =~ $FILE ]]; then
    echo "Skipping excluded file $FILE"
    continue
  fi
  if [[ $FILE == *"tests"* ]]; then
    echo "Skipping test file $FILE"
    continue
  fi
  echo "Copying $FILE to $DEPLOY_DIR$FILE"
  cp --parent $FILE $DEPLOY_DIR
done

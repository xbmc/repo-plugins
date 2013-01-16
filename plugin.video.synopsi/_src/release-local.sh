PROJECT_FOLDER=$1

INCLUDED_IN="`dirname \"$0\"`"
INCLUDED_IN="`( cd \"$INCLUDED_IN\" && pwd )`"
INCLUDED_IN="`dirname \"$INCLUDED_IN\"`"
BASE_NAME="`basename \"$INCLUDED_IN\"`"
TARGET_DIR="`dirname \"$INCLUDED_IN\"`"

echo $INCLUDED_IN, $BASE_NAME

: ${PROJECT_FOLDER:="$BASE_NAME"}

cd $TARGET_DIR
pwd

rm ${PROJECT_FOLDER}-local*.zip
zip -x ${PROJECT_FOLDER}/_src/\* ${PROJECT_FOLDER}/tests/\* \*.pyc -Z store -r ${PROJECT_FOLDER}-local.zip ${PROJECT_FOLDER}/*
RANDSTR=`tr -dc "0-9" < /dev/urandom | head -c 3`

NEWNAME="${PROJECT_FOLDER}-local-$RANDSTR.zip"

echo $NEWNAME
cp ${PROJECT_FOLDER}-local.zip $NEWNAME



# Where Are You

## About

Where Are You is a plugin for Kodi that accepts a URL from a stream file and then displays a dialog box with the title and message from the stream file URL.  After the dialog is dismissed a black video plays for 2 seconds.  This is basically to do what the media stub file does (which is display a title and a message for a given file), but for streaming files because the media stub only works if you have an optical drive attached to the device running Kodi.

## Usage

The stream file is just a text file with a URL in it.  The format of the URL is:

```
    plugin://plugin.whereareyou?empty=pad&title=Available+streaming&message=This+is+available+via+the+Netflix+app+on+the+TV
```

The stream file should be named in a way that Kodi can scrape it as a TV show:

```
    My.TV.Show.S01.E01.My.Episode.strm
```
or a movie:

```
    My.Great.Movie (2020).strm
```

Place the stream file in a location you have defined as a source and then scan the stream files into your library. Now when you play them you'll get a dialog box telling you were to find the TV show or movie (like the Disney+ app on your Smart TV).

## Generating the Stream Files

I also wrote a little python3 command line tool to generate the stream files.  That command line tool is available at:

<https://github.com/pkscout/create.kodi.mediastubs/releases/>

## Credits

The icon is Compass by Diane from the Noun Project.
# Where Are You

## About

Where Are You is a plugin for Kodi that accepts a URL from a stream file and then displays a dialog box with the title and message from the stream file URL.  After the dialog is dismissed a black video plays for 2 seconds.  This is basically to do what the media stub file does (which is display a title and a message for a given file), but for streaming files because the media stub only works if you have an optical drive attached to the device running Kodi.

## Usage

### Standard

The stream file is just a text file with a URL in it.  The format of the URL is:

```
    plugin://plugin.whereareyou?empty=pad&title=Available+streaming&message=This+is+available+via+the+Netflix+app+on+the+TV
```

### Deep Linking with AppleTV and Home Assistant

If you are using an AppleTV as your streaming device and Home Assistant control, you can include a URL in the streaming file to directly launch the episode or movie.  This doesn't work on every streaming service, but it does for a bunch of them.  For more details on this and how to get the URL, see the [Home Assistant AppleTV integration documention](https://www.home-assistant.io/integrations/apple_tv) and look for the section on deep links.

You'll need to create a script called "Launch Streaming Video."  Make sure it has an entity ID of `script.launch_streaming_video`.  This is the script:

```
alias: Launch Streaming Video
fields:
  the_url:
    description: The URL to the episode or movie
    example: https://www.disneyplus.com/video/afdc98f1-26bf-48d8-8866-af185ba5d5ac
sequence:
  - service: media_player.play_media
    data:
      media_content_type: url
      media_content_id: "{{ the_url }}"
    target:
      device_id: <CHANGE TO THE DEVICE ID FOR YOUR APPLETV>
mode: single
icon: mdi:television
```

The URL for the streaming file needs one more thing, the_url passed as an argument, like this:

```
    plugin://plugin.whereareyou?empty=pad&title=Available+Streaming&message=Available+on+Disney%2B&the_url=https://www.disneyplus.com/video/618050a1-5dbf-4b4f-91ca-3299fb077be1
```

## Naming

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
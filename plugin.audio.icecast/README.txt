GENERAL

This is a simple XBMC add-on to listen to IceCast online radio stations.

It is mostly based on the original SHOUTcast add-on. Some additional reserch and coding by <assen.totin@gmail.com>


INSTALL

Move the "plugin.audio.icecast" directory into your "addons" directory. Restart XBMC.


NOTES

1. A note on genres: with IceCast, each server lists one or more words as its "genre". Two approaches are possible:
- Treat each string as a whole category name; I don't like this, because "pop rock" and "rock pop" will appear as two different genres
- Split each string into words and use each word as a separate category; this way, "pop" and "rock" will appear only once, but most stations will apear in more than one genre. This
 is the current behaviour.

2. To speed up processing and decrease network load (the full IceCast XML is over 3 MB), the add-on sets up a local cache file. When you first run the add-on, it gets the XML from the IceCast server; it is then cached and reused until you quit the add-on.

3. Some IceCast radio stations obviously feed broken UTF-8 in their names and genres - there's nothing to do about it, complain to the radio station.

4. The client-side search (as server-side seems unavailable with IceCast) searches in both genres and server names


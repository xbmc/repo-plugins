GENERAL

This is a simple XBMC add-on to listen to IceCast online radio stations.

It is based on the original SHOUTcast add-on. Icecast-specific reserch and coding as well as SQLite support by <assen.totin@gmail.com>


INSTALL

The add-on is available in the official XBMC repository. 

If you still want to install manually, move the "plugin.audio.icecast" directory into your "addons" directory. 


TECHNICAL NOTES

1. A note on genres: with IceCast, each server lists one or more words as its "genre". Two approaches are possible:
- Treat each string as a whole category name; I don't like this, because "pop rock" and "rock pop" will appear as two different genres
- Split each string into words and use each word as a separate category; this way, "pop" and "rock" will appear only once, but most stations will apear in more than one genre. This
 is the current behaviour.

2. To speed up processing and decrease network load (the full IceCast XML is over 3 MB with around 10,000 streams), the add-on sets up a local cache. If SQLite is available (as with standard Ubuntu release), it will be used since it is faster. If SQLite is not available, a text file will be used instead; this is slower, but still better than getting the XML off the Internet every time. The cache is updated if it is more than 1 day old. 

3. Some IceCast radio stations obviously feed broken UTF-8 in their names and genres - there's nothing to do about it, complain to the radio station. More on the investigation of the issue here: http://bilbo.online.bg/~assen/icecast-addon/unicode.htm

4. The client-side search (as server-side seems unavailable with IceCast) searches in both genres and server names


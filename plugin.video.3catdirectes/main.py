import xbmcplugin
import xbmcgui
import xbmc

# Diccionari amb els fluxos M3U8
# URLs dels fluxos M3U8
streams = {
    "TV3":      {"https://directes3-tv-cat.3catdirectes.cat/live-content/tv3-hls/master.m3u8"},
    "3/24":     {"https://directes-tv-int.3catdirectes.cat/live-content/canal324-hls/master.m3u8"},
    "Esport 3": {"https://directes-tv-cat.3catdirectes.cat/live-content/esport3-hls/master.m3u8"},
    "SX3":      {"https://directes-tv-cat.3catdirectes.cat/live-content/super3-hls/master.m3u8"},
    "33":       {"https://directes-tv-cat.3catdirectes.cat/live-content/c33-super3-hls/master.m3u8"}
}


# Create a gUI with a table with the available channels
def show_stream_choices():

    dialog = xbmcgui.Dialog()

    # Grab the table items, which are the channel names from the streams dict keys 
    stream_names = list(streams.keys())
    # Show the menu with the options
    choice = dialog.select("Tria un flux per reproduir", stream_names)
    if choice != -1:  # If not cancel
        stream_key = stream_names[choice]
        player = xbmc.Player()
        player.play(list(streams[stream_key])[0])


# Plugin entry point
if __name__ == "__main__":
    show_stream_choices()


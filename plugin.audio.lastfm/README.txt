info for skinners:
Window(Home).Property(LastFM.RadioPlaying)
Window(Home).Property(LastFM.CanLove)
Window(Home).Property(LastFM.CanBan)

LastFM.Love:
RunScript(plugin.audio.lastfm,action=LastFM.Love&amp;artist=$INFO[MusicPlayer.Artist]&amp;song=$INFO[MusicPlayer.Title])

LastFM.Ban:
RunScript(plugin.audio.lastfm,action=LastFM.Ban&amp;artist=$INFO[MusicPlayer.Artist]&amp;song=$INFO[MusicPlayer.Title]) 

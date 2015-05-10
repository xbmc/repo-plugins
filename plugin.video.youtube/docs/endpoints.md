# ENDPOINTS
## Videos
### Play a video via ID
####Syntax
```
plugin://plugin.video.youtube/play/?video_id=[VID]
```
####Example
https://www.youtube.com/watch?v=eWATHgcn2QE or https://youtu.be/eWATHgcn2QE
```
plugin://plugin.video.youtube/play/?video_id=eWATHgcn2QE
```

## Playlists
### Show videos of a playlist
```
plugin://plugin.video.youtube/playlist/[PID]/
```
### Default executing a playlist:
```
plugin://plugin.video.youtube/play/?playlist_id=[PID]
```
### Play a playlist in a predetermined order
```
plugin://plugin.video.youtube/play/?playlist_id=[PID]&order=[default|reverse|shuffle]
```
### Play a playlist with a starting video:
```
plugin://plugin.video.youtube/play/?playlist_id=[PID]&video_id=[VID]
```
## Channels
### Navigate to a channel via ID:
```
plugin://plugin.video.youtube/channel/[CID]/
```
### Navigate to a channel via username:
```
plugin://plugin.video.youtube/user/[NAME]/
```
## Search
```
plugin://plugin.video.youtube/search/?q=[URL_ENCODED_TEXT]
```

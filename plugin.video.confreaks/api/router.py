import urllib2
import json

from event import Event
from video import Video

class Router(object):
  @classmethod
  def events(cls):
    response = urllib2.urlopen('http://www.confreaks.tv/api/v1/events.json?sort=recent')
    return [Event(event) for event in json.load(response)]

  @classmethod
  def videos(cls, event_short_code):
    response = urllib2.urlopen('http://www.confreaks.tv/api/v1/events/%s/videos.json?sort=recent' % event_short_code)
    return [Video(video) for video in json.load(response)]

  @classmethod
  def video(cls, video_slug):
    response = urllib2.urlopen('http://www.confreaks.tv/api/v1/videos/%s.json' % video_slug)
    return Video(json.load(response))

class Video(object):
  def __init__(self, json):
    self.id = json['id']
    self.slug = json['slug']
    self.title = json['title']
    self.presenters = json['presenters']
    self.host = json['host']
    self.embed_code = json['embed_code']

  def presenter_names(self):
    return ', '.join(map(lambda p: p['first_name'] + ' ' + p['last_name'], self.presenters))

  def url(self):
    return 'plugin://plugin.video.%s/?action=play_video&videoid=%s' % (self.host, self.embed_code)

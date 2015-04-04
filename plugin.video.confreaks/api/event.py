from datetime import datetime, date

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

class Event(object):
  def __init__(self, json):
    self.display_name = json['display_name']
    self.short_code = json['short_code']
    self.conference = json['conference']
    self.start_at = datetime.strptime(json['start_at'], DATETIME_FORMAT)
    self.end_at = datetime.strptime(json['end_at'], DATETIME_FORMAT)

  # Format start date e.g. 'Jan 10'
  def pretty_start(self):
    return self.start_at.strftime('%b %d')

  # Format end date e.g. 'Jan 15'
  def pretty_end(self):
    return self.end_at.strftime('%b %d')

  # Format date range e.g. 'Jan 10 - Jan 15' or 'Jan 10' if only one day
  def pretty_range(self):
    if self.pretty_start() == self.pretty_end():
      return self.pretty_start()
    else:
      return '%s - %s' % (self.pretty_start(), self.pretty_end())

  def name(self):
    return self.display_name if self.display_name is not None else self.conference

  def code(self):
    return self.short_code.lower()

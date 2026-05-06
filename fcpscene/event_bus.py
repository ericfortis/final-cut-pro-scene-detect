class EventBus:
  def __init__(self):
    self._subs = {}

  def _subscribe(self, event, callback):
    self._subs.setdefault(event, []).append(callback)

  def _unsubscribe_all(self, event):
    if event in self._subs:
      del self._subs[event]

  def _emit(self, event, *args):
    for cb in self._subs.get(event, []):
      cb(*args)


  def emit_progress(self, *args):
    self._emit('DETECT.progress', *args)

  def subscribe_progress(self, callback):
    self._subscribe('DETECT.progress', callback)

  def unsubscribe_progress(self):
    self._unsubscribe_all('DETECT.progress')


  def emit_stop(self):
    self._emit('DETECT.stop')

  def subscribe_stop(self, callback):
    self._subscribe('DETECT.stop', callback)

  def unsubscribe_stop(self):
    self._unsubscribe_all('DETECT.stop')


  def emit_export_progress(self, *args):
    self._emit('EXPORT.progress', *args)

  def subscribe_export_progress(self, callback):
    self._subscribe('EXPORT.progress', callback)

  def unsubscribe_export_progress(self):
    self._unsubscribe_all('EXPORT.progress')

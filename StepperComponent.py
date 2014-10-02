from Push.PlayheadComponent import PlayheadComponent
from APCMessenger import APCMessenger
from MatrixMaps import PAD_FEEDBACK_CHANNEL

class StepperComponent(PlayheadComponent, APCMessenger):
  """ For a basic beats stepper. Sets own notes """
  def __init__(self, *a, **k):
    super(StepperComponent, self).__init__(*a, **k)
    self._on_song_is_playing_changed.subject = self.song()

  def set_buttons(self, buttons):
    self._buttons = buttons
    if buttons:
      for i, button in enumerate(buttons):
        button.set_channel(PAD_FEEDBACK_CHANNEL)
        button.set_identifier(50 + i)
        button.turn_off()
    self.update()

  @property
  def _track(self):
    if self.is_enabled() and self.song().is_playing:
      for track in self.song().tracks:
        if track.name == "Stepper":
          # Weird little hack to work around a bug in the C API
          # If we just return 'track' it doesn't work 
          return track.clip_slots[0].canonical_parent
    
  def update(self): 
    super(PlayheadComponent, self).update()
    if self._playhead:
      self._playhead.velocity = 127
      self._playhead.track = self._track
      if self._track and self._buttons:
        self._playhead.notes = self._calculated_notes
        self._playhead.wrap_around = False 
        self._playhead.start_time = 0.0
        self._playhead.step_length = 1.0

  @property
  def _calculated_notes(self):
    return [button._msg_identifier for button, (x, y) in self._buttons.iterbuttons()] 

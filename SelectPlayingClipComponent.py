from Push.SelectPlayingClipComponent import SelectPlayingClipComponent

class SelectPlayingClipComponent(SelectPlayingClipComponent):
  """ Customized to always select the playing clip """

  def on_selected_track_changed(self):
    if self.song().is_playing:
      self._go_to_playing_clip()

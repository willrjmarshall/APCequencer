from itertools import imap, ifilter
from _Framework.Util import find_if, first
from Push.DrumGroupComponent import DrumGroupComponent
from MatrixMaps import PAD_FEEDBACK_CHANNEL
from APCMessenger import APCMessenger

class APCDrumGroupComponent(DrumGroupComponent, APCMessenger):
  """ Customized to use its own feedback channel """

  def _update_control_from_script(self):
    """ Patched to use our own feedback channel """
    takeover_drums = self._takeover_drums or self._selected_pads
    profile = 'default' if takeover_drums else 'drums'
    if self._drum_matrix:
      for button, _ in ifilter(first, self._drum_matrix.iterbuttons()):
        button.set_channel(PAD_FEEDBACK_CHANNEL)
        button.set_enabled(takeover_drums)
        button.sensitivity_profile = profile

  def on_selected_track_changed(self):
    if self.song().view.selected_track.has_midi_input:
      self.set_enabled(True)
      self.update()
    else:
      self.set_enabled(False)

  def _update_drum_pad_leds(self):
    if (not self.is_enabled()) and self._drum_matrix:
      for button, (col, row) in ifilter(first, self._drum_matrix.iterbuttons()):
        button.set_light('DrumGroup.PadInvisible')
    else:
      super(APCDrumGroupComponent, self)._update_drum_pad_leds()

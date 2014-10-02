from itertools import imap, chain, starmap, izip, ifilter
from _Framework.Util import first
from _Framework.ClipCreator import ClipCreator
from _Framework.SubjectSlot import subject_slot, subject_slot_group
from _Framework.Layer import Layer 
from Push.StepSeqComponent import StepSeqComponent, DrumGroupFinderComponent
from Push.SkinDefault import make_default_skin 
from NoteSettings import NoteEditorSettingsComponent 
from APCDrumGroupComponent import APCDrumGroupComponent
from APCMessenger import APCMessenger
from MatrixMaps import PAD_FEEDBACK_CHANNEL
from APCNoteEditorComponent import APCNoteEditorComponent

class StepSeqComponent(StepSeqComponent, APCMessenger):
  """ Step sequencer for APC40 MkII """

  def __init__(self, *a, **k):
    super(StepSeqComponent, self).__init__(
        clip_creator = ClipCreator(),
        note_editor_settings = self._note_editor_setting(),
        is_enabled = False,
        skin = make_default_skin(),
        *a, **k)
    self._quant_buttons = None 
    self._drum_group.__class__ = APCDrumGroupComponent
    self._note_editor.__class__ = APCNoteEditorComponent
    self._setup_drum_group_finder()
    self._configure_playhead()


  def _select_track_by_name(self, name):
    for track in self.song().tracks:
      if track.name == name:
        self.song().view.selected_track = track

  def _note_editor_setting(self):
    return NoteEditorSettingsComponent(self.control_surface._grid_resolution,
        Layer(initial_encoders = self.control_surface._mixer_encoders),
        Layer(encoders = self.control_surface._mixer_encoders))

  def set_velocity_slider(self, button_slider):
    self._note_editor.set_velocity_slider(button_slider)

  def _configure_playhead(self):
    self._playhead_component._notes=tuple(chain(*starmap(range, (
         (28, 32),
         (20, 24),
         (12, 16),
         (4, 8)))))
    self._playhead_component._triplet_notes=tuple(chain(*starmap(range, (
         (28, 31),
         (20, 23),
         (12, 15),
         (4, 7)))))

  def _setup_drum_group_finder(self):
    self._drum_group_finder = DrumGroupFinderComponent()
    self._on_drum_group_changed.subject = self._drum_group_finder
    self._drum_group_finder.update()

  @subject_slot('drum_group')
  def _on_drum_group_changed(self):
    self.set_drum_group_device(self._drum_group_finder.drum_group)

  def on_selected_track_changed(self):
    self.set_drum_group_device(self._drum_group_finder.drum_group)
    self.update()

  def set_delete_button(self, button):
    if button:
      button.set_channel(PAD_FEEDBACK_CHANNEL)
    super(StepSeqComponent, self).set_delete_button(button)

  def set_quantization_buttons(self, buttons):
    """ When loaded, move the buttons to empty space on channel 15
    When unloaded reset them """
    if self._quant_buttons:
      self._quant_buttons.reset() # Reset quant buttons when released
    self._quant_buttons = buttons
    if buttons:
      for i, button in enumerate(buttons):
        if i > 3: # Only change second half's channel
          button.set_channel(PAD_FEEDBACK_CHANNEL - 1)
          button.set_identifier(100 + i)
    self._grid_resolution.set_buttons(buttons)

  def set_button_matrix(self, matrix):
    """ This method, as with most set_* methods, is called every time
    This component is enabled """
    self._note_editor_matrix = matrix
    self._update_note_editor_matrix()
    if matrix:
      self._select_track_by_name("Drums") # Select the drum track if we can
      for button, _ in ifilter(first, matrix.iterbuttons()):
        button.set_channel(PAD_FEEDBACK_CHANNEL)

  def set_loop_selector_matrix(self, matrix):
    self._loop_selector.set_loop_selector_matrix(matrix)
    if matrix:
      for button, _ in ifilter(first, matrix.iterbuttons()):
        button.set_channel(PAD_FEEDBACK_CHANNEL)

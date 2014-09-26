from __future__ import with_statement
import sys
from functools import partial
from contextlib import contextmanager

from _Framework.ModesComponent import ModesComponent, ImmediateBehaviour
from _Framework.Layer import Layer
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from _Framework.Dependency import inject
from _Framework.Util import const, recursive_map
from _Framework.Dependency import inject
from _Framework.ComboElement import ComboElement, DoublePressElement, MultiElement, DoublePressContext
from _Framework.ButtonMatrixElement import ButtonMatrixElement 
from _APC.APC import APC
from Push import Colors
from Push.PlayheadElement import PlayheadElement
from Push.NoteSettingsComponent import NoteEditorSettingsComponent
from Push.GridResolution import GridResolution

# Monkeypatch ControlElementUtils
import ControlElementUtils
sys.modules['_APC.ControlElementUtils'] = ControlElementUtils
from APC40_MkII.APC40_MkII import APC40_MkII, NUM_SCENES, NUM_TRACKS
from SkinDefault import make_rgb_skin, make_default_skin, make_stop_button_skin, make_crossfade_button_skin
from SessionComponent import SessionComponent
from StepSeqComponent import StepSeqComponent
from MatrixMaps import PAD_TRANSLATIONS, FEEDBACK_CHANNELS

class APCAdvanced_MkII(APC40_MkII):
  """ APC40Mk2 script with step sequencer mode """
  def __init__(self, *a, **k):
    APC.__init__(self, *a, **k)
    self._color_skin = make_rgb_skin()
    self._default_skin = make_default_skin()
    self._stop_button_skin = make_stop_button_skin()
    self._double_press_context = DoublePressContext()
    self._crossfade_button_skin = make_crossfade_button_skin()
    with self.component_guard():
      self._create_controls()
      self._create_bank_toggle()
      self._create_session()
      self._create_mixer()
      self._create_sequencer()
      self._create_session_mode()
      self._create_transport()
      self._create_device()
      self._create_view_control()
      self._create_quantization_selection()
      self._create_recording()
      self._create_m4l_interface()
      self._session.set_mixer(self._mixer)
    self.set_highlighting_session_component(self._session)
    self.set_device_component(self._device)
    self.set_pad_translations(PAD_TRANSLATIONS)
    self._device_selection_follows_track_selection = True
    self.set_feedback_channels(FEEDBACK_CHANNELS)

  def _create_controls():
    super(APCAdvanced_MkII, self)._create_controls()
    self._grid_resolution = GridResolution()
    double_press_rows = recursive_map(DoublePressElement, self._matrix_rows_raw) 
    self._double_press_matrix = ButtonMatrixElement(name='Double_Press_Matrix', rows=double_press_rows)
    self._double_press_event_matrix = ButtonMatrixElement(name='Double_Press_Event_Matrix', rows=recursive_map(lambda x: x.double_press, double_press_rows))

  def _create_session(self):
    """ Not assigning layers here, instead doing it via a ModeSelector """
    self._session = SessionComponent(NUM_TRACKS, NUM_SCENES, auto_name=True,
        is_enabled = False, enable_skinning = True)
    clip_color_table = Colors.CLIP_COLOR_TABLE.copy()
    clip_color_table[16777215] = 119 # What is this?
    self._session.set_rgb_mode(clip_color_table, Colors.RGB_COLOR_TABLE)
    self._session_zoom = SessionZoomingComponent(self._session, name='Session_Overview', 
        enable_skinning=True, is_enabled=False)

  def _create_mixer(self):
    """ As with _create_session, separating layer assignment so we have
    explicit control using ModeSelector """

  def _create_sequencer(self):
    self._sequencer = StepSeqComponent(grid_resolution = self._grid_resolution,
        note_editor_settings = self._note_editor_settings())

  def _create_session_mode(self): 
    """ Switch between Session and StepSequencer modes """
    self._session_mode = ModesComponent(name='Session_Mode', is_enabled = False)
    self._session_mode.default_behaviour = ImmediateBehaviour()
    self._session_mode.add_mode('session', self._session_mode_layers())
    self._session_mode.add_mode('session_2', self._session_mode_layers())
    self._session_mode.add_mode('sequencer', (self._sequencer, self._sequencer_layer()))
    self._session_mode.layer = Layer(session_button = self._pan_button,
        session_2_button = self._sends_button, sequencer_button = self._user_button)
    #self._session_mode.selected_mode = "session"
    self._session_mode.selected_mode = "sequencer"

  def _session_mode_layers(self):
    return [ (self._session, self._session_layer()),
      (self._session_zoom, self._session_zoom_layer())]

  def _sequencer_layer(self):
    return Layer(
        drum_matrix = self._session_matrix.submatrix[:4, 1:5],
        button_matrix = self._double_press_matrix.submatrix[4:8, 1:5],
        select_button = self._user_button,
        delete_button = self._stop_all_button,
        playhead = self._playhead(),
        quantization_buttons = self._stop_buttons,
        shift_button = self._shift_button,
        loop_selector_matrix = self._double_press_matrix.submatrix[:8, :1],
        short_loop_selector_matrix = self._double_press_event_matrix.submatrix[:8, :1],
        drum_bank_up_button = self._up_button,
        drum_bank_down_button = self._down_button)

  def _mixer_layer(self):
    pass

  def _session_layer(self):
    def when_bank_on(button):
      return self._bank_toggle.create_toggle_element(on_control=button)
    def when_bank_off(button):
      return self._bank_toggle.create_toggle_element(off_control=button)
    return Layer(
      track_bank_left_button = when_bank_off(self._left_button), 
      track_bank_right_button = when_bank_off(self._right_button), 
      scene_bank_up_button = when_bank_off(self._up_button), 
      scene_bank_down_button = when_bank_off(self._down_button), 
      page_left_button = when_bank_on(self._left_button), 
      page_right_button = when_bank_on(self._right_button), 
      page_up_button = when_bank_on(self._up_button), 
      page_down_button = when_bank_on(self._down_button), 
      stop_track_clip_buttons = self._stop_buttons,
      stop_all_clips_button = self._stop_all_button, 
      scene_launch_buttons = self._scene_launch_buttons, 
      clip_launch_buttons = self._session_matrix)

  def _session_zoom_layer(self):
    return Layer(button_matrix=self._shifted_matrix, 
      nav_left_button=self._with_shift(self._left_button), 
      nav_right_button=self._with_shift(self._right_button), 
      nav_up_button=self._with_shift(self._up_button), 
      nav_down_button=self._with_shift(self._down_button), 
      scene_bank_buttons=self._shifted_scene_buttons)

  def _note_editor_settings(self):
    return NoteEditorSettingsComponent(self._grid_resolution, 
        Layer(initial_encoders=self._mixer_encoders, 
          priority=consts.MODAL_DIALOG_PRIORITY), 
        Layer(encoders=self._mixer_encoders, 
          priority=consts.MODAL_DIALOG_PRIORITY))

  def _playhead(self):
    return PlayheadElement(self._c_instance.playhead)

  # EVENT HANDLING FUNCTIONS
  def reset_controlled_track(self):
    self.set_controlled_track(self.song().view.selected_track)
  
  def update(self):
    self.reset_controlled_track()
    super(APCAdvanced_MkII, self).update()

  def _on_selected_track_changed(self):
    self.reset_controlled_track()
    super(APCAdvanced_MkII, self)._on_selected_track_changed()

  @contextmanager
  def component_guard(self):
    """ Customized to inject additional things """
    with super(APCAdvanced_MkII, self).component_guard():
      with self.make_injector().everywhere():
        yield

  def make_injector(self):
    """ Adds some additional stuff to the injector, used in BaseMessenger """
    return inject(
      double_press_context = const(self._double_press_context),
      control_surface = const(self),
      log_message = const(self.log_message))

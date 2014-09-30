from __future__ import with_statement
import sys
from functools import partial
from contextlib import contextmanager

from _Framework.ModesComponent import ModesComponent, ImmediateBehaviour
from _Framework.Layer import Layer
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from _Framework.Dependency import inject
from _Framework.Util import const, recursive_map, find_if
from _Framework.Dependency import inject
from _Framework.ComboElement import ComboElement, DoublePressElement, MultiElement, DoublePressContext
from _Framework.ButtonMatrixElement import ButtonMatrixElement 
from _Framework.SubjectSlot import subject_slot
from _Framework.Resource import PrioritizedResource
from _APC.APC import APC
from Push import Colors
from Push.PlayheadElement import PlayheadElement
from Push.GridResolution import GridResolution
from Push.AutoArmComponent import AutoArmComponent

# Monkeypatch things
import ControlElementUtils
import SessionComponent
import SkinDefault
sys.modules['_APC.ControlElementUtils'] = ControlElementUtils
sys.modules['_APC.SessionComponent'] = SessionComponent
sys.modules['_APC.SkinDefault'] = SkinDefault

from APC40_MkII.APC40_MkII import APC40_MkII, NUM_SCENES, NUM_TRACKS
from SkinDefault import make_rgb_skin, make_default_skin, make_stop_button_skin, make_crossfade_button_skin
from SessionComponent import SessionComponent
from StepSeqComponent import StepSeqComponent
from MatrixMaps import PAD_TRANSLATIONS, FEEDBACK_CHANNELS
from ButtonSliderElement import ButtonSliderElement
from PPMeter import PPMeter
from RepeatComponent import RepeatComponent
from SelectPlayingClipComponent import SelectPlayingClipComponent

class APCAdvanced_MkII(APC40_MkII):
  """ APC40Mk2 script with step sequencer mode """
  def __init__(self, *a, **k):
    self._double_press_context = DoublePressContext()
    APC40_MkII.__init__(self, *a, **k)
    with self.component_guard():
      self._create_sequencer()
      self._create_repeats()
      #self._init_auto_arm()
      self._init_select_playing_clip()
      self._create_ppm()
      self._create_session_mode()
    self.set_pad_translations(PAD_TRANSLATIONS)
    self.set_feedback_channels(FEEDBACK_CHANNELS)
  
  def _create_controls(self):
    """ Add some additional stuff baby """
    super(APCAdvanced_MkII, self)._create_controls()
    self._grid_resolution = GridResolution()
    self._velocity_slider = ButtonSliderElement(tuple(self._scene_launch_buttons_raw[::-1])) 
    double_press_rows = recursive_map(DoublePressElement, self._matrix_rows_raw) 
    self._double_press_matrix = ButtonMatrixElement(name='Double_Press_Matrix', rows=double_press_rows)
    self._double_press_event_matrix = ButtonMatrixElement(name='Double_Press_Event_Matrix', rows=recursive_map(lambda x: x.double_press, double_press_rows))
    self._playhead = PlayheadElement(self._c_instance.playhead)
    # Make these prioritized resources, which share between Layers() equally
    # Rather than building a stack
    self._pan_button._resource_type = PrioritizedResource 
    self._user_button._resource_type = PrioritizedResource 
    for button in self._scene_launch_buttons_raw:
      button._resource_type = PrioritizedResource

  def _create_repeats(self):
    self._repeats = RepeatComponent(is_enabled = False, layer = Layer(
      parameter_buttons = self._scene_launch_buttons))
    self._repeats.set_device(find_if(lambda d: d.name == 'Repeats', self.song().master_track.devices)) 

  def _create_ppm(self):
    self._ppm = PPMeter(self.song().master_track)
    self._ppm_layer = Layer(target_matrix = ButtonMatrixElement(rows=[self._scene_launch_buttons_raw[::-1]])) 

  def _create_session(self):
    """ Overridden to remove scene launches """
    def when_bank_on(button):
      return self._bank_toggle.create_toggle_element(on_control=button)
    def when_bank_off(button):
      return self._bank_toggle.create_toggle_element(off_control=button)
    super(APCAdvanced_MkII, self)._create_session()
    self._session.layer=Layer(track_bank_left_button=when_bank_off(self._left_button), 
          track_bank_right_button=when_bank_off(self._right_button), 
          scene_bank_up_button=when_bank_off(self._up_button),
          scene_bank_down_button=when_bank_off(self._down_button), 
          page_left_button=when_bank_on(self._left_button), 
          page_right_button=when_bank_on(self._right_button), 
          page_up_button=when_bank_on(self._up_button), 
          page_down_button=when_bank_on(self._down_button), 
          stop_track_clip_buttons=self._stop_buttons, 
          stop_all_clips_button=self._stop_all_button, 
          clip_launch_buttons=self._session_matrix)

  def _create_sequencer(self):
    self._sequencer = StepSeqComponent(grid_resolution = self._grid_resolution)

  def _create_session_mode(self): 
    """ Switch between Session and StepSequencer modes """
    self._session_mode = ModesComponent(name='Session_Mode', is_enabled = False)
    self._session_mode.default_behaviour = ImmediateBehaviour()
    self._session_mode.add_mode('session', self._session_mode_layers())
    self._session_mode.add_mode('session_2', self._session_mode_layers())
    self._session_mode.add_mode('sequencer', self._sequencer_mode_layers())
    self._session_mode.layer = Layer(
        session_button = self._pan_button,
        session_2_button = self._sends_button, 
        sequencer_button = self._user_button)
    self._session_mode.selected_mode = "session"

  def _session_mode_layers(self):
    return [ self._session, self._session_zoom, (self._ppm, self._ppm_layer), self._select_playing_clip]

  def _sequencer_mode_layers(self):
    return [
      self._select_playing_clip,
      (self._sequencer, self._sequencer_layer())]

  def _sequencer_layer(self):
    return Layer(
        velocity_slider = self._velocity_slider,
        drum_matrix = self._session_matrix.submatrix[:4, 1:5],
        button_matrix = self._double_press_matrix.submatrix[4:8, 1:5],
        select_button = self._user_button,
        delete_button = self._stop_all_button,
        playhead = self._playhead,
        quantization_buttons = self._stop_buttons,
        shift_button = self._shift_button,
        loop_selector_matrix = self._double_press_matrix.submatrix[:8, :1],
        short_loop_selector_matrix = self._double_press_event_matrix.submatrix[:8, :1],
        drum_bank_up_button = self._up_button,
        drum_bank_down_button = self._down_button)

  def _init_auto_arm(self):
    self._auto_arm = AutoArmComponent(is_enabled = True)

  def _init_select_playing_clip(self):
    self._select_playing_clip = SelectPlayingClipComponent(name='Select_Playing_Clip', 
        playing_clip_above_layer=Layer(action_button=self._up_button), 
        playing_clip_below_layer=Layer(action_button=self._down_button))

  # EVENT HANDLING FUNCTIONS
  def reset_controlled_track(self):
    self.set_controlled_track(self.song().view.selected_track)
  
  def update(self):
    self.reset_controlled_track()
    super(APCAdvanced_MkII, self).update()

  def _on_selected_track_changed(self):
    self.reset_controlled_track()
    if self._auto_arm.needs_restore_auto_arm:
      self.schedule_message(1, self._auto_arm.restore_auto_arm)
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

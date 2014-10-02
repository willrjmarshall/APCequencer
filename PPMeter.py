import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.SubjectSlot import subject_slot
from _Framework.SessionComponent import SessionComponent 
from Push.Colors import Rgb
from APCMessenger import APCMessenger
import math

MASTER_SCALE_MAX = 1.0
MASTER_SCALE_MIN = 0.6
COLORS = [
  Rgb.GREEN.shade(2),
  Rgb.GREEN,
  Rgb.YELLOW,
  Rgb.AMBER,
  Rgb.RED
]

class PPMeter(ControlSurfaceComponent, APCMessenger):
  'represents a single PPM with Track source and ButtonMatrix target' 

  def __init__(self, track, top = MASTER_SCALE_MAX, bottom = MASTER_SCALE_MIN, *a, **k):
    super(PPMeter, self).__init__(*a, **k) 
    self.target_matrix = None
    self.top = top
    self.bottom = bottom
    self.track = track 
    self.prev_mean_peak = 0.0
    self._on_output_meter.subject = self.track

  def set_target_matrix(self, target_matrix):
    self.target_matrix = target_matrix

  def set_light(self):
    for x in range(self.led_count):
      for y in range(self.columns):
        button = self.target_matrix.get_button(x, y)
        if x < self.led_index:
          button.send_value(COLORS[x])          
        else:
          button.send_value(0)          

  @subject_slot('output_meter_left')
  def _on_output_meter(self):
    if self.target_matrix:
      self.set_light()

  def update(self):
    if self.target_matrix:
      self.set_light()

  @property
  def led_index(self):
    """ The index of the current peak LED """
    return int(round(self.scaled_mean_peak * self.multiplier))

  @property
  def scaled_mean_peak(self):
    """ 
      Rounds down/up values outside the range, then scales by bottomn of range.
      E.g. if range is 0.5-1.0, and value is 0.6, we'll be given 0.1
      or value is 1.1, we'll be given 0.5
    """
    value = self.mean_peak
    if (value > self.top): # Round values over the max down: e.g. clipping values
      value = self.top 
    elif (value < self.bottom):
      value = self.bottom 
    return value - self.bottom

  @property
  def mean_peak(self):
    """ The mean peak value of the left and right channel """
    return (self.track.output_meter_left + self.track.output_meter_right) / 2

  @property
  def multiplier(self):
    """ Multiplier to translate an adjusted decimal range (e.g. 0.0 - 0.5)
    to nearest LED integer """
    return (self.number_of_states / self.display_range)

  @property
  def number_of_states(self):
    """ All LEDs + OFF """
    return self.led_count + 1

  @property
  def led_count(self):
    """ Number of LEDs in our display. 
    A matrix on its side """
    return self.target_matrix.width()

  @property
  def columns(self):
    """ This is flipped 90 degrees! Remember! """
    return self.target_matrix.height()

  @property
  def display_range(self):
    """ 
    Volume values range from 0.0 to 1.0
    We only want to display a subsection of these values: e.g. 0.5 - 1.0
    This returns the length of this subsection
    """
    return self.top - self.bottom


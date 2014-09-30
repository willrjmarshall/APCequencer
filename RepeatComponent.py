from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.DeviceComponent import DeviceComponent
from _Framework.EncoderElement import EncoderElement
from _Framework.SubjectSlot import subject_slot_group
from _Generic.Devices import device_parameters_to_map, number_of_parameter_banks, parameter_banks, parameter_bank_names, best_of_parameter_bank
from APCMessenger import APCMessenger


class RepeatComponent(DeviceComponent, APCMessenger):
  """ Takes buttons rather than encoders.
  Doesn't support paging because why bother? 
  """
  def __init__(self, *a, **k):
    super(RepeatComponent, self).__init__(*a, **k)
    self._device_buttons = None

  @property
  def _bank(self):
    return parameter_banks(self._device)[0]

  def set_parameter_buttons(self, buttons):
    self._parameter_buttons = buttons
    self._on_parameter_button.replace_subjects(buttons or [])

  @subject_slot_group('value')
  def _on_parameter_button(self, value, button):
    parameter = self._bank[self._button_index(button)]
    if value > 0:
      parameter.value = parameter.max
    else:
      parameter.value = parameter.min

  def _button_index(self, button):
    return list(self._parameter_buttons).index(button)

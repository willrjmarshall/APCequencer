from _APC.SessionComponent import SessionComponent
from MatrixMaps import DEFAULT_CHANNEL

class SessionComponent(SessionComponent):
  """ Resets matrix when assigned """

  def set_clip_launch_buttons(self, buttons):
    if buttons:
      buttons.reset()
    super(SessionComponent, self).set_clip_launch_buttons(buttons)

  def set_stop_all_clips_button(self, button):
    """ This is so it can be mapped in one mode
    And still used in another mode """
    if button:
      button.set_channel(DEFAULT_CHANNEL)
    super(SessionComponent, self).set_stop_all_clips_button(button)

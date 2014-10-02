from _Framework.ButtonElement import ButtonElement

class ButtonElement(ButtonElement):
  """ Extended ButtonElement that exposes the correct API for
  Various Push-specific tools """

  def set_on_off_values(self, on_value, off_value):
    """ We don't actually care, but the script does want to set these.
    If the button doesn't support 'em, no change is necessary """
    pass

  def reset(self):
    self.set_identifier(self._original_identifier)
    self.set_channel(self._original_channel)

"""
This module defines application actions and provides input mapping functions.

This file is named user_input instead of simply "input" so that, when importing
this file, a name collision does not occur between this module and the Python
built-in function "input()".

"""

class InputSource:
    """
    Class that manages the polling for user input.

    """

    def __init__(self, curses, window):
        """
        Constructor.

        """
        self._curses = curses
        self._window = window

        self._configure_window()

    def _configure_window(self):
        """
        Prepare window instance attribute for input polling.

        """
        self._window.nodelay(True)

    def sample_input(self):
        """
        Return a string representation of the key(s) pressed.

        Returns:
            str: The keyboard keys(s) pressed when polled.

        """
        try:
            key_pressed = self._window.getkey()
        except self._curses.error:
            key_pressed = None

        return key_pressed

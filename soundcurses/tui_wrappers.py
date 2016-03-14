""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

The curses library performs the following tasks when initialized:

"""

import curses

class CursesWrapper:

    def __init__(self):
        # All instance variables declared here. If no initialization value
        # available, initialized to None.
        self._standard_screen = None

    def initialize_window(self):
        """ Immediately assumes control of the current TUI window.

        Changes window settings to facilitate proper handling of UI events.

        See https://docs.python.org/3.5/howto/curses.html#curses-howto

        From https://docs.python.org/3.5/library/curses.html#curses.initscr
        "If there is an error opening the terminal, the underlying curses
        library may cause the interpreter to exit."

        """
        # Return WindowObject, assuming control of current window.
        self._standard_screen = curses.initscr()
        # Replace curses constant values for special keys' escape sequences.
        self._standard_screen.keypad(True)
        # Prevent keypress' character display.
        curses.noecho()
        # Disable buffered input mode.
        curses.cbreak()

    def write(self, string):
        pass

    def destroy_window(self):
        """ Return TUI window to normal settings and relinquish control

        Returns window settings to original values.

        """
        # Disable special keys' escape sequence replacement.
        self._standard_screen.keypad(False)
        # Input returned to buffer mode.
        curses.nocbreak()
        # Character input display reactivated.
        curses.echo()
        # Release window control.
        curses.endwin()

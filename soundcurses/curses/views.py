""" This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.


"""

from collections import deque

class MainView:
    """ Highest-level view designed to control broad functions often associated
    with curses' stdscr. Manipulated by the main controller class.

    """

    def __init__(self, input_source, screen,
        window_header, window_nav, window_content):
        """ Constructor.

        input_source - Provides an interface for receiving input events from
            the curses library.
        screen - An abstracted interface for the display of the various curses
            components in a "composited" TUI view.

        """
        # Declare instance attributes.
        self._input_source = input_source
        self._screen = screen
        self._window_header = window_header
        self._window_nav = window_nav
        self._window_content = window_content

    def start(self):
        """ Render virtual curses state to physical screen.

        """
        self._screen.render()

    def start_input_polling(self):
        """ Starts polling for input from curses windows.

        """
        self._input_source.start()

    def stop_input_polling(self):
        self._input_source.stop()

    def stop(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._screen.destroy()

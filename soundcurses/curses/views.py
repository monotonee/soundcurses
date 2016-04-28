""" This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.


"""

from collections import deque

class MainView:
    """ Highest-level view designed to control broad functions often associated
    with curses' stdscr. Manipulated by the main controller class.

    """

    def __init__(self, input_source, screen,
        window_header, window_nav, window_content, modal_window_factory):
        """ Constructor.

        input_source - Provides an interface for receiving input events from
            the curses library.
        screen - An abstracted interface for the display of the various curses
            components in a "composited" TUI view.

        """
        # Declare instance attributes.
        self._input_source = input_source
        self._modal_window_factory = modal_window_factory
        self._screen = screen
        self._window_header = window_header
        self._window_nav = window_nav
        self._window_content = window_content

    def prompt_username(self):
        """ Display a modal input window into which the user will enter a
        valid SoundCloud username.

        """
        # Calculate screen percentages for modal dimensions.
        modal_dim_lines = round(self._screen.lines * 0.4)
        modal_dim_cols = round(self._screen.cols * 0.6)

        # Create and configure window.
        username_modal = self._modal_window_factory.create_modal(
            modal_dim_lines, modal_dim_cols)

        self._screen.schedule_window_update(username_modal)
        self._screen.render()
        test_input = username_modal.prompt('enter username: ')

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

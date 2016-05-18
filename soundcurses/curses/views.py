""" This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.


"""

import time

class MainView:
    """ Highest-level view designed to control broad functions often associated
    with curses' stdscr. Manipulated by the main controller class.

    """

    def __init__(self, input_source, screen,
        window_header, window_nav, window_content, window_modal):
        """ Constructor.

        input_source - Provides an interface for receiving input events from
            the curses library.
        screen - An abstracted interface for the display of the various curses
            components in a "composited" TUI view.

        """
        self._input_source = input_source
        self._screen = screen
        self._window_content = window_content
        self._window_header = window_header
        self._window_modal = window_modal
        self._window_nav = window_nav

    def destroy(self):
        """
        Relinquish control of the screen. Revert terminal settings.
        """
        self._screen.destroy()

    def hide_loading_animation(self):
        """
        Stop the loading animation and hide the modal window.
        """
        self._modal_window.stop_loading_animation()
        self._modal_window.hide()

    @property
    def last_render_timestamp(self):
        return self._screen.last_render_timestamp

    def prompt_username(self):
        """ Display a modal input window into which the user will enter a
        valid SoundCloud username.

        """
        self._window_modal.show()
        username = self._window_modal.prompt('enter username: ')
        self._window_modal.hide()

        return username

    def render(self):
        self._screen.render()

    def sample_input(self):
        """ Starts polling for input from curses windows.

        """
        return self._input_source.sample_input()

    def show_loading_animation(self):
        """ Displays a modal window in which an animated spinner is rendered.

        Designed to indicate that the program is waiting for some task to
        complete.

        """
        self._window_modal.start_loading_animation()
        self._window_modal.show()

""" This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.


"""

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
        # Declare instance attributes.
        self._input_source = input_source
        self._screen = screen
        self._window_content = window_content
        self._window_header = window_header
        self._window_modal = window_modal
        self._window_nav = window_nav


    def prompt_username(self):
        """ Display a modal input window into which the user will enter a
        valid SoundCloud username.

        """
        # Render new window. Note that the curses window methods called in the
        # modal's prompt method have implicit curses refresh calls.
        # self._screen.force_render_all()
        self._window_modal.show()
        self._screen.force_render_all()
        import time
        time.sleep(1)
        test_input = self._window_modal.prompt('enter username: ')
        # self._window_modal.hide()
        # self._screen.force_render_all()

        # return test_input

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

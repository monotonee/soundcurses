""" This module defines a series of wrappers and facade service classes designed
to compose other classes with more coarsely-defined interfaces.

"""

class CursesWrapper:
    """ Wraps the bare curses library interface, applying desired configurations
    at construction and passing calls through to underlying curses object.

    """

    def __init__(self, curses, locale):
        self._curses = curses
        self._locale = locale
        self.character_encoding = None

        self._configure()
        self._set_character_encoding()

    def __getattr__(self, name):
        """ According to my current knowledge, allows attribute access
        passthrough to underlying curses object. If attribute is nonexistent,
        AttributeError is raised by getattr() and allowed to bubble.

        """
        return getattr(self._curses, name)

    def _configure(self):
        """ Applies necessary setup configurations for app.

        See https://docs.python.org/3.5/howto/curses.html#curses-howto

        From https://docs.python.org/3.5/library/curses.html#curses.initscr
        "If there is an error opening the terminal, the underlying curses
        library may cause the interpreter to exit."

        Note: curses.initscr() must be called before curses.savetty().

        """
        # Save current state.
        self._curses.savetty()
        # Make cursor invisible.
        self._curses.curs_set(0)

        # Define color pairs.
        # self._curses.init_pair(
            # 1, self._curses.COLOR_BLACK, self._curses.COLOR_WHITE)

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        self._locale.setlocale(self._locale.LC_ALL, '')
        self.character_encoding = self._locale.getpreferredencoding()

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        # Restore original terminal configuration.
        self._curses.resetty()
        # Release window control.
        self._curses.endwin()


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

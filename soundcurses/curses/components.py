""" This module defines a series of wrappers and facade service classes designed
to compose other classes with more coarsely-defined interfaces.

"""

class CursesWrapper:
    """ Wraps the bare curses library interface, applying desired configurations
    at construction and passing calls through to underlying curses object.

    """

    def __init__(self, curses, locale):
        self._character_encoding = None
        self._curses = curses
        self._locale = locale

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
        self._curses.init_pair(
            1, self._curses.COLOR_WHITE, self._curses.COLOR_BLUE)

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        self._locale.setlocale(self._locale.LC_ALL, '')
        self._character_encoding = self._locale.getpreferredencoding()

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        # Restore original terminal configuration.
        self._curses.resetty()
        # Release window control.
        self._curses.endwin()


class InputSource:
    """ Manages the polling for user input and the issuing of keypress signals.

    """

    def __init__(self, window, signal_keypress):
        self._window = window
        self._signal_keypress = signal_keypress
        self._poll_input = True

    def start(self):
        """ Starts polling for input from window.

        window.getkey() is used so that the entities handling the keypress
        events don't need to be aware of curses' code point constants.

        """
        self._poll_input = True
        while self._poll_input:
            key_string = self._window.get_character()
            if key_string:
                self._signal_keypress.emit(key_string=key_string)

    def stop(self):
        """ Sets input polling loop sentinel value to Boolean false, breaking
        the polling loop if currently running.

        """
        self._poll_input = False

""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

The curses library performs the following tasks when initialized:

"""

import curses
import locale

class ViewCurses:

    def __init__(self):
        """ Initialize the curses standard (main) screen and window hierarchy.

        """
        # All instance variables declared here. If no initialization value
        # available, initialized to None.
        self._character_encoding = None
        self._standard_screen = None
        self._window_bar_first = None
        self._window_bar_second = None
        self._window_content = None

        # Start curses.
        self._set_character_encoding()
        self._initialize_standard_screen()
        self._initialize_windows()

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        locale.setlocale(locale.LC_ALL, '')
        self._character_encoding = locale.getpreferredencoding()

    def _initialize_standard_screen(self):
        """ Immediately assumes control of the current TUI window.

        Configues screen for presentation of common TUI.

        See https://docs.python.org/3.5/howto/curses.html#curses-howto

        From https://docs.python.org/3.5/library/curses.html#curses.initscr
        "If there is an error opening the terminal, the underlying curses
        library may cause the interpreter to exit."

        curses.initscr() must be called before curses.savetty().

        """
        # Return WindowObject, assuming control of current window.
        self._standard_screen = curses.initscr()
        # Save current state.
        curses.savetty()
        # Enable color rendering.
        curses.start_color()
        # Prevent keypress' character display.
        curses.noecho()
        # Disable buffered input mode.
        curses.cbreak()
        # Replace curses constant values for special keys' escape sequences.
        self._standard_screen.keypad(True)

    def _initialize_windows(self):
        """ Initializes windows, pads, and styles necessary for layout.

        https://docs.python.org/3.5/library/curses.html#curses.doupdate
        Note that when drawing content to a new subwindow, one must call
        refresh() on the subwindow reference. Refresh internally calls
        noutrefresh on the subwindow and then calls curses.doupdate(). If one
        calls refresh() on the main window first, the subwindow's state is never
        written to the virtual screen since its noutrefresh() method is never
        called.

        """
        # self._window_01 = curses.newwin(4, curses.COLS - 1, 0, 0)
        # self._window_01.border()
        # self._window_01.addstr('THIS IS ONLY A TEST')
        # self._standard_screen.refresh()
        # self._window_01.refresh()
        # self._standard_screen.refresh()
        # self._window_01.noutrefresh()
        # curses.doupdate()

    def destroy(self):
        """ Relinquish control of standard screen.

        Also returns window settings to original values.

        """
        # Restore original terminal configuration.
        curses.resetty()
        # Release window control.
        curses.endwin()

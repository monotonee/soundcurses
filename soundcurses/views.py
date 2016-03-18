""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

The curses library performs the following tasks when initialized:

"""

class CursesView:

    def __init__(self, curses, stdscr, locale):
        """ Initialize the curses standard (main) screen and window hierarchy.

        curses - A curses library interface.
        stdscr - A reference to a curses standard screen (main window).
        locale - A reference to the Python standard library locale interface.

        _character_encoding - Saves a reference to the character encoding used
            if it becomes necessary to convert byte streams into characters.
        _standard_screen - The reference to the main curses screen.
        _window_bar_first - The first horizontal window bar. Often contains
            current artist and track title.
        _window_bar_second - Displayed directly underneath the first bar. Often
            displays a breadcrumb-like hierarchy of current resources, letting
            a user know where one is in the SoundCloud resource tree.
        _window_content - The main window. Displays resource lists such as
            SoundCloud stream content, playlists, tracks, etc.

        """
        # All instance variables declared here. If no initialization value
        # available, initialized to None.
        self._curses = curses
        self._stdscr = stdscr
        self._locale = locale

        self._character_encoding = None
        self._standard_screen = None
        self._window_bar_first = None
        self._window_bar_second = None
        self._window_content = None

        # Start view.
        self._set_character_encoding()
        self._configure_stdscr()
        self._initialize_windows()

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        self._locale.setlocale(self._locale.LC_ALL, '')
        self._character_encoding = self._locale.getpreferredencoding()

    def _configure_stdscr(self):
        """ Immediately assumes control of the current TUI window.

        Configues screen for presentation of common TUI.

        See https://docs.python.org/3.5/howto/curses.html#curses-howto

        From https://docs.python.org/3.5/library/curses.html#curses.initscr
        "If there is an error opening the terminal, the underlying curses
        library may cause the interpreter to exit."

        curses.initscr() must be called before curses.savetty().

        """
        # Save current state.
        self._curses.savetty()
        # Make cursor invisible.
        self._curses.curs_set(0)

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
        # First bar.
        self._window_bar_first = self._curses.newwin(
            3, self._curses.COLS, 0, 0
        )
        self._window_bar_first.border()
        self._window_bar_first.noutrefresh()

        # Second bar.
        self._window_bar_second = self._curses.newwin(
            3, self._curses.COLS, 3, 0
        )
        self._window_bar_second.border()
        self._window_bar_second.noutrefresh()

        # Main area.
        self._window_content = self._curses.newwin(
            self._curses.LINES - 6, self._curses.COLS, 6, 0
        )
        self._window_content.border()
        self._window_content.noutrefresh()

        self._render()

    def _render(self):
        """ Render the state of the virtual curses windows and pads.

        """
        self._curses.doupdate()

    def destroy(self):
        """ Relinquish control of standard screen.

        Also returns window settings to original values.

        """
        # Restore original terminal configuration.
        self._curses.resetty()
        # Release window control.
        self._curses.endwin()

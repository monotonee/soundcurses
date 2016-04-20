""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

"""

import abc

class CursesView:

    def __init__(
        self, curses, locale,
        window_stdscr, window_header, window_nav, window_content):
        """ Construct the curses standard (main) screen and window hierarchy.

        curses - The curses library interface.
        locale - A reference to the Python standard library locale interface.
        window_stdscr - A reference to a curses standard screen (main window).
            Needed so that window refresh order can be properly maintained and
            UI events can be captured. Traditional "stdscr" nomenclature used
            to facilitate readability among those who are already familiar with
            the C curses library. Prefixed with "window" to denote custom
            wrapper class around the raw curses stdscr.

        _character_encoding - Saves a reference to the character encoding used
            if it becomes necessary to convert byte streams into characters.
        _curses - A reference to the curses
        _locale - Displayed directly underneath the first bar. Often
            displays a breadcrumb-like hierarchy of current resources, letting
            a user know where one is in the SoundCloud resource tree.
        _window_stdscr - The main window. Displays resource lists such as
            SoundCloud stream content, playlists, tracks, etc.

        """
        # Declare instance attributes.
        self._character_encoding = None
        self._curses = curses
        self._locale = locale
        self._window_stdscr = window_stdscr
        self._window_header = window_header
        self._window_nav = window_nav
        self._window_content = window_content

        # Gather information and establish initial instance state.
        self._set_character_encoding()
        self._configure_curses()
        self._configure_subwindows()
        self._render()

    def _configure_curses(self):
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

        # Establish color pairs.
        self._curses.init_pair(
            1, self._curses.COLOR_WHITE, self._curses.COLOR_BLUE)

    def _configure_subwindows(self):


    def _render(self):
        """ Render virtual curses state to physical screen.

        """
        self._curses.doupdate()

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        self._locale.setlocale(self._locale.LC_ALL, '')
        self._character_encoding = self._locale.getpreferredencoding()

    def start_input_polling(self):
        """ Starts polling for input from curses windows.

        """
        while True:
            char_code_point = self._window_stdscr.get_input()
            if char_code_point == ord('q'):
                break

    def destroy(self):
        """ Relinquish control of standard screen.

        Also returns window settings to original values.

        """
        # Restore original terminal configuration.
        self._curses.resetty()
        # Release window control.
        self._curses.endwin()


class CursesWindow(metaclass=abc.ABCMeta):
    """ Defines an abstract base class that encapsulates a layout region.

    """

    def __init__(self, curses, window):
        """ Constructor.

        curses - The curses library interface.
        window - A raw curses window object.

        """
        # Retain passed arguments.
        self._curses = curses
        self._window = window

        # Declare instance attributes.
        self.input_exception = curses.error
        self.virtual_state_updated = False

        # Gather information and establish initial instance state.
        self._configure_window()

    @abc.abstractmethod
    def _configure_window(self):
        """ Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Only called during object construction.

        Warning: make sure to call update_virtual_state() if necessary.

        """
        pass

    def update_virtual_state(self):
        """ Writes window state to curses' virtual screen state.

        """
        self._window.noutrefresh()
        self.virtual_state_updated = True


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window.

    """

    def _configure_window(self):
        """ Perform an empty update so that subsequent calls to refresh, either
        explicit or implicit (such as in window.getkey()) don't cause stdscr to
        overlap other windows.

        Called in constructor.

        """
        self._window.nodelay(True)

    def get_input(self):
        """ Wrapper for internal curses window instance method.

        """

        return self._window.getch()


class HeaderWindow(CursesWindow):
    """ A curses window that manages the header window.

    """

    def _configure_window(self):
        self._window.bkgd(' ', self._curses.color_pair(1))
        self._window.addstr(
            1, 2, 'Current user: Monotonee', self._curses.A_BOLD)


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation window.

    """

    def _configure_window(self):
        self._window.border()

class ContentWindow(CursesWindow):
    """ A curses window that manages the content window.

    """

    def _configure_window(self):
        self._window.border()





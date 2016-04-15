""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

"""

import abc

class CursesView:

    def __init__(
            self, curses, locale,
            stdscr_window, header_window, nav_window, content_window):
        """ Initialize the curses standard (main) screen and window hierarchy.

        curses - The curses library interface.
        locale - A reference to the Python standard library locale interface.
        stdscr_window - A reference to a curses standard screen (main window).
            Needed so that window refresh order can be properly maintained.

        _character_encoding - Saves a reference to the character encoding used
            if it becomes necessary to convert byte streams into characters.
        _window_bar_first - The first horizontal window bar. Often contains
            current artist and track title.
        _window_navigation - Displayed directly underneath the first bar. Often
            displays a breadcrumb-like hierarchy of current resources, letting
            a user know where one is in the SoundCloud resource tree.
        _window_content - The main window. Displays resource lists such as
            SoundCloud stream content, playlists, tracks, etc.

        """
        # Retain passed arguments.
        self._curses = curses
        self._locale = locale
        self._window_stdscr = stdscr_window
        self._window_header = header_window
        self._window_nav = nav_window
        self._window_content = content_window

        # Declare other instance attributes.
        self._character_encoding = None

        # Gather information and establish initial instance state.
        self._set_character_encoding()
        self._configure_curses()
        self._render()

    def _set_character_encoding(self):
        """ Determine environment locale and get encoding.

        See https://docs.python.org/3.5/library/curses.html

        """
        # Set current locale to user default as specified in LANG env variable.
        self._locale.setlocale(self._locale.LC_ALL, '')
        self._character_encoding = self._locale.getpreferredencoding()

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

    def _render(self):
        """ Render virtual curses state to physical screen.

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


class CursesWindow(metaclass=abc.ABCMeta):
    """ Defines an abstract base class that encapsulates a layout region.

    These are passed to the curses view which then manipulates the windows'
    content.

    """

    def __init__(self, curses, window):
        """ Initializer.

        curses - The curses library interface.

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

        Warning: make sure to call _update_virtual_state() if necessary.

        """
        pass

    def _update_virtual_state(self):
        """ Writes window state to curses' virtual screen state.

        """
        self._window.noutrefresh()
        self.virtual_state_updated = True


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window.

    """

    def _configure_window(self):
        """ Perform an empty update so that subsequent calls to refresh don't
        cause stdscr to overlap other windows.

        """
        self._window.nodelay(True)
        self._update_virtual_state()

    def get_key(self):
        """ Wrapper for internal curses window instance method.

        """

        return self._window.getkey()


class HeaderWindow(CursesWindow):
    """ A curses window that manages the header window.

    """

    def _configure_window(self):
        self._window.bkgd(' ', self._curses.color_pair(1))
        self._window.addstr(
            1, 2, 'Current user: Monotonee', self._curses.A_BOLD)
        self._update_virtual_state()


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation window.

    """

    def _configure_window(self):
        self._window.border()
        self._update_virtual_state()


class ContentWindow(CursesWindow):
    """ A curses window that manages the content window.

    """

    def _configure_window(self):
        self._window.border()
        self._update_virtual_state()





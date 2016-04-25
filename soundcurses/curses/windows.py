""" Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level classes.

"""

class CursesWindow:
    """ Defines a base class that encapsulates a layout region, implemented
    using a curses window or panel.

    """

    def __init__(self, curses, window):
        """ Constructor.

        curses - The curses library interface.
        window - A raw curses window object.

        """
        # Declare instance attributes.
        self._curses = curses
        self._window = window
        self.render_priority = 0
        self.virtual_state_requires_update = True

        # Gather information and establish initial instance state.
        self._configure_window()

    def _configure_window(self):
        """ Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        pass

    def update_virtual_state(self):
        """ Writes window state to curses' virtual screen state. Note the lack
        of checking whether or not the window state has changed.

        """
        self._window.noutrefresh()
        self._virtual_state_requires_update = False


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window above which other windows are
    rendered. In the curses library, stdscr often performs some special duties
    as well and this specialized subclass exposes the necessary interfaces.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.nodelay(True)
        self.render_priority = 1

    def getch(self):
        """ Wrapper for internal curses window instance method.

        """
        return self._window.getch()


class HeaderWindow(CursesWindow):
    """ A curses window that manages the header region. The header region is
    mostly a static data display.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.bkgd(' ', self._curses.color_pair(1))
        # self._window.addstr(
            # 1, 2, 'Current user: Monotonee', self._curses.A_BOLD)


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation region. The navigation
    region displays a SoundCloud user's available categories within which tracks
    may be present. Examples may include "tracks," "playlists," or "likes." The
    user may use the keyboard to select categories for track listings.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()


class ContentWindow(CursesWindow):
    """ A curses window that manages the content region. The content region's
    primary function is to display track listings, the constituent tracks of
    which may be selected and played.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()

class UsernameModalWindow(CursesWindow):
    """ Manages the modal window into which users input a SoundCloud user name.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()


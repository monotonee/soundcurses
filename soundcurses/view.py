""" Supplies a text-based user interface library wrapper object.

Designed to provide an additional layer of abstraction between the application
and the chosen text-based user interface library (TUI), in this case the curses
library.

"""

# import abc
from collections import deque

class CursesView:

    def __init__(self, curses, screen):
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
        _window_stdscr - The main window.

        """
        # Declare instance attributes.
        self._curses = curses
        self._screen = screen

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._curses.destroy()

    def render(self):
        """ Render virtual curses state to physical screen.

        """
        self._screen.render()

    def poll_input(self):
        """ Starts polling for input from curses windows.

        """
        self._screen.poll_input()


class CursesWindow:
    """ Defines an abstract base class that encapsulates a layout region.

    """

    def __init__(self, curses, window):
        """ Constructor.

        curses - The curses library interface.
        window - A raw curses window object.

        """
        # Declare instance attributes.
        self._curses = curses
        self._window = window
        self.input_exception = curses.error
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
        """ Writes window state to curses' virtual screen state regardless of
        necessity of doing so.

        """
        self._window.noutrefresh()
        self._virtual_state_requires_update = False


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window.

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
    """ A curses window that manages the header region.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.bkgd(' ', self._curses.color_pair(1))
        self._window.addstr(
            1, 2, 'Current user: Monotonee', self._curses.A_BOLD)


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation region.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()


class ContentWindow(CursesWindow):
    """ A curses window that manages the content region.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()


class CursesScreen:
    """ Makes sure that curses windows' states are written to virtual screen
    in the correct order. Manages rendering of virtual state to screen.

    _window_update_queue - A queue of window objects in order by refresh
        priority. Deque used due to possibility of adding element to front
        of queue, an operation for which a simple list is not optimized.

    """

    def __init__(self, curses, window_stdscr, *args):
        self._curses = curses
        self._windows = [window for window in args]
        self._window_stdscr = window_stdscr
        self._window_update_queue = deque()

        # New windows require initial update. Attempt to add ALL to update queue
        # in case initial virtual state update has not been completed.
        # Note list expansion in temporary list below.
        for window in [*self._windows, self._window_stdscr]:
            self.schedule_window_update(window)

    def _execute_update_queue(self):
        """ Iterate window virtual state update queue and execute updates.

        """
        if self._window_update_queue:
            for window in self._window_update_queue:
                window.update_virtual_state()
            self._window_update_queue.clear()

    def poll_input(self):
        """ Starts polling for input from curses windows.

        """
        while True:
            code_point = self._window_stdscr.getch()
            if code_point == ord('q'):
                break

    def render(self):
        self._execute_update_queue()
        self._curses.doupdate()

    def schedule_window_update(self, window):
        """ Push window objects into queue for virtual state update in order.

        The main "stdscr" window must always be scheduled for refresh first so
        that subwindow refreshes will be rendered "on top" of the main window.

        """
        if window.virtual_state_requires_update:
            if window is self._window_stdscr:
                self._window_update_queue.appendleft(window)
            else:
                self._window_update_queue.append(window)


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


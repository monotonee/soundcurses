""" This module defines a series of wrappers and facade service classes designed
to compose other classes with more coarsely-defined interfaces.

"""

from collections import deque

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

    @property
    def cols(self):
        return self._curses.COLS

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._curses.destroy()

    @property
    def lines(self):
        return self._curses.LINES

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


class InputSource:
    """ Manages the polling for user input and the issuing of keypress signals.

    """
    def __init__(self, window, signal_keypress):
        self._window = window
        self._signal_keypress = signal_keypress
        self._poll_input = True

    def start(self):
        """ Starts polling for input from window.

        """
        self._poll_input = True
        while self._poll_input:
            code_point = self._window.getch()
            if code_point > -1:
                self._signal_keypress.emit(code_point=code_point)

    def stop(self):
        """ Sets input polling loop sentinel value to Boolean false, breaking
        the polling loop if currently running.

        """
        self._poll_input = False

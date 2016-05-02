""" This module defines a series of wrappers and facade service classes designed
to compose other classes with more coarsely-defined interfaces.

"""

import itertools

class CursesScreen:
    """ Makes sure that curses windows' states are written to virtual screen
    in the correct order. Manages rendering of virtual state to screen and
    abstracts some basic functions of both the curses object and the stdscr
    object.

    _render_queue - A queue of window objects indexed by render layer.
    _windows - Begins as a straight conversion from *args tuple into a list.
        Used to maintain an unordered list of references to all curses windows.

    """

    def __init__(self, curses, render_queue, *args):
        self._curses = curses
        self._render_queue = render_queue
        self._windows = [*args]

        # New windows require initial update. Attempt to add all to render queue
        # in case initial virtual state update has not been completed.
        for window in self._windows:
            self.schedule_window_update(window)

    def _execute_update_queue(self):
        """ Iterate render queue and push window states to curses virtual state.

        """
        if self._render_queue:
            for window in self._render_queue:
                window.update_virtual_state()
            self._render_queue.clear()

    @property
    def cols(self):
        return self._curses.COLS

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._curses.destroy()

    def force_refresh_all(self):
        """ Add all windows to update queue regardless of necessity and then
        execute queue.

        Useful for forcing re-renders after modal windows are no longer needed.

        """
        for window in self._windows:
            window.touch()
            self.schedule_window_update(window)
        self.render()

    @property
    def lines(self):
        return self._curses.LINES

    def render(self):
        """ Pushes window state to curses virtual screen and then renders
        virtual screen state to physical screen.

        """
        self._execute_update_queue()
        self._curses.doupdate()

    def schedule_window_update(self, window):
        """ Push window objects into render queue.

        The queue object handles indexing and ordering by render layer.

        """
        if window.virtual_state_requires_update:
            self._render_queue.add(window)


class WindowRenderQueue():
    """ This class is designed to abstract the ordering of curses windows
    pushed onto the queue for later rendering.

    Each window object belongs to a predetermined rendering layer and this class
    uses that to insert the window into the appropriate order on the queue while
    accounting for collisions.

    The conscious choice was made to use a list as the value for every render
    layer "key" in the queue. While this does use more memory, it simplifies
    code by avoiding constant iterable checks. For this scale, the increased
    memory is deemed negligible.

    """

    def __init__(self):
        """ Constructor.

        """
        self._queue = {}

    def __iter__(self):
        """ Implements the iterable interface method.

        A key will only exist in the queue if it corresponds to a list value so
        it is safe to begin iteration of the value without checks.

        See: https://docs.python.org/3/reference/datamodel.html#object.__iter__

        Caution: I'm not sure if the dictionary view produced by dict.values()
        has consistent, deterministic order. In this queue, order is important
        so this needs to be watched.

        See: https://docs.python.org/3.1/library/stdtypes.html#dictionary-view-
            objects

        """
        return self._flatten_queue()

    def __len__(self):
        """ Implements len() interface.

        itertools.chain has no len() interface, thus it must be converted to an
        iterable that does. I question the efficiency of calculating something
        as simple as length this way. Consider implemting a loop and using an
        accumulator.

        See: https://docs.python.org/3/reference/datamodel.html#object.__len__

        """
        return len(list(self._flatten_queue()))

    def _flatten_queue(self):
        """ Returns windows in queue, contained in a one-dimensional, iterable
        sequence.

        """
        return itertools.chain(*self._queue.values())

    def add(self, window):
        """ Add a window object to the queue.

        Render layer collisions are handled by storing items in a bucket,
        implemented with a simple list.

        """
        if window.render_layer in self._queue:
            self._queue[window.render_layer].append(window)
        else:
            self._queue[window.render_layer] = [window]

    def clear(self):
        """ Empty the queue.

        """
        self._queue.clear()


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

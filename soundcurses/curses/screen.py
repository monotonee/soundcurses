""" This module provides classes that manage the curses screen nd window state.

"""

import itertools
import time

class CursesScreen:
    """
    Makes sure that curses windows' states are written to virtual screen
    in the correct order. Manages rendering of virtual state to screen and
    abstracts some basic functions of both the curses object and the stdscr
    object.

    *args - It seems to improve abstraction if all windows are passed to this
        class upon construction. This is helpful for complete refreshes of the
        entire screen.

    Attributes:
        _last_rendered_timestamp (float): Timestamp of last rendering.
        _render_queue (RenderQueue): Queue of window objects indexed by render
            layer.
        _windows (List): Maintains an unordered list of references to all
            windows.
    """

    RENDER_LAYER_HIDDEN = 0
    RENDER_LAYER_BASE = 1
    RENDER_LAYER_REGIONS = 2
    RENDER_LAYER_MODALS = 3

    def __init__(self, curses, render_queue, signal_rendered, *args):
        self._curses = curses
        self._last_render_timestamp = 0
        self._render_queue = render_queue
        self._windows = []
        self.signal_rendered = signal_rendered

        if args:
            for window in args:
                self.add_window(window)

    def _detect_touched_windows(self):
        """ Check all windows for touched status. If touched, add to update
        queue.

        """
        for window in self._windows:
            if window.is_wintouched():
                self._render_queue.add(window)

    def _flush_render_queue(self):
        """ Iterate render queue and push window states to curses virtual
        screen.

        """
        if self._render_queue:
            for window in self._render_queue:
                window.noutrefresh()
            self._render_queue.clear()

    def _force_touch_all(self):
        """ Touch all windows to force curses to render all.

        Useful for forcing re-renders after window(s) change render layers.

        """
        for window in self._windows:
            window.touchwin()

    def _handle_window_layer_change(self, window, delta, **kwargs):
        """
        Respond to a change in a given window's render layer value.

        Designed as a slot to the windows' signals indiciating a render layer
        change.

        """
        # If window is in render queue, it must have been touched.
        # No need to add to queue since _detect_touched_windows call in render()
        # will perform that function.
        if window in self._render_queue:
            self._render_queue.remove(window)
        self._force_touch_all()

    def add_window(self, window):
        """
        Add a new window to the screen.

        """
        window.signal_layer_change.connect(self._handle_window_layer_change)
        self._windows.append(window)

    @property
    def cols(self):
        return self._curses.COLS

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._curses.destroy()

    @property
    def last_render_timestamp(self):
        return self._last_render_timestamp

    @property
    def lines(self):
        return self._curses.LINES

    def remove_window(self, window):
        """
        Remove a window from the screen.

        The removed window, if still referenced somewhere, will no longer be
        rendered for any reason.

        List item comparisons apparently use identity first and equality second.

        See: http://stackoverflow.com/a/28562780

        """
        window.signal_layer_change.disconnect(self._handle_window_layer_change)
        self._windows.remove(window)
        self._render_queue.remove(window)

    def render(self):
        """ Pushes window state to curses virtual screen and then renders
        virtual screen state to physical screen.

        This method is kept public so that calling code, such as that of the
        view, can make all necessary writes to window state and call a single
        physical screen refresh rather than rely upon constant physical
        refreshes.

        """
        self._detect_touched_windows()
        self._flush_render_queue()
        self._curses.doupdate()
        self._last_render_timestamp = time.time()
        self.signal_rendered.emit()


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


class RenderQueue:
    """
    A class to manage the render order of curses window objects.

    Each window object belongs to a predetermined rendering layer and this class
    uses that to insert the window into the appropriate order on the queue while
    accounting for collisions.

    The conscious choice was made to use an iterable type as the value for every
    render layer "key" in the queue. While this does use more memory, it
    simplifies code by avoiding constant iterable checks. For this scale, the
    increased memory is deemed negligible.

    """

    def __init__(self):
        """
        Constructor.

        """
        self._queue = {}

    def __contains__(self, window):
        """
        Implement the membership test interface.

        Note that the list "in" operator first uses identity comparison before
        resorting to value equality comparison.

        Args:
            window (CursesWindow): A curses window object.

        Returns:
            bool: True if window is present in queue.

        """
        return window in self._flatten_queue()

    def __iter__(self):
        """
        Implement the iterable interface method.

        A key (render layer value) will only exist in the queue if there are
        windows present on that render layer. It is therefore safe to begin
        iteration of a key's associated list value without checking its
        existence.

        Caution: I'm not sure if the dictionary view produced by dict.values()
        has consistent, deterministic order. In this queue, order is important
        so this needs to be watched.

        See:
            https://docs.python.org/3/reference/datamodel.html#object.__iter__
            https://docs.python.org/3/library/stdtypes.html#dictionary-view-
                objects

        Returns:
            list: A list of window objects in render order.

        """
        return self._flatten_queue()

    def __len__(self):
        """
        Implement iterable length interface.

        The object returned by itertools.chain has no len() interface, thus it
        must be converted to an iterable that does.

        I question the efficiency of calculating something as simple as length
        this way. Consider implemting a loop and using an accumulator.

        See:
            https://docs.python.org/3/reference/datamodel.html#object.__len__
            https://docs.python.org/3/library/itertools.html#itertools.chain

        Returns:
            int: The count of window objects in the queue.

        """
        return len(list(self._flatten_queue()))

    def _flatten_queue(self):
        """
        Convert the queue data structure into a flat list.

        The window objects are placed into the list in proper render order.

        See:
            http://docs.python.org/3/library/stdtypes.html#dictionary-view-
                objects

        Returns:
            list: A list of window objects ordered by render layer.

        """
        return itertools.chain(*self._queue.values())

    def add(self, window):
        """
        Add a window object to the queue.

        Render layer collisions are handled by storing items in a bucket,
        implemented with a set iterable to prevent duplicates since once a
        window has been touched, it only needs to be present in the queue once.

        Args:
            window (CursesWindow): A curses window object.

        """
        if window.render_layer in self._queue:
            self._queue[window.render_layer].add(window)
        else:
            self._queue[window.render_layer] = {window}

    def clear(self):
        """
        Empty the queue.

        """
        self._queue.clear()

    def remove(self, window):
        """
        Remove a window from the queue.

        Will not throw an exception if the window was not present in the queue.

        Warning: do not modify an iterable during iteration with an iterator. To
        avoid modifying data structure during iteration, keys marked for
        deletion are saved and applied after iteration is complete. There's
        probably a more elegant way to do this.

        Args:
            window (CursesWindow): A curses window object.

        """
        empty_render_layers = []
        for render_layer, bucket in self._queue.items():
            if window in bucket:
                bucket.remove(window)
                if not bucket:
                    empty_render_layers.append(render_layer)

        for empty_render_layer in empty_render_layers:
            del self._queue[empty_render_layer]

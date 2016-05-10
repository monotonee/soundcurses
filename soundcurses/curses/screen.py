""" This module provides classes that manage the curses screen nd window state.

"""

import itertools

class CursesScreen:
    """ Makes sure that curses windows' states are written to virtual screen
    in the correct order. Manages rendering of virtual state to screen and
    abstracts some basic functions of both the curses object and the stdscr
    object.

    *args - It seems to improve abstraction if all windows are passed to this
        class upon construction. This is helpful for complete refreshes of the
        entire screen. See force_render()

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
            self.add_window(window)

    def _execute_update_queue(self):
        """ Iterate render queue and push window states to curses virtual
        screen.

        """
        if self._render_queue:
            for window in self._render_queue:
                window.update_virtual_state()
            self._render_queue.clear()

    def _handle_window_render_layer_change(self, delta, **kwargs):
        """ Designed as a slot to the windows' signals indiciating a render
        layer change.

        """

    def add_window(self, new_window):
        """ Add a window to the screen.

         """
        new_window.signal_render_layer_change.connect(
            self._handle_window_render_layer_change)
        self.schedule_window_update(new_window)

    @property
    def cols(self):
        return self._curses.COLS

    def destroy(self):
        """ Relinquish control of the screen. Also returns window settings
        not set by curses.wrapper() to original values.

        """
        self._curses.destroy()

    def force_render_all(self):
        """ Add all windows to update queue regardless of necessity and then
        execute queue.

        Useful for forcing re-renders after window(s) change render layers.

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

        The docs page on the dictionary's values() method returns a view,
        iteration over which is in arbitrary order. So simply to guarantee
        ascending sort, I am iterating manually.
        See: docs.python.org/3.5/library/stdtypes.html#dictionary-view-objects

        Previous implementation may also work but tests are needed:
        return itertools.chain(*self._queue.values())

        """
        # sorted_list = []
        # for key in sorted(self._queue.keys()):
            # sorted_list.append(self._queue[key])
        # return itertools.chain.from_iterable(sorted_list)
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

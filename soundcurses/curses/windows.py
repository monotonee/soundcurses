"""
Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level view classes.

The basic curses window objects are wrapped with a few helper methods and a
layering system used by the CursesScreen instance.

"""

class BoxCoords:
    """
    A plain data object that stores simple coordinates for a box.

    Coordinates are maintained in curses style (y, x) and operations are
    generally assumed to take place within the context of a curses screen.

    """

    def __init__(self, origin, lines, cols):
        """
        Constructor.

        Args:
            origin (tuple): A tuple of ints (y, x) of box origin coords. Again,
                curses style dictates that origin is top left vertex.
            lines (int): The total number of lines encompassed by box.
            cols (int): The total number of columns encompassed by box.

        """
        self.cols = cols
        self.lines = lines
        self.origin = origin

        self._validate_coords()

    def _validate_coords(self):
        """
        Validate the data with which an instance of this class was created.

        Raises:
            ValueError: If line or column count is less than or equal to zero.

        """
        if self.lines <= 0 or self.cols <= 0:
            raise ValueError('A box must have positive dimensions.')

    @property
    def bottom_left(self):
        """
        Get the bottom-right coordinate tuple.

        Returns:
            tuple: Tuple of ints (y, x)

        """
        return (self.origin[0] + self.lines, self.origin[1])

    @property
    def bottom_right(self):
        """
        Get the bottom-right coordinate tuple.

        Returns:
            tuple: Tuple of ints (y, x)

        """
        return (self.origin[0] + self.lines, self.origin[1] + self.cols)

    @property
    def top_left(self):
        """
        Get the top-left (origin) coordinate tuple.

        Alias of self.origin attribute.

        Returns:
            tuple: Tuple of ints (y, x)

        """
        return self.origin

    @property
    def top_right(self):
        """
        Get the top-right coordinate tuple.

        Returns:
            tuple: Tuple of ints (y, x)

        """
        return (self.origin[0], self.origin[1] + self.cols)


class CursesWindow:
    """
    A curses window wrapper class.

    All curses window wrapper classes are expected to expose or override
    the underlying curses window methods as well. This class also defines the
    additional methods.

    """

    def __init__(self, window, screen, signal_layer_change, render_layer=None):
        """
        Constructor.

        Args:
            screen (CursesScreen): Necessary for the use of render layer
                constants.

        """
        if render_layer == None:
            render_layer = screen.RENDER_LAYER_BASE

        self._render_layer_current = render_layer
        self._screen = screen
        self._window = window
        self.render_layer_default = render_layer
        self.signal_layer_change = signal_layer_change

    def __getattr__(self, name):
        """
        Expose underlying curses window methods.

        Designed to allow passthrough access to underlying window object using
        built-in getattr(). If attribute is nonexistent, AttributeError is
        raised by getattr() and allowed to bubble.

        I don't know if definining this "magic method" in an ABC is good
        practice. It was done for future maintainability so that the maintainer
        does not forget to expose curses window methods with any new window
        wrapper classes.

        """
        return getattr(self._window, name)

    def _change_render_layer(self, new_render_layer):
        """
        Change render layer and emit appropriate signal.

        """
        render_layer_delta = new_render_layer - self._render_layer_current
        self._render_layer_current = new_render_layer
        self.signal_layer_change.emit(
            window=self, delta=render_layer_delta)

    @property
    def cols(self):
        """
        Return the window's x-axis dimension in columns.

        Returns:
            int: The number of columns.

        """
        return self._window.getmaxyx()[1]

    @property
    def hidden(self):
        """
        Returns whether or not the window is on the "hidden" render layer.

        Returns:
            Boolean: True if hidden, false otherwise.

        """
        return self._render_layer_current == self._screen.RENDER_LAYER_HIDDEN

    def hide(self):
        """
        Set current render layer to hidden.

        When window is passed to rendering queue, will ensure that window is not
        visible upon next physical screen render.

        """
        self._change_render_layer(self._screen.RENDER_LAYER_HIDDEN)

    @property
    def lines(self):
        """
        Return the window's y-axis dimension in lines.

        Returns:
            int: The number of lines.

        """
        return self._window.getmaxyx()[0]

    @property
    def render_layer(self):
        """
        Return the render layer to which the window is currently assigned.

        Returns:
            int: The render layer.

        """
        return self._render_layer_current

    def show(self):
        """
        Set window's render layer to its default.

        Often called to reverse the effects of a call to hide().

        """
        self._change_render_layer(self.render_layer_default)


class CursesPad(CursesWindow):
    """
    A class that wraps a curses pad from curses.newpad().

    This class is designed to isolate the screen rendering classes from the
    peculiar interface of pads' refresh() and noutrefresh() methods.

    """

    def __init__(self, pad, screen, signal_layer_change,
        visible_origin, clipping_box, render_layer=None):
        """
        Constructor.

        Note that no validation of coordinate arguments is currently performed.
        Exceptions will be raised when the pad is refreshed if the coordinate
        arguments are invalid.

        Args:
            pad (curses.pad): A pad data structure from the curses library.
            visible_origin (tuple): A tuple of int coords (y, x). This
                coordinate is the coordinate within the pad that will be placed
                directly under the clipping box origin (upper left) when pad is
                rendered. Corresponds to the curses.pad.refresh method's
                "pminrow" and "pmincol" parameters.
            clipping_box (BoxCoords): A Box object defining the rendering area
                of pad.

            See:
                https://docs.python.org/3.5/library/curses.html#curses.newpad
                http://linux.die.net/man/3/newpad

        """
        super().__init__(pad, screen, signal_layer_change,
            render_layer=render_layer)

        self._visible_origin = visible_origin
        self._clipping_box = clipping_box

    def refresh(self):
        """
        Refresh the pad.

        Actually returns a partial function with bound arguments necessary
        for the curses.pad's unique refresh method signature.

        """
        self._window.refresh(
            *self._visible_origin,
            *self._clipping_box.origin,
            *self._clipping_box.bottom_right)

    def noutrefresh(self):
        """
        Refresh the pad.

        Actually returns a partial function with bound arguments necessary
        for the curses.pad's unique refresh method signature.

        """
        self._window.noutrefresh(
            *self._visible_origin,
            *self._clipping_box.origin,
            *self._clipping_box.bottom_right)


class CursesWindowFactory:
    """
    A class to hide the creation details of CursesWindow objects at runtime.

    """

    def __init__(self, curses, screen, signalslot):
        """
        Constructor.

        """
        self._curses = curses
        self._screen = screen
        self._signalslot = signalslot
        self._signal_layer_change_args = ['window', 'delta']

    def _create_layer_change_signal(self):
        """
        Create the signalslot.Signal for window layer changes.

        Returns:
            signalslot.Signal: Signal object with kwargs configured.

        """
        return self._signalslot.Signal(args=self._signal_layer_change_args)

    def create_box_coords(self, lines, cols, origin):
        """
        Create a new box data object.

        Args:
            origin (tuple): A tuple of ints (y, x) of box origin coords. Again,
                curses style dictates that origin is top left vertex.
            lines (int): The total number of lines encompassed by box.
            cols (int): The total number of columns encompassed by box.

        """
        return BoxCoords(origin, lines, cols)

    def create_pad(self, lines, cols, visible_origin, clipping_box,
        render_layer=None):
        """
        Create a curses pad wrapper object.

        Args:
            lines (int): The number of lines pad should ecompass.
            cols (int): The number of cols pad should encompass.
            visible_origin (tuple): A tuple of int coords (y, x). This
                coordinate is the coordinate within the pad that will be placed
                directly under the clipping box origin (upper left) when pad is
                rendered. Corresponds to the curses.pad.refresh method's
                "pminrow" and "pmincol" parameters.
            clipping_box (BoxCoords): A box object defining the rendering area
                of pad.

            See:
                https://docs.python.org/3.5/library/curses.html#curses.newpad

        """
        return CursesPad(
            self._curses.newpad(lines, cols),
            self._screen,
            self._create_layer_change_signal(),
            visible_origin,
            clipping_box,
            render_layer=render_layer)

    def create_window(self, lines, cols, y, x, render_layer=None):
        """
        Create and return a new CursesWindow instance.

        The curses library will raise an exception if window size is larger than
        available screen dimensions.

        """
        return CursesWindow(
            self._curses.newwin(lines, cols, y, x),
            self._screen,
            self._create_layer_change_signal(),
            render_layer)

    def wrap_window(self, window, render_layer=None):
        """
        Create a new CursesWindow with the passed window.

        Instead of creating a new curses window with curses.newwin, uses the
        passed window object.

        See:
            self.create_window

        """
        return CursesWindow(
            window,
            self._screen,
            self._create_layer_change_signal(),
            render_layer)


class CursesString:
    """
    A class that maintains a string and its coordinates within a window.

    Facilitates the display of characters within a curses window. Collects
    a displayed string's coordinates within a window and makes operations such
    as moving, erasing, and overwriting strings easier.

    The string passed into the constructor may contain newline characters. The
    string will be converted into a list of lines, split on the newline
    characters. Each line will be written to a new line in the window
    sequentially.

    A string is not written to the window by default. The calling code must
    manually call the write method.

    """

    def __init__(self, curses, window, string, y, x, attr=None):
        """
        Constructor.

        Args:
            curses: A curses library module namespace or the CursesWrapper.
                Necessary for the use of string styling contstants.
            window (curses.newwin): A curses window wrapper. Must have wrapper
                interface with the lines and cols getter properties.
            string: (string): The string. Will be split into lines on each
                newline character (\n).
            y (int): The y-coord at which to initially write string.
            x (int): The x-coord at which to initially write string.
            attr (int): A curses attribute integer. Each bit represents a style.
                Ex: curses.A_BOLD

        Raises:
            ValueError
        """
        # Validate arguments.. Ensure y and x do not exceed window bounds.
        if y > window.lines or x > window.cols:
            raise ValueError('String origin coords exceed window bounds.')
        if attr == None:
            attr = curses.A_NORMAL

        self._coord_x = x
        self._coord_y = y
        self._curses = curses
        self._is_written = False
        self._string_lines_list = string.split('\n')
        self._window = window
        self.attr = attr
        self._string = string

        self._validate_string()

    def __len__(self):
        """
        Implement the length interface method for use with len().

        """
        return len(self._string)

    @property
    def _string_lines(self):
        """
        Generate origin coords and string for each string line.

        A generator function that yields a tuple of three elements: y-coord,
        x-coord, and string of each line in the string.

        Returns:
            tuple: (coord_y, coord_x, length) Of each line in string.
        """
        line_number = 0
        for line in self._string_lines_list:
            line_coord_y = self._coord_y + line_number
            line_coord_x = self._coord_x
            yield (line_coord_y, line_coord_x, line)
            line_number += 1

    def _validate_string(self):
        """
        Ensure that string can be properly written to window in its enirety.

        Raises:
            ValueError: If string is too long or has too many lines to fit into
                the window.

        """
        line_count = len(self._string_lines_list)
        longest_line = len(max(self._string_lines_list, key=len))
        if longest_line > self._window.cols or line_count > self._window.lines:
            raise ValueError('String is too long for window dimensions.')

    @property
    def attr(self):
        """
        Get the current string's curses attribute byte sequence.

        """
        return self._attr

    @attr.setter
    def attr(self, attr):
        """
        Set the current string's curses attribute byte sequence.

        If string has already been written, alter it. Overwrite current string
        attributes if any.

        """
        self._attr = attr
        if self._is_written:
            for coord_y, coord_x, line in self._string_lines:
                self._window.chgat(
                    coord_y,
                    coord_x,
                    len(line),
                    self._attr)

    def erase(self):
        """
        Overwrite string with blank chars.

        """
        for coord_y, coord_x, line in self._string_lines:
            empty_string = ''.ljust(len(line))
            self._window.addstr(coord_y, coord_x, empty_string)
        self._is_written = False

    @property
    def lines(self):
        """
        Get the list of the string's lines.

        Returns:
            list: A list of string lines.

        """
        return self._string_lines_list

    def move(self, y, x):
        """
        Change coords of string.

        If string is currently written, erase and rewrite in new location.

        """
        # Inelegant. erase() needs old coords, write() needs new ones.
        if self._is_written:
            self.erase()
            self._coord_y = y
            self._coord_x = x
            self.write()
        else:
            self._coord_y = y
            self._coord_x = x

    def style_bold(self):
        """
        Set the string curses attribute to bold style.

        Overwrite current string attributes if any.

        """
        self.attr = self._curses.A_BOLD

    def style_dim(self):
        """
        Set the string curses attribute to bold style.

        Overwrite current string attributes if any.

        """
        self.attr = self._curses.A_DIM

    def style_normal(self):
        """
        Set the string curses attribute to no style.

        Overwrite current string attributes if any.

        """
        self.attr = self._curses.A_NORMAL

    def style_reverse(self):
        """
        Set the string curses attribute to reverse style.

        Overwrite current string attributes if any.

        """
        self.attr = self._curses.A_REVERSE

    @property
    def value(self):
        """
        Return the raw internal string value.

        Returns:
            string: The raw string value before line splitting or processing.

        """
        return self._string

    def write(self):
        """
        Write the string to the window.

        Curses does not care if string is re-written over identical string so no
        is_written check is performed.

        """
        for coord_y, coord_x, line in self._string_lines:
            self._window.addstr(
                coord_y,
                coord_x,
                line,
                self._attr)
        self._is_written = True

    @property
    def x(self):
        """
        Get the origin x-coordinate string.

        """
        return self._coord_x

    @property
    def y(self):
        """
        Get the origin y-coordinate string.

        """
        return self._coord_y


class CursesStringFactory:
    """
    A class to hide creation details of CursesString classes at runtime.

    """

    def __init__(self, curses):
        """
        Constructor.

        """
        self._curses = curses

    def create_string(self, window, string, y, x, attr=None):
        """
        Create a new CursesString instance.

        """
        return CursesString(self._curses, window, string, y, x, attr)


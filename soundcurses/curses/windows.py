"""
Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level view classes.

The basic curses window objects are wrapped with a few helper methods and a
layering system used by the CursesScreen instance.

Regions are higher-level abstractions than windows and represent display regions
in the view. The regions are the interface with which the iew object interacts.

"""

import collections
import itertools
import math
import textwrap

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
        # Validate arguments.
        # Set default render layer value.
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

    def create_window(self, lines, cols, y, x, render_layer=None):
        """
        Create and return a new CursesWindow instance.

        The curses library will raise an exception if window size is larger than
        available screen dimensions.

        """
        return CursesWindow(
            self._curses.newwin(lines, cols, y, x),
            self._screen,
            self._signalslot.Signal(args=self._signal_layer_change_args),
            render_layer)

    def wrap_window(self, window, render_layer=None):
        """
        Create a new CursesWindow with the passed window.

        Instead of creating a new curses window with curses.newwin, use the
        passed window object.

        """
        return CursesWindow(
            window,
            self._screen,
            self._signalslot.Signal(args=self._signal_layer_change_args),
            render_layer)


class HeaderRegion:
    """
    A class that represents the header region.

    The header region displays the current program version and the help hotkey.
    The text displayed in this region is static and will not change at
    runtime.

    """

    def __init__(self, window, curses):
        """
        Constructor.

        Raises:
            ValueError: If window is too small for content.

        """
        # Validate arguments.
        if window.lines < 1:
            raise ValueError('Window is to small for region content.')

        self._curses = curses
        self._window = window

        self._configure()
        self._write_text()

    def _configure(self):
        """
        Configure region/window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        self._window.bkgd(' ', self._curses.A_REVERSE)

    def _write_text(self):
        """
        Writes static text to the window.

        Text will not change at runtime. Yes, this is currently incompatible
        with too few columns. The curses library will throw an exception from
        addstr() if there are too few columns to complete string write.

        """
        self._window.addstr(0, 0, 'soundcurses - version 0.0.1')
        help_string = 'F1: help'
        self._window.addstr(0, self._window.cols - len(help_string) - 1,
            help_string)


class StatusRegion:
    """
    A class that represents the header region.

    This region displayes the current SoundCLoud user from which assets, such as
    tracks and playlists, are currently displayed. May also display title
    and artist of currently-playing tracks.

    """

    def __init__(self, window, string_factory):
        """
        Constructor.

        Raises:
            ValueError: If window is too small for content.

        """
        # Validate arguments.
        if window.lines < 1:
            raise ValueError('Window is to small for region content.')

        self._string_factory = string_factory
        self._username = None

    @property
    def username(self):
        """
        Get the currently-displayed username.

        The value of the username attribute will either be None or a
        curses string wrapper (CursesString) object instance.

        """
        username_string = None
        if self._username:
            username_string = self._username.string

        return username_string

    @username.setter
    def username(self, username):
        """
        Set the currently-displayed username.

        Yes, this is currently incompatible with too few window columns. The
        curses library will throw an exception from addstr() if there are too
        few columns to complete string write.

        """
        y_coord = (self._window.lines - 1) / 2
        x_coord = 1

        self._username = self._string_factory.create_string(
            self._window,
            username,
            y_coord,
            x_coord)
        self._username.write()


class NavRegion:
    """
    A class that represents the nav region.

    Displays username sub-resources such as tracks, playlists, etc. Only a
    single nav item can be highlighted at a given time. There will always be a
    nav item highlighted.

    The user subresource categories are pretty static and I know of no way to
    query a resource in order to dynamically-enumerate them. Therefore,
    this window will be hard-coded with a preset set of available menu items.

    """

    NAV_ITEM_01_TRACKS = 'TRACKS'
    NAV_ITEM_02_PLAYLISTS = 'PLAYLISTS'
    NAV_ITEM_03_FAVORITES = 'FAVORITES'
    NAV_ITEM_04_FOLLOWING = 'FOLLOWING'
    NAV_ITEM_05_FOLLOWERS = 'FOLLOWERS'

    def __init__(self, window, string_factory):
        """
        Constructor.

        Raises:
            ValueError: If window is too small for content.

        """
        # Validate arguments.
        if window.lines < 1:
            raise ValueError('Window is to small for region content.')

        self._currently_highlighted_item = None
        self._highlighted_item_cycle = None
        self._nav_items = collections.OrderedDict()
        self._string_factory = string_factory
        self._window = window

        self._configure()
        self._init_items()
        self._init_highlighted_item()

    def _configure(self):
        """
        Configure region/window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        self._window.border()

    def _init_items(self):
        """
        Write nav items to the nav window.

        Dynamically enumerates the NAV_ITEM_* constants and places them in a
        dictionary. Dict keys are nav item constant values, dict values are the
        CursesString objects of the character strings written to window.

        Currently does not accound for very narrow screen widths.

        Called in constructor before the highlighted item initializer.

        """
        # Enumerate nav items. Do not yet create strings since coords are not
        # yet known and are dependent upon the number of nav items and their
        # string lengths.
        total_char_count = 0
        for attribute in dir(self):
            if attribute.startswith('NAV_ITEM_'):
                nav_item_display_string = getattr(self, attribute)
                self._nav_items[nav_item_display_string] = None
                total_char_count += len(nav_item_display_string)

        # Calculate initial intra-nav-item spacing within window.
        # For now, ignore very narrow edge case window sizes.
        # TEMPORARILY assume that there are more available cols than characters.
        # Remove two cols from available cols for edge spacing/border.
        spacing_cols = math.floor((self._window.cols - 2 - total_char_count) \
            / (len(self._nav_items) - 1))

        # Determine coords at which to begin writing.
        y_coord = math.floor((self._window.lines - 1) / 2)
        x_coord = 1

        # Create nav item string objects with spaced coords and write to window.
        # Place first nav item then place following items in a loop since first
        # item has no left-hand spacing.
        nav_item_iter =  iter(self._nav_items.keys())
        first_item = next(nav_item_iter)
        first_string = self._string_factory.create_string(
            self._window, first_item, y_coord, x_coord)
        first_string.write()
        self._nav_items[first_item] = first_string

        # Write the remainder of the nav items to window.
        x_coord = len(first_string) + spacing_cols
        for nav_item in nav_item_iter:
            nav_string = self._string_factory.create_string(
                self._window, nav_item, y_coord, x_coord)
            nav_string.write()
            self._nav_items[nav_item] = nav_string
            x_coord += len(nav_string) + spacing_cols

    def _init_highlighted_item(self):
        """
        Initialize the highlight iterator and highlight the default nav item.

        Called in constructor after the nav item initializer. Each item in cycle
        is a CursesString instance so "highlighting" is merely changing the
        displayed string's style in some contrasting way.

        """
        self._highlighted_item_cycle = itertools.cycle(
            iter(self._nav_items.values()))
        self._currently_highlighted_item = next(self._highlighted_item_cycle)
        self._currently_highlighted_item.style_reverse()

    def _set_highighted_style(self, item):
        """
        Set the passed item to the chosen highlight curses string style.

        This method simply centralizes the style.

        """
        item.style_reverse()

    def highlight_item(self, item_string):
        """
        Highlight a specific nav item.

        Args:
            item_string (string): A string value of one of NAV_ITEM_* constants.

        Raises:
            ValueError: If item is not a valid nav item.
        """
        if item_string not in self._nav_items:
            raise ValueError('Nonexistent nav menu item.')

        self._currently_highlighted_item.style_normal()
        self._currently_highlighted_item = self._nav_items[item_string]
        self._set_highighted_style(self._currently_highlighted_item)

        # "Fast-forward" cycle to match currently-highlighted item.
        for item in self._highlighted_item_cycle:
            if item.string == self._currently_highlighted_item.string:
                break

    def highlight_next(self):
        """
        Highlight the next navigation item.

        """
        self._currently_highlighted_item.style_normal()
        self._currently_highlighted_item = next(self._highlighted_item_cycle)
        self._set_highighted_style(self._currently_highlighted_item)


class ContentRegion:
    """
    A class that represents the content region.

    The content region's primary function is to display user sub-resource
    listings such as tracks or playlists.

    """

    def __init__(self, window, curses):
        """
        Constructor.

        Raises:
            ValueError: If window is too small for content.

        """
        # Validate arguments.
        if window.lines < 1:
            raise ValueError('Window is to small for region content.')

        self._curses = curses
        self._window = window

        self._configure()

    def _configure(self):
        """
        Configure region/window properties.

        """
        self._window.border(
            ' ', ' ', 0, ' ',
            self._curses.ACS_HLINE, self._curses.ACS_HLINE, ' ', ' ')


class ModalRegionBase:
    """
    A class representing a region that exposes modal-like behavior.

    This is a base class that provides common functionality for more specialized
    modal windows. Note that ModalRegion differs from other region classes in
    one main way: it creates its own curses window per instance rather than
    accepting a window argument in its constructor. Modal "windows" such as
    alerts or popups are temporary in nature and therefore ModalRegion instances
    expose a destroy method.

    Attributes:
        WIN_MAX_PERCENT (float): The max size of the modal window relative to
            the screen dimensions.
        WIN_MIN_PERCENT (float): The min size of the modal window relative to
            the screen dimensions.

    """

    WIN_MAX_PERCENT = 0.9
    WIN_MIN_PERCENT = 0.4

    def __init__(self, curses, screen, window_factory):
        """
        Constructor.

        Args:
            screen (CursesScreen): Necessary so that the new curses windows
                created by instances of this class can be added to render queue.

        """
        self._curses = curses
        self._reserved_cols = 4
        self._reserved_lines = 4
        self._screen = screen
        self._window = None
        self._window_factory = window_factory

        self._init_window()

    @property
    def _avail_cols(self):
        """
        Get the number of available, non-reserved lines.

        Returns:
            int: The number of avaiable lines.

        """
        avail_lines, avail_cols = self._get_avail_dimensions(
            self._window.lines, self._window.cols)
        return avail_cols

    @property
    def _avail_lines(self):
        """
        Get the number of available, non-reserved lines.

        Returns:
            int: The number of avaiable lines.

        """
        avail_lines, avail_cols = self._get_avail_dimensions(
            self._window.lines, self._window.cols)
        return avail_lines

    @property
    def _avail_origin(self):
        """
        Get the origin y-coord of available space within window.

        Returns:
            tuple: Ints (y, x), the origin of available area within window.

        """
        return self._get_centered_coords(
            self._window.lines, self._window.cols,
            self._avail_lines, self._avail_cols)

    def _center_window(self):
        """
        Centers the window in the screen if necessary.

        This method can be called, for example, if the window has been resized.

        """
        centered_coords = self._get_centered_coords(
            self._curses.LINES, self._curses.COLS,
            self._window.lines, self._window.cols)
        if self._window.getbegyx() != centered_coords:
            self._window.mvwin(*centered_coords)

    def _get_avail_dimensions(self, lines, cols):
        """
        Given dimensions, return this modal region's available dimensions.

        Certain lines and columns are reserved inside the window. Two each of
        lines and columns may be reserved for the window border, for instance.
        This method returns the writable space inside a window of the given
        dimensions.

        Note that no exceptions are thrown for invalid dimensions such as
        negative numbers. The responsibility of validation rests with the
        calling code.

        Args:
            lines (int): Number of lines in a window.
            cols (int): Number of columns in a window.

        Returns:
            tuple: Tuple (lines, cols) of available dimensions.

        """
        avail_lines = lines - self._reserved_lines
        avail_cols = cols - self._reserved_cols
        return (avail_lines, avail_cols)

    @staticmethod
    def _get_centered_coords(avail_lines, avail_cols,
        target_lines, target_cols):
        """
        Return a tuple (y, x) that will result in a centered object.

        This function takes two sets of dimensions. The avail_lines and
        avail_cols arguments are the dimensions of the object in which target
        object will be centered.

        The target_lines and target_cols arguments are the dimensions of the
        object that needs to be centered within the available lines and columns.

        The returned coordinate tuple contains the coordinates within the
        containing object at which the upper left corner of the target object
        should be placed for it to be centered within the available dimensions.

        The returned centered coordinates may sometimes result in an imperfect
        centering solution. For example, if one tries to center a single line
        within a two-line container, one line will be left over. In these cases,
        the extra line will be added underneath the target object.

        Args:
            avail_lines (int): The number of lines of containing box.
            avail_cols (int): The number of cols in containing box.
            target_lines (int): The number of lines in box to be centered.
            target_cols (int): THe number of lines in box to be centered.

        Returns:
            tuple: Tuple of ints (y, x) of origin of target area centered.

        Raises:
            ValueError: If target dimension is larger than avail dimension.

        """
        # Validate arguments.
        if target_lines > avail_lines:
            raise ValueError(
                'Cannot center object with more lines than its container.')
        if target_cols > avail_cols:
            raise ValueError(
                'Cannot center object with more columns than its container.')

        centered_y = math.floor((avail_lines - target_lines) / 2)
        centered_x = math.floor((avail_cols - target_cols) / 2)
        return (centered_y, centered_x)

    def _init_window(self):
        """
        Initialize the curses window instance attribute.

        On class instantiation, this method creates a curses window of a
        default, minimum size.

        """
        dim_y = self._min_lines
        dim_x = self._min_cols
        coord_y, coord_x = self._get_centered_coords(
            self._curses.LINES, self._curses.COLS,
            dim_y, dim_x)
        self._window = self._window_factory.create_window(
            dim_y, dim_x, coord_y, coord_x, self._screen.RENDER_LAYER_MODALS)
        self._screen.add_window(self._window)

    @property
    def _max_cols(self):
        """
        Get the number of columns in a window of maximum size.

        """
        return math.floor(self._curses.COLS * self.WIN_MAX_PERCENT)

    @property
    def _max_lines(self):
        """
        Get the number of lines in a window of maximum size.

        """
        return math.floor(self._curses.LINES * self.WIN_MAX_PERCENT)

    @property
    def _min_cols(self):
        """
        Get the number of columns in a window of minimum size.

        """
        return math.floor(self._curses.COLS * self.WIN_MIN_PERCENT)

    @property
    def _min_lines(self):
        """
        Get the number of lines in a window of minimum size.

        """
        return math.floor(self._curses.LINES * self.WIN_MIN_PERCENT)

    @property
    def _percent_cols(self):
        """
        Get the percent of total screen columns currently used by window.

        Returns:
            float: The total screen columns muliplier, rounded to single
                digit after decimal.

        """
        return round(self._window.cols / self._curses.COLS, 1)

    @property
    def _percent_lines(self):
        """
        Get the percent of total screen lines currently used by window.

        Returns:
            float: The total screen lines muliplier, rounded to single
                digit after decimal.

        """
        return round(self._window.lines / self._curses.LINES, 1)

    def destroy(self):
        """
        Remove the region from the screen permanently.

        """
        self.hide()
        self._screen.remove_window(self._window)

    def hide(self):
        """
        Set current render layer to hidden.

        """
        self._window.hide()

    def show(self):
        """
        Set window's render layer to default.

        """
        self._window.show()


class ModalRegionPrompt(ModalRegionBase):
    """
    A class that represents a modal prompt "window."

    """

    def __init__(self, curses, screen, window_factory,
        prompt_string, string_factory):
        """
        Constructor.

        Args:
            prompt_string (string): Message to display to user above the actual
                user input line.

        """
        super().__init__(curses, screen, window_factory)

        self._prompt_string = None
        self._reserved_lines = 5
        self._string_factory = string_factory

        self._init_prompt_string(prompt_string)
        self._configure()

    def _configure(self):
        """
        Configure region/window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        self._window.border()

    def _erase(self):
        """
        Clear all window content and re-draw border.

        """
        self._window.erase()
        self._configure()

    def _init_prompt_string(self, prompt_string):
        """
        Validate string length, create string, and resize window if necessary.

        For instance, ensure that the prompt string is not too long to fit in
        a window of maximum size. Remember that space must be reserved for the
        actual prompt line into which user input is typed as well as space for
        the window's borders. Lines: subtract two for border and one for prompt.
        Columns: subtrat two for border.

        If string is too long for current window size, check if resize operation
        would allow it to fit. If a suitable size is found, resize window.
        Determine string coordinates and create string object.

        I'm not happy with the brute-force, iterative solution here. I could
        attempt a more intelligent solution using word counts, character counts,
        and guessing, but premature optimization is the root of all evil. One
        main problem is that it's not an issue of raw character count. The text
        wrapping breaks on words and/or hyphens and other rules. Therefore,
        only the textwrap library can answer if a given string will fit into a
        given number of lines.

        Args:
            prompt_string (string): The prompt string.

        Raises:
            ValueError: If string is too long to fit in window even at max size.

        """
        # If string too large for max window, no sense in continuing.
        max_avail_lines, max_avail_cols = self._get_avail_dimensions(
            self._max_lines, self._max_cols)
        max_lines_list = textwrap.wrap(prompt_string, width=max_avail_cols)
        if len(max_lines_list) > max_avail_lines:
            raise ValueError('Prompt string length exceeds window bounds.')

        # If prompt can fit into window at current size, it avoids a resize.
        # At this point, it is a given that the prompt string is short enough to
        # fit into at least a window of maximum size.
        current_lines_list = textwrap.wrap(
            prompt_string, width=self._avail_cols)

        # If string doesn't fit current size, find a size that does and resize.
        # Note that this will NOT preserve any established window proportions,
        # resetting the window dimensions to fixed percentages of the total
        # screen size.
        if len(current_lines_list) > self._avail_lines:
            multiplier_step = 0.1
            multiplier = self._percent_cols + multiplier_step
            while multiplier <= self.WIN_MAX_PERCENT:
                test_lines = math.floor(self._curses.LINES * multiplier)
                test_cols = math.floor(self._curses.COLS * multiplier)
                test_avail_lines, test_avail_cols = self._get_avail_dimensions(
                    test_lines, test_cols)
                test_line_list = textwrap.wrap(
                    prompt_string, width=test_avail_cols)
                if len(test_line_list) > test_avail_lines:
                    multiplier += multiplier_step
                else:
                    self._window.resize(test_lines, test_cols)
                    self._center_window()
                    break

        # Create string and write. Remember that the prompt string will be
        # written directly above the user input (prompt) line.
        # Because available dimensions are almost always less than total window
        # dimensions, one must find the origin of available area within the
        # window. The area of available space should be centered in the window
        # as much as possible.
        avail_origin_y, avail_origin_x = self._avail_origin
        lines_list = textwrap.wrap(prompt_string, width=self._avail_cols)
        coord_y, coord_x = self._get_centered_coords(
            self._avail_lines, self._avail_cols,
            len(lines_list), len(max(lines_list, key=len)))

        # Create and write the string.
        self._prompt_string = self._string_factory.create_string(
            self._window, '\n'.join(lines_list),
            avail_origin_y + coord_y, avail_origin_x + coord_x)
        self._prompt_string.write()

    def prompt(self):
        """
        Captures user input into a single line, returning input as string.

        Currently, the prompt is only a single line underneath the prompt string
        and is left-justified with prompt string. Note that this method converts
        the bytes object returned by window.getstr() into a string using the
        encoding contained in the curses object.

        Warning: window.getstr() implicitly calls a screen refresh.

        Raises:
            RuntimeError: If window is hidden when prompt is called.

        """
        # Throw an exception if prompt is called while window is hidden.
        if self._window.hidden:
            raise RuntimeError('Cannot issue prompt while window is hidden.')

        # The user input line should be on the first line underneath the prompt
        # string.
        coord_y = self._prompt_string.y + len(self._prompt_string.lines)
        coord_x = self._prompt_string.x

        # Start input polling.
        self._curses.echo()
        input_string = self._window.getstr(coord_y, coord_x)
        self._curses.noecho()

        return input_string.decode(self._curses.character_encoding)


class ModalLoadingAnim(ModalRegionBase):
    """
    A class that represents a modal loading animation "window."

    """
    def __init__(self, curses, screen, window_factory, string_factory):
        super().__init__(curses, screen, window_factory)

        self._current_animation = animation
        self._current_spinner = None
        self._curses = curses
        self._string_factory = string_factory

        self._configure()

    def _get_centered_coords(self, string):
        """
        Return a tuple of coordinates (y, x) that will place given string at
        center of window.

        Args:
            string (str): A single-line string.

        Raises:
            ValueError: If string is too long for window dimensions.

        """
        if len(string) > self.cols - 2:
            raise ValueError('String lenght exceeds window bounds')

        coord_x = round((self.cols - len(string)) / 2)
        coord_y = round((self.lines - 1) / 2)
        return (coord_y, coord_x)

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._configure_style()
        self.render_layer_default = self.RENDER_LAYER_BASE + 2
        self._render_layer_current = self.RENDER_LAYER_HIDDEN

    def _configure_style(self):
        """
        Reinitialize window styles tht can be cleared by calls to window.erase.

        Internal method for drawing borders and other decoration. Separated
        so that borders, for instance, can be redrawn after calls to
        window.erase() while style configuration is centralized.

        """
        self._window.border()

    def erase(self):
        """ Clear all window content and re-draw border.

        """
        self._window.erase()
        self._configure_style()

    def message(self, string):
        """
        Display a blank modal window save for a string of text characters.

        Currently, text string must not occupy more columns than those that are
        available in the window's dimensions.

        Raises:
            ValueError: If text string is too long for window dimensions.

        """
        self.erase()
        coord_y, coord_x = self._get_centered_coords(string)
        string_object = self._string_factory.create_string(
            self, string, coord_y, coord_x)
        string_object.write()

    def prompt(self, prompt_string):
        """ Clears window and displays a prompt for input to the user. Returns
        the entered string. Currently, the prompt string is only a single line
        and is rendered in the center of the window with the user input echoed
        below it.

        Warning: window.addstr() and/or window.getstr() implicitly call screen
        refreshes.

        Note that this converts the bytes object returned by window.getstr()
        into a string using the encoding contained in the curses object. In this
        instance, I favor fully abstracting curses' idiosyncrasies rather than
        forcing the higher level abstractions to handle all the various forms
        of return values.

        """
        # Throw an exception if prompt is called while window is hidden.
        if self._render_layer_current == self.RENDER_LAYER_HIDDEN:
            raise RuntimeError('Cannot issue prompt while window is hidden.')

        # Validate prompt string. Subtract two from columns to account for
        # window border.
        prompt_string_length = len(prompt_string)
        if prompt_string_length > self.cols - 2:
            raise ValueError('Prompt string exceeds window bounds.')

        # Draw prompt string. Prompt string and input line span two window lines
        # in total. In order for both prompt string and input line to appear
        # centered in modal, therefore, both lines must be shifted upward on y
        # axis by two lines.
        self.erase()
        prompt_string_coord_y, prompt_string_coord_x = \
            self._get_centered_coords(prompt_string)
        curses_prompt_string = self._string_factory.create_string(
            self._window,
            prompt_string,
            prompt_string_coord_y,
            prompt_string_coord_x)
        curses_prompt_string.write()

        # Start input polling. User's input will be displayed directly below
        # prompt.
        self._curses.echo()
        input_string = self._window.getstr(
            prompt_string_coord_y + 1, prompt_string_coord_x)
        self._curses.noecho()

        return input_string.decode(self._curses.character_encoding)

    def start_loading_animation(self):
        """
        Clear the window and enable the loading animation.
        """
        self.erase()
        self._current_animation.add_render_instance(
            self,
            round((self.lines - self._current_animation.lines) / 2),
            round((self.cols - self._current_animation.cols) / 2))
        self._current_animation.start()

    def stop_loading_animation(self):
        """
        Disable the animation and clear the window.

        """
        self._current_animation.stop()
        self.erase()


class MessageModalWindow:
    """ Manages the display and operation of a modal window on a rendering layer
    that will place it on top of existing windows. Hidden by default.

    Note that window.addstr() and/or window.getstr() contains implicit refresh.

    Attributes:
        PADDING_* (float) The "percent" of window cols and lines used as
            internal padding for the message. Calling code may wish to consider
            these values when deciding window size and submitting messages to
            the instances of this class. Value is per side.

    """

    PADDING = 0.2

    def __init__(self, window, signal_layer_change, string_factory):
        super().__init__(window, signal_layer_change)

        self._string_factory = string_factory

        self._configure()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._configure_style()
        self.render_layer_default = self.RENDER_LAYER_BASE + 2
        self._render_layer_current = self.RENDER_LAYER_HIDDEN

    def _configure_style(self):
        """
        Reinitialize window styles tht can be cleared by calls to window.erase.

        Internal method for drawing borders and other decoration. Separated
        so that borders, for instance, can be redrawn after calls to
        window.erase().

        """
        self._window.border()

    def _get_centered_coords(self, string):
        """
        Return a tuple of coordinates (y, x) that will place given string at
        center of window.

        Args:
            string (str): A single-line string.

        Raises:
            ValueError: If string is too long for window dimensions.

        """
        if len(string) > self.cols - 2:
            raise ValueError('String length exceeds window bounds')

        coord_x = round((self.cols - len(string)) / 2)
        coord_y = round((self.lines - 1) / 2)
        return (coord_y, coord_x)

    def erase(self):
        """ Clear all window content and re-draw border.

        """
        self._window.erase()
        self._configure_style()

    def message(self, message_string):
        """
        Display a blank modal window save for a string of text characters.

        Currently, text string must not occupy more columns than those that are
        available in the window's dimensions.

        Raises:
            ValueError: If text string is too long for window dimensions.

        """
        # Validate string.
        lines_list = textwrap.wrap

        self.erase()
        coord_y, coord_x = self._get_centered_coords(string)
        string_object = self._string_factory.create_string(
            self, string, coord_y, coord_x)
        string_object.write()

    @property
    def padding_cols(self):
        return self.cols


class ModalRegionFactory:
    """
    A class that hides creation details of modal regions at runtime.

    """
    def __init__(self, curses, screen, window_factory, string_factory):
        """
        Constructor.

        """
        self._curses = curses
        self._screen = screen
        self._string_factory = string_factory
        self._window_factory = window_factory

    def create_prompt(self, prompt_string):
        """
        Create and return a new instance of a prompt modal.

        """
        return ModalRegionPrompt(self._curses, self._screen,
            self._window_factory, prompt_string, self._string_factory)

    def create_message_modal(self, message_string):
        """
        Create a message modal window.

        Modal window is hidden by default. Although the message in the returned
        modal window can be publicly set, the passed message string will be
        preemptively set and will be ready for display when new window object is
        returned. No sense in making the calling code pass it twice.

        This method uses the length of the passed message to determine the size
        of the returned window. A margin will be left around the window so that
        it does not cover the entirety of the available screen space and padding
        will be placed inside the window so that borders do not conflict with
        the text. Window will be centered in screen.

        The message window class my impose its own message length restrictions.
        Any thrown exceptions will be allowed to propagate. This methd does not
        attempt to anticipate the message window's internal requirements.

        """
        pass


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
        self.string = string

        self._validate_string()

    def __len__(self):
        """
        Implement the length interface method for use with len().

        """
        return len(self.string)

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


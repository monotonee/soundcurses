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
        self._window.addstr(
            0, self._window.cols - len(help_string) - 1,
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
        self._window = window

    @property
    def username(self):
        """
        Get the currently-displayed username.

        The value of the username attribute will either be None or a
        curses string wrapper (CursesString) object instance.

        """
        username_string = None
        if self._username:
            username_string = self._username.value

        return username_string

    @username.setter
    def username(self, username):
        """
        Set the currently-displayed username.

        Yes, this is currently incompatible with too few window columns. The
        curses library will throw an exception from addstr() if there are too
        few columns to complete string write.

        """
        y_coord = math.floor((self._window.lines - 1) / 2)
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

    def __init__(self, window, string_factory, model):
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
        self._model = model
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
        for soubresource_name in self._model.avail_user_subresources:
            total_char_count += len(soubresource_name)
            self._nav_items[soubresource_name.upper()] = None

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
        Initialize the highlight iterator and highlight the first nav item.

        Called in constructor after the nav item initializer. Each item in cycle
        is a CursesString instance so "highlighting" is merely changing the
        displayed string's style in some contrasting way.

        """
        self._highlighted_item_cycle = itertools.cycle(
            iter(self._nav_items.values()))
        self._currently_highlighted_item = next(self._highlighted_item_cycle)
        self._set_highighted_style(self._currently_highlighted_item)

    def _set_highighted_style(self, item):
        """
        Set the passed item to the chosen highlight curses string style.

        This method simply centralizes the style.

        """
        item.style_reverse()

    @property
    def selected_item(self):
        """
        Get the value of the currently-selected nav item.

        Returns:
            string: The nav item value.

        """
        return self._currently_highlighted_item.value

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
            if item.value == self._currently_highlighted_item.value:
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

    Note that, when created, modal regions are visible by default.

    Attributes:
        RESERVED_COLS (int): The number of columns inside the window onto which
            nothing can be written. Used for padding, border lines, etc.
        RESERVED_LINES (int): The number of lines inside the window onto which
            nothing can be written. Used for padding, border lines, etc.
        WIN_MAX_PERCENT (float): The max size of the modal window relative to
            the screen dimensions.
        WIN_MIN_PERCENT (float): The min size of the modal window relative to
            the screen dimensions.

    """

    RESERVED_COLS = 4
    RESERVED_LINES = 4
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
        avail_lines = lines - self.RESERVED_LINES
        avail_cols = cols - self.RESERVED_COLS
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


class ModalRegionAnim(ModalRegionBase):
    """
    A class that represents a modal window containing some type of animation.

    When instantiated, animation is started by default, although it can be
    started and stopped manually by the calling code.

    """

    def __init__(self, curses, screen, window_factory, animation):
        """
        Constructor.

        """
        super().__init__(curses, screen, window_factory)

        self._animation = animation

        self._configure()
        self.start_animation()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        self._window.border()

    def start_animation(self):
        """
        Start enable the animation.

        """
        avail_origin_y, avail_origin_x = self._avail_origin
        coord_y, coord_x = self._get_centered_coords(
            self._avail_lines, self._avail_cols,
            self._animation.lines, self._animation.cols)
        self._animation.add_render_instance(
            self._window,
            avail_origin_y + coord_y,
            avail_origin_x + coord_x)
        self._animation.start()

    def stop_animation(self):
        """
        Stop the animation.

        """
        self._animation.stop()


class ModalRegionMessage(ModalRegionBase):
    """
    A class that represents a modal message window.

    """

    def __init__(self, curses, screen, window_factory,
        msg_string, string_factory):
        """
        Constructor.

        Args:
            msg_string (string): Message to display to user.

        """
        super().__init__(curses, screen, window_factory)

        self._msg_string = None
        self._string_factory = string_factory

        self._init_msg_string(msg_string)
        self._configure()

    def _configure(self):
        """
        Configure region/window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        self._window.border()

    def _init_msg_string(self, msg_string):
        """
        Validate string length, create string, and resize window if necessary.

        For instance, ensure that the string is not too long to fit in
        a window of maximum size. Remember that space must be reserved for the
        the window's borders.

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
            msg_string (string): The message string.

        Raises:
            ValueError: If string is too long to fit in window even at max size
                or string is empty.

        """
        # Validate message string.
        if not msg_string:
            raise ValueError('Message string is empty.')
        max_avail_lines, max_avail_cols = self._get_avail_dimensions(
            self._max_lines, self._max_cols)
        max_lines_list = textwrap.wrap(msg_string, width=max_avail_cols)
        if len(max_lines_list) > max_avail_lines:
            raise ValueError('Prompt string length exceeds window bounds.')

        # If prompt can fit into window at current size, it avoids a resize.
        # At this point, it is a given that the prompt string is short enough to
        # fit into at least a window of maximum size.
        current_lines_list = textwrap.wrap(msg_string, width=self._avail_cols)

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
                    msg_string, width=test_avail_cols)
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
        lines_list = textwrap.wrap(msg_string, width=self._avail_cols)
        coord_y, coord_x = self._get_centered_coords(
            self._avail_lines, self._avail_cols,
            len(lines_list), len(max(lines_list, key=len)))

        # Create and write the string.
        self._msg_string = self._string_factory.create_string(
            self._window, '\n'.join(lines_list),
            avail_origin_y + coord_y, avail_origin_x + coord_x)
        self._msg_string.write()


class ModalRegionHelp(ModalRegionBase):
    """
    A class that represents a modal message tht will display app key mappings.

    Passed the input mapper object that maps raw input to application actions,
    this specialized modal window will display a formatted listing of the keys
    and associated actions.

    """

    def __init__(self, curses, screen, window_factory,
        input_mapper, string_factory):
        """
        Constructor.

        Args:
            input_mapper (UserInputMapper): Contains key-to-action mappings.

        """
        super().__init__(curses, screen, window_factory)

        self._help_string = None
        self._string_factory = string_factory

        self._init_help_string(input_mapper)

    @staticmethod
    def _format_special_key_string(special_key_str):
        """
        Convert a special key input string into human-readable form.

        In the curses library, for example, the F1 keypress returns a string
        "KEY_F(1)". This is ugly and would confuse my mother. This function
        converts the raw string into the more common "F1" string.

        Returns:
            string: The formatted string.
        """
        formatted_str = special_key_str
        formatted_str = formatted_str.replace('KEY_', '')
        formatted_str = formatted_str.replace('(', '').replace(')', '')

        return formatted_str

    def _init_help_string(self, input_mapper):
        """
        Generate and write a help string from the available input mappings.

        """
        # Convert any special key strings into strings suitable for display.
        display_keymap = {}
        for key_str, action_str in input_mapper.keymap.items():
            if self._is_special_key(key_str):
                key_str = self._format_special_key_string(key_str)
            display_keymap[key_str] = action_str

        # Sort the key map dictionary by key.
        ordered_keymap = collections.OrderedDict(sorted(display_keymap.items()))

        # Build string lines list.
        lines_list = []
        for key_str, action_str in ordered_keymap.items():
            lines_list.append(key_str + ': ' + action_str)

        # Write string.
        avail_origin_y, avail_origin_x = self._avail_origin
        coord_y, coord_x = self._get_centered_coords(
            self._avail_lines, self._avail_cols,
            len(ordered_keymap), len(max(ordered_keymap.values(), key=len)))
        self._help_string = self._string_factory.create_string(
            self._window, '\n'.join(lines_list),
            avail_origin_y + coord_y, avail_origin_x + coord_x)
        self._help_string.write()

    @staticmethod
    def _is_special_key(key_string):
        """
        Determine whether the input key string is a special key value.

        In the curses library, for example, the F1 keypress returns a string
        "KEY_F(1)" nd is considered a special key string.

        Returns:
            bool: True if special key, false otherwise.

        """
        return key_string.startswith('KEY_')


class ModalRegionPrompt(ModalRegionMessage):
    """
    A class that represents a modal prompt "window."

    Differs from modal message by exposing a prompt functionality into which
    a user inputs text, echoed on the same line as it is typed. Therefore,
    an extra line must be reserved from the message string so that both the
    message and the prompt line will fit into the window.

    Attributes:
        RESERVED_LINES (int): Override the base constant, reserving an extra
            line for the prompt.

    """

    RESERVED_LINES = 5

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
        coord_y = self._msg_string.y + len(self._msg_string.lines)
        coord_x = self._msg_string.x

        # Start input polling.
        self._curses.echo()
        input_string = self._window.getstr(coord_y, coord_x)
        self._curses.noecho()

        return input_string.decode(self._curses.character_encoding)


class ModalRegionFactory:
    """
    A class that hides creation details of modal regions at runtime.

    """
    def __init__(self, curses, screen, window_factory, string_factory,
        spinner_anim, input_mapper):
        """
        Constructor.

        Args:
            spinner_anim (AbstractAnimation): The animation effect to place into
                the "spinner" modal window.

        """
        self._curses = curses
        self._input_mapper = input_mapper
        self._screen = screen
        self._spinner_anim = spinner_anim
        self._string_factory = string_factory
        self._window_factory = window_factory

    def create_help(self):
        """
        Create and return a new instance of a help modal.

        """
        return ModalRegionHelp(self._curses, self._screen,
            self._window_factory, self._input_mapper, self._string_factory)

    def create_message(self, msg_string):
        """
        Create and return a new instance of a message modal.

        """
        return ModalRegionMessage(self._curses, self._screen,
            self._window_factory, msg_string, self._string_factory)

    def create_prompt(self, prompt_string):
        """
        Create and return a new instance of a prompt modal.

        """
        return ModalRegionPrompt(self._curses, self._screen,
            self._window_factory, prompt_string, self._string_factory)

    def create_spinner(self):
        """
        Create and return a new instance of a "spinner" animation modal.

        """
        return ModalRegionAnim(self._curses, self._screen, self._window_factory,
            self._spinner_anim)


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


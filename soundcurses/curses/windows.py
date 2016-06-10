""" Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level classes.

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

    def __init__(self, window, signal_layer_change, screen, render_layer=None):
        """
        Constructor.

        """
        # Validate arguments.
        # Set default render layer value.
        if render_layer == None:
            render_layer = screen.RENDER_LAYER_BASE

        self._curses = curses
        self._render_layer_current = render_layer
        self._screen = screen
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
        render_layer_delta = int(new_render_layer) - self._render_layer_current
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


# class LayoutWindow():
    # """
    # Defines a base class that encapsulates a layout region.

    # Must be passed to the curses screen object in order to be rendered.

    # """

    # RENDER_LAYER_HIDDEN = 0
    # RENDER_LAYER_BASE = 1

    # def __init__(self, window, signal_layer_change):
        # """
        # Constructor.

        # _curses - The curses library interface. Necessary for many window
            # config tasks such as the utilization of constants, toggling
            # curses.echo()/curses.noecho(), etc.
        # _window - A raw curses window object.
        # render_layer_default - Ranges from 0 (lowest) to integer n (higher).
            # Layers are rendered from lowest to highest. Windows on the same
            # render layer will be rendered in arbitrary order. Attribute is
            # public so that callers can "reset" _render_layer_current through
            # render_layer property if needed.

        # """

        # # Declare instance attributes.
        # self._render_layer_current = self.RENDER_LAYER_BASE
        # self._window = window
        # self.render_layer_default = self.RENDER_LAYER_BASE
        # self.signal_layer_change = signal_layer_change

    # def __getattr__(self, name):
        # """
        # According to my current knowledge, allows attribute access
        # passthrough to underlying window object. If attribute is nonexistent,
        # AttributeError is raised by getattr() and allowed to bubble.
        # """
        # return getattr(self._window, name)

    # def _change_render_layer(self, new_render_layer):
        # """
        # Change render layer instance attribute and emit signal.
        # """
        # render_layer_delta = int(new_render_layer) - self._render_layer_current
        # self._render_layer_current = new_render_layer
        # self.signal_layer_change.emit(
            # window=self, delta=render_layer_delta)

    # @property
    # def cols(self):
        # """
        # Implement abstract method.

        # """
        # return self._window.getmaxyx()[1]

    # def hide(self):
        # """
        # Implement abstract method.

        # """
        # self._change_render_layer(self.RENDER_LAYER_HIDDEN)

    # @property
    # def lines(self):
        # """
        # Implement abstract method.

        # """
        # return self._window.getmaxyx()[0]

    # @property
    # def render_layer(self):
        # """
        # Implement abstract method.

        # """
        # return self._render_layer_current

    # def show(self):
        # """
        # Implement abstract method.

        # """
        # self._change_render_layer(self.render_layer_default)


# class BackgroundRegion:
    # """
    # A class that represents the background region of the screen.

    # The background region encompasses the entirety of the screen and usually
    # remains blank. It occupies the base render layer and therefore obscures
    # any windows placed on lower render layers.

    # Note the render layer value. This region must be rendered first since it
    # lies behind all other regions. Render_layer value remains at the default 0.
    # If rendered after other regions, this region will overlap them, resulting in
    # a blank screen.

    # """
    # def __init__(self, window):
        # """
        # Constructor.

        # """
        # self._window = window


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
        self.render_layer_default = self.RENDER_LAYER_BASE + 1
        self._render_layer_current = self.RENDER_LAYER_BASE + 1

    def _write_text(self):
        """
        Writes static text to the window.

        Text will not change at runtime. Yes, this is currently incompatible
        with too few columns. The curses library will throw an exception from
        addstr() if there are too few columns to complete string write.

        """
        self._window.addstr(0, 0, 'soundcurses - version 0.0.1')
        help_string = 'F1: help'
        self._window.addstr(0, self.cols - len(help_string) - 1, help_string)


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

        """
        return self._username

    @username.setter
    def username(self, username):
        """
        Set the currently-displayed username.

        Yes, this is currently incompatible with too few window columns. The
        curses library will throw an exception from addstr() if there are too
        few columns to complete string write.

        """
        self._username = username
        self._window.addstr(1, 1, username)


class NavWindow(LayoutWindow):
    """
    A curses window that manages the navigation region.

    Generally, since this application is largely based on the SoundCloud
    user, each navigation link is a user sub-resource. Examples include
    the current SoundCloud user's tracks, playlists, favorites, etc.

    The SoundCloud user subresource categories are pretty static. Therefore,
    this window will be hard-coded with a preset set of available menu items.
    The calling code will simply activate or deactivate them as necessary.

    """

    NAV_ITEM_01_TRACKS = 'TRACKS'
    NAV_ITEM_02_PLAYLISTS = 'PLAYLISTS'
    NAV_ITEM_03_FAVORITES = 'FAVORITES'
    NAV_ITEM_04_FOLLOWING = 'FOLLOWING'
    NAV_ITEM_05_FOLLOWERS = 'FOLLOWERS'

    def __init__(self, window, signal_layer_change,
        curses_string_factory):
        super().__init__(window, signal_layer_change)

        self._currently_highlighted_item = None
        self._curses_string_factory = curses_string_factory
        self._highlighted_item_cycle = None
        self._nav_items = collections.OrderedDict()

        self._configure()
        self._init_items()
        self._init_highlighted_item()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._window.border()
        self.render_layer_default = self.RENDER_LAYER_BASE + 1
        self._render_layer_current = self.RENDER_LAYER_BASE + 1

    def _init_items(self):
        """
        Write nav items to the nav window and select first highlighted item.

        Dynamically enumerates the NAV_ITEM_* constants and places them in a
        dictionary. Dict keys are nav item constant values, dict values are the
        CursesString objects of the character strings written to window.

        After writing, selects the nav item to be highlighted by default.

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

        # Calculate initial nav item string spacing within window.
        # For now, ignore edge case window sizes such as "very small."
        # TEMPORARILY assume that there are more available cols than characters.
        # Remove two cols from available cols for edge spacing/border.
        spacing_cols = math.floor(
            (self.cols - 2 - total_char_count) / (len(self._nav_items) - 1))

        # Create nav item string objects with spaced coords and write to window.
        # Place first nav item then place following items in a loop since first
        # item has no left-hand spacing.
        nav_item_iter =  iter(self._nav_items.keys())
        first_item = next(nav_item_iter)
        first_string = self._curses_string_factory.create_string(
            self._window, first_item, 1, 1)
        first_string.write()
        self._nav_items[first_item] = first_string

        # Write the remainder of the nav items to window.
        cols_offset = 1 + len(first_string) + spacing_cols
        for nav_item in nav_item_iter:
            nav_string = self._curses_string_factory.create_string(
                self._window, nav_item, 1, cols_offset)
            nav_string.write()
            self._nav_items[nav_item] = nav_string
            cols_offset += len(nav_string) + spacing_cols

    def _init_highlighted_item(self):
        """
        Initialize the highlight iterator and highlight the default nav item.

        Called in constructor after the nav item initializer.

        """
        self._highlighted_item_cycle = itertools.cycle(
            iter(self._nav_items.values()))
        self._currently_highlighted_item = next(self._highlighted_item_cycle)
        self._currently_highlighted_item.style_reverse()

    def highlight_next(self):
        """
        Highlight the next navigation item.

        """
        self._currently_highlighted_item.style_normal()
        self._currently_highlighted_item = next(self._highlighted_item_cycle)
        self._currently_highlighted_item.style_reverse()


class ContentWindow(LayoutWindow):
    """ A curses window that manages the content region. The content region's
    primary function is to display track listings, the constituent tracks of
    which may be selected and played.

    """
    def __init__(self, window, signal_layer_change, curses):
        super().__init__(window, signal_layer_change)

        self._curses = curses

        self._configure()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._window.border(
            ' ', ' ', 0, ' ',
            self._curses.ACS_HLINE, self._curses.ACS_HLINE, ' ', ' ')
        self.render_layer_default = self.RENDER_LAYER_BASE + 1
        self._render_layer_current = self.RENDER_LAYER_BASE + 1


class ModalWindow(AbstractCursesWindow):
    """
    A wrapper for a curses window that exposes modal-like behavior.

    This is a base class that provides common functionality for more specialized
    modal windows.

    """
    def __int__(self, curses, signal_layer_change):
        """
        Constructor.

        """
        self._curses = curses
        self._window = None
        self.signal_layer_change = signal_layer_change

    @property
    def cols(self):
        """
        Return the window's x-axis dimension in columns.

        Returns:
            int: The number of columns.

        """
        return self._window.getmaxyx()[1]

    def hide(self):
        """
        Set current render layer to hidden.

        When window is passed to rendering queue, will ensure that window is not
        visible upon next physical render.

        This method was defined so that calling code does not necessarily have
        to be aware of class constant attributes such as RENDER_LAYER_HIDDEN and
        may use this shorthand method over directly accessing render_layer
        attribute.
        """
        self._change_render_layer(self.RENDER_LAYER_HIDDEN)

    @property
    def lines(self):
        return self._window.getmaxyx()[0]

    @property
    def render_layer(self):
        return self._render_layer_current

    def show(self):
        """
        Set window's render layer to default.

        Often called to reverse the effects of a call to hide().
        """
        self._change_render_layer(self.render_layer_default)


class ModalWindow(LayoutWindow):
    """ Manages the display and operation of a modal window on a rendering layer
    that will place it on top of existing windows. Hidden by default.

    Note that window.addstr() and/or window.getstr() contains implicit refresh.

    """
    def __init__(self, window, signal_layer_change,
        curses, curses_string_factory, animation):
        super().__init__(window, signal_layer_change)

        self._current_animation = animation
        self._current_spinner = None
        self._curses = curses
        self._curses_string_factory = curses_string_factory

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
        string_object = self._curses_string_factory.create_string(
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
        curses_prompt_string = self._curses_string_factory.create_string(
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


class MessageModalWindow(LayoutWindow):
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

    def __init__(self, window, signal_layer_change, curses_string_factory):
        super().__init__(window, signal_layer_change)

        self._curses_string_factory = curses_string_factory

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
        string_object = self._curses_string_factory.create_string(
            self, string, coord_y, coord_x)
        string_object.write()

    @property
    def padding_cols(self):
        return self.cols



class ModalWindowFactory:
    """
    A class the allows the runtime creation of modal windows.

    """
    def __init__(self, curses, signal_layer_change,
        curses_string_factory, spinner_animation):
        """
        Constructor.

        """
        self._curses = curses
        self._curses_string_factory = curses_string_factory
        self._signal_layer_change = signal_layer_change
        self._spinner_animation = spinner_animation

    def create_prompt_modal(self):
        pass

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
        # Determine minimum window size.
        min_window_percent = 0.4
        min_dim_cols = self._curses.COLS * min_window_percent
        min_dim_lines = self._curses.LINES * min_window_percent


        # Validate message length.
        min_margin = 0.2
        max_win_cols = self._curses.COLS - (self._curses.COLS * min_margin)
        avail_cols = max_win_cols - (max_win_cols * MessageModalWindow.PADDING)
        max_win_lines = self._curses.LINES - (self._curses.LINES * min_margin)
        avail_lines = max_win_lines \
            - (max_win_lines * MessageModalWindow.PADDING)

        max_lines_list = textwrap.wrap(mesage_string, width=avail_cols)
        if len(max_lines_list) > avail_lines:
            raise ValueError('Message string will not fit in window.')

        # Calculate window size. If message fits into a window half of max size,
        # do it. Otherwise, create window at max size.
        window_cols = avail_cols
        window_lines = avail_lines
        test_lines_list = textwrap.wrap(mesage_string, width=(avail_cols / 2))
        if len(test_lines_list) <= avail_lines:
            window_cols /= 2
            window_lines /= 2

        return MessageModalWindow(
            self._curses.newwin(
                window_lines,
                window_cols,
                (self._curses.LINES - window_lines) / 2,
                (self._curses.COLS - window_cols) / 2),
            self._signal_layer_change,
            self._curses_string_factory)

    def create_text_modal(self):
        pass


class CursesString:
    """
    A class that maintains a string and its coordinates within a window.

    Facilitates the display of characters within a curses window. Collects
    a displayed string's coordinates within a window and makes operations such
    as moving, erasing, and overwriting strings easier.

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
            string: (string)
            y (int): The y-coord at which to initially write string.
            x (int): The x-coord at which to initially write string.
            attr (int): A curses attribute integer. Each bit represents a style.
                Ex: curses.A_BOLD

        Raises:
            ValueError
        """
        # Validate arguments.. Ensure y and x do not exceed window bounds.
        if y > window.lines or x > window.cols:
            raise ValueError('String coords exceed window bounds.')
        if attr == None:
            attr = curses.A_NORMAL

        self._coord_x = x
        self._coord_y = y
        self._curses = curses
        self._is_written = False
        self._string = string
        self._window = window
        self.attr = attr

    def __len__(self):
        """
        Implement the length interface method for use with len().

        """
        return len(self._string)

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
            self._window.chgat(
                self._coord_y,
                self._coord_x,
                len(self),
                self._attr)

    def erase(self):
        """
        Overwrite string with blank chars.

        """
        empty_string = ''.ljust(len(self))
        self._window.addstr(self._coord_y, self._coord_x, empty_string)
        self._is_written = False

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
        Get the internal string's value.

        """
        return self._string

    def write(self):
        """
        Write the string to the window.

        Curses does not care if string is re-written over identical string so no
        is_written check is performed.

        """
        self._window.addstr(
            self._coord_y,
            self._coord_x,
            self._string,
            self._attr)
        self._is_written = True

    @property
    def x(self):
        """
        Get the x-coordinate of window at which string is or will be written.

        """
        return self._coord_x

    @property
    def y(self):
        """
        Get the y-coordinate of window at which string is or will be written.

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


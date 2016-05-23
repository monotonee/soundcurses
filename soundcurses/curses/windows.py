""" Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level classes.

"""

class CursesWindow:
    """ Defines a base class that encapsulates a layout region, implemented
    using a curses window or panel.

    RENDER_LAYER_* - Standardize special render layer levels.
    RENDER_LAYER_HIDDEN - Windows rendered on this layer will be rendered
        behind stdscr and will therefore be invisible on physical screen.
        New windows default to this render layer.
    RENDER_LAYER_BASE - The base layer on which the stdscr window will
        (should) be rendered. Since stdscr is not used for rendering any UI
        components, will remain blank.

    """

    RENDER_LAYER_HIDDEN = 0
    RENDER_LAYER_BASE = 1

    def __init__(self, curses, window, signal_render_layer_change):
        """
        Constructor.

        _curses - The curses library interface.
        _window - A raw curses window object.
        render_layer_default - Ranges from 0 (lowest) to integer n (higher).
            Layers are rendered from lowest to highest. Windows on the same
            render layer will be rendered in arbitrary order. Attribute is
            public so that callers can "reset" _render_layer_current through
            render_layer property if needed.
        """

        # Declare instance attributes.
        self._curses = curses
        self._render_layer_current = self.RENDER_LAYER_BASE
        self._window = window
        self.render_layer_default = self.RENDER_LAYER_BASE
        self.signal_render_layer_change = signal_render_layer_change

    def __getattr__(self, name):
        """
        According to my current knowledge, allows attribute access
        passthrough to underlying window object. If attribute is nonexistent,
        AttributeError is raised by getattr() and allowed to bubble.
        """
        return getattr(self._window, name)

    def _change_render_layer(self, new_render_layer):
        """
        Change render layer instance attribute and emit signal.
        """
        render_layer_delta = int(new_render_layer) - self._render_layer_current
        self._render_layer_current = new_render_layer
        self.signal_render_layer_change.emit(
            window=self, delta=render_layer_delta)

    @property
    def cols(self):
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


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window above which other windows are
    rendered. In the curses library, stdscr often performs some special duties
    as well and this specialized subclass exposes the necessary interfaces.

    Note the render layer. stdscr must be rendered first since it
    lies behind all subwindows so render_layer value remains at the default 0.
    If rendered after subwindows, stdscr will overlap them, resulting in a blank
    screen since no content is rendered to stdscr.

    """
    def __init__(self, curses, window, signal_render_layer_change):
        super().__init__(curses, window, signal_render_layer_change)
        self._configure()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._window.nodelay(True)
        self.render_layer_default = self.RENDER_LAYER_BASE
        self._render_layer_current = self.RENDER_LAYER_BASE

    def get_character(self):
        """ Attempt to sample keypress from user.

        """
        try:
            key_pressed = self._window.getkey()
        except self._curses.error:
            key_pressed = None

        return key_pressed


class HeaderWindow(CursesWindow):
    """ A curses window that manages the header region. The header region is
    mostly a static data display.

    """
    def __init__(self, curses, window, signal_render_layer_change):
        super().__init__(curses, window, signal_render_layer_change)
        self._configure()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        # self._window.bkgd(' ', self._curses.color_pair(1))
        self.render_layer_default = self.RENDER_LAYER_BASE + 1
        self._render_layer_current = self.RENDER_LAYER_BASE + 1


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation region. The navigation
    region displays a SoundCloud user's available categories within which tracks
    may be present. Examples may include "tracks," "playlists," or "likes." The
    user may use the keyboard to select categories for track listings.

    """
    def __init__(self, curses, window, signal_render_layer_change):
        super().__init__(curses, window, signal_render_layer_change)
        self._configure()

    def _configure(self):
        """
        Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.
        """
        self._window.border()
        self.render_layer_default = self.RENDER_LAYER_BASE + 1
        self._render_layer_current = self.RENDER_LAYER_BASE + 1


class ContentWindow(CursesWindow):
    """ A curses window that manages the content region. The content region's
    primary function is to display track listings, the constituent tracks of
    which may be selected and played.

    """
    def __init__(self, curses, window, signal_render_layer_change):
        super().__init__(curses, window, signal_render_layer_change)
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


class ModalWindow(CursesWindow):
    """ Manages the display and operation of a modal window on a rendering layer
    that will place it on top of existing windows. Hidden by default.

    Note that window.addstr() and/or window.getstr() contains implicit refresh.

    """
    def __init__(self, curses, window, signal_render_layer_change, animation):
        super().__init__(curses, window, signal_render_layer_change)

        self._configure()

        self._current_animation = animation
        self._current_spinner = None

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
        """ Internal method for drawing borders and other decoration. Separated
        so that borders, for instance, can be redrawn after calls to
        window.erase() while style configuration is centralized.

        """
        self._window.border()

    def erase(self):
        """ Clear all window content and re-draw border.

        """
        self._window.erase()
        self._configure_style()

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

        prompt_string_length = len(prompt_string)
        window_dimensions = self._window.getmaxyx()

        # Validate prompt string. Subtract two from columns to account for
        # window border.
        if prompt_string_length > window_dimensions[1] - 2:
            raise ValueError('Prompt string will not fit in window.')

        # Draw prompt string. Prompt string and input line span two window lines
        # in total. In order for both prompt string and input line to appear
        # centered in modal, therefore, both lines must be shifted upward on y
        # axis by two lines.
        self.erase()
        prompt_string_coord_y = round((window_dimensions[0] - 2) / 2)
        prompt_string_coord_x = round(
            (window_dimensions[1] - prompt_string_length) / 2)
        self._window.addstr(
            prompt_string_coord_y, prompt_string_coord_x, prompt_string)

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

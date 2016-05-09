""" Module that defines wrapper classes designed to abstract raw curses windows
and to be passed to higher-level classes.

"""

class CursesWindow:
    """ Defines a base class that encapsulates a layout region, implemented
    using a curses window or panel.

    """

    def __init__(self, curses, window):
        """ Constructor.

        curses - The curses library interface.
        render_layer - Ranges from 0 (lowest) to integer n (higher). Layers are
            rendered from lowest to highest. Remains public so that render queue
            can access value. Windows on the same render layer will be rendered
            in arbitrary order.
        window - A raw curses window object.

        """
        # Declare instance attributes.
        self._curses = curses
        self._window = window
        self.render_layer = 0
        self.virtual_state_requires_update = True

        # Gather information and establish initial instance state.
        self._configure_window()

    def _configure_window(self):
        """ Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        pass

    def touch(self):
        """ Force curses to render window regardless of actual update to state.

        """
        self._window.touchwin()
        self.virtual_state_requires_update = True

    def update_virtual_state(self):
        """ Writes window state to curses' virtual screen state. Note the lack
        of checking whether or not the window state has changed.

        """
        self._window.noutrefresh()
        self._virtual_state_requires_update = False


class StdscrWindow(CursesWindow):
    """ Abstracts the main "stdscr" curses window above which other windows are
    rendered. In the curses library, stdscr often performs some special duties
    as well and this specialized subclass exposes the necessary interfaces.

    Note the render layer. stdscr must be rendered first since it
    lies behind all subwindows so render_layer value remains at the default 0.
    If rendered after subwindows, stdscr will overlap them, resulting in a blank
    screen since no content is rendered to stdscr.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.nodelay(True)

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

    def _configure_window(self):
        """ Override parent method.

        """
        # self._window.bkgd(' ', self._curses.color_pair(1))
        self.render_layer = 1


class NavWindow(CursesWindow):
    """ A curses window that manages the navigation region. The navigation
    region displays a SoundCloud user's available categories within which tracks
    may be present. Examples may include "tracks," "playlists," or "likes." The
    user may use the keyboard to select categories for track listings.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()
        self.render_layer = 1


class ContentWindow(CursesWindow):
    """ A curses window that manages the content region. The content region's
    primary function is to display track listings, the constituent tracks of
    which may be selected and played.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border(
            ' ', ' ', 0, ' ',
            self._curses.ACS_HLINE, self._curses.ACS_HLINE, ' ', ' ')
        self.render_layer = 1


class ModalPromptWindow(CursesWindow):
    """ Manages the display and operation of a modal window on a rendering layer
    that will place it on top of existing windows.

    Instances designed to be created and destroyed along with each modal window.

    Note that window.addstr() and/or window.getstr() contains implicit refresh.

    """

    def __init__(self, curses, window, prompt_string):
        """ Override parent method. Added prompt string parameter.

        """
        super().__init__(curses, window)
        if not self._validate_prompt_string(prompt_string):
            raise ValueError('Prompt string too long for modal window.')

        self._prompt_string = prompt_string

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()
        self.render_layer = 2

    def _validate_prompt_string(self, prompt_string):
        """ Called in the constructor.

        When rendered to the window, the prompt string must fit on a single
        line. The window may have a border so prompt string must have at least
        two fewer characters than the window has columns.

        Returns Boolean true if valid, false otherwise.

        """
        prompt_string_is_valid = False
        if len(prompt_string) < self._window.getmaxyx()[1] - 2:
            prompt_string_is_valid = True

        return prompt_string_is_valid

    def prompt(self):
        """ Prompts user for input and returns the entered string. Currently,
        the prompt string is only a single line and is rendered in the center of
        the window with the user input echoed below it.

        Note that window.addstr() and/or window.getstr() implicitly call screen
        refreshes.

        Note that this converts the bytes object returned by window.getstr()
        into a string using the encoding contained in the curses object. In this
        instance, I favor fully abstracting curses' idiosyncrasies rather than
        forcing the higher level abstractions to handle all the various forms
        of return values.

        """
        # Draw prompt string. In order for both prompt string and input line to
        # appear centered in modal, both lines must be shifted upward on y axis
        # by two lines.
        window_dimensions = self._window.getmaxyx()
        prompt_string_length = len(self._prompt_string)
        prompt_string_coord_y = round((window_dimensions[0] - 2) / 2)
        prompt_string_coord_x = round(
            (window_dimensions[1] - prompt_string_length) / 2)
        self._window.addstr(
            prompt_string_coord_y, prompt_string_coord_x, self._prompt_string)

        # Start input polling.
        self._curses.echo()
        input_string = self._window.getstr(
            prompt_string_coord_y + 1, prompt_string_coord_x)
        self._curses.noecho()

        return input_string.decode(self._curses.character_encoding)


class ModalWindowFactory:
    """ Creates and returns curses windows that are designed to act as modals.

    """

    POSITION_CENTER = 0

    def __init__(self, curses):
        """ Note that a curses stdscr object must have already been created in
        order for the terminal dimensions (such as curses.COLS) to be available.
        This class requires the values stored in curses.LINES and curses.COLS.

        """
        self._curses = curses

    def _get_window_coords(self, lines, cols, position):
        """ Given a desired position class constant and dimensions of a curses
        window, returns the coordinates at which the top left corner of the
        window should be placed. Returns a tuple of coords (y, x).

        Note that the x and y coord order is switched. Maintains consistency
        with curses library's standard (y, x) tuple.

        Returns tuple of integer coordinates (y, x).

        """
        if position == self.POSITION_CENTER:
            coord_y = round((self._curses.LINES - lines) / 2)
            coord_x = round((self._curses.COLS - cols) / 2)
        else:
            raise ValueError('Unknown positional constant.')

        return (coord_y, coord_x)

    def create_prompt_modal(self, lines, cols, prompt_string, position = None):
        """ Instantiate and return a new curses window designed to act as a
        modal window.

        """
        # Validate arguments.
        if lines > self._curses.LINES or cols > self._curses.COLS:
            raise ValueError('Modal window dimensions must not exceed ' +
                'available terminal dimensions.')
        if not position:
            position = self.POSITION_CENTER

        # Determine window top left vertex coordinates.
        coord_tuple = self._get_window_coords(lines, cols, position)

        # Create new window.
        return ModalPromptWindow(
            self._curses,
            self._curses.newwin(lines, cols, *coord_tuple),
            prompt_string)


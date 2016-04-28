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
        window - A raw curses window object.

        """
        # Declare instance attributes.
        self._curses = curses
        self._window = window
        self.render_priority = 0
        self.virtual_state_requires_update = True

        # Gather information and establish initial instance state.
        self._configure_window()

    def _configure_window(self):
        """ Configure window properties.

        Sets initial window state such as borders, colors, initial content, etc.
        Designed to be called only during object construction.

        """
        pass

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

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.nodelay(True)
        self.render_priority = 1

    def getch(self):
        """ Wrapper for internal curses window instance method.

        """
        return self._window.getch()


class HeaderWindow(CursesWindow):
    """ A curses window that manages the header region. The header region is
    mostly a static data display.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.bkgd(' ', self._curses.color_pair(1))
        # self._window.addstr(
            # 1, 2, 'Current user: Monotonee', self._curses.A_BOLD)


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


class ContentWindow(CursesWindow):
    """ A curses window that manages the content region. The content region's
    primary function is to display track listings, the constituent tracks of
    which may be selected and played.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()


class ModalWindow(CursesWindow):
    """ Manages the modal window into which users input a SoundCloud user name.

    """

    def _configure_window(self):
        """ Override parent method.

        """
        self._window.border()

    def prompt(self, prompt_string):
        """ Prompts user for input and returns the entered string. Currently,
        the prompt string is only a single line and is rendered in the center of
        the window with the user input echoed below it.

        """
        window_dimensions = self._window.getmaxyx()
        prompt_string_length = len(prompt_string)

        # Valiate arguments.
        # If prompt string character count exceeds max window column count minus
        # two (accounting for border), raise exception. This effectively
        # enforces a single-line prompt.
        if prompt_string_length > window_dimensions[1] - 2:
            raise ValueError('Prompt string too long for window.')

        # Draw prompt string. In order for both prompt string and input line to
        # appear centered in modal, both lines must be shifted upward on y axis
        # by two lines.
        prompt_string_coord_y = round((window_dimensions[0] - 2) / 2)
        prompt_string_coord_x = round(
            (window_dimensions[1] - prompt_string_length) / 2)
        self._window.addstr(
            prompt_string_coord_y,
            prompt_string_coord_x,
            prompt_string)

        # Start input polling.
        self._curses.echo()
        input_string = self._window.getstr(
            prompt_string_coord_y + 1, prompt_string_coord_x)
        self._curses.noecho()

        return input_string


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
        with curses library.

        """
        if position == self.POSITION_CENTER:
            coord_y = round((self._curses.LINES - lines) / 2)
            coord_x = round((self._curses.COLS - cols) / 2)
        else:
            raise ValueError('Unknown positional constant.')

        return (coord_y, coord_x)

    def create_modal(self, lines, cols, position = None):
        """ Instantiate and return a new curses window designed to act as a
        modal window.

        """
        # Validate arguments.
        if lines > self._curses.LINES or cols > self._curses.COLS:
            raise ValueError('Modal window dimensions must not exceed those ' +
                'of terminal.')
        if not position:
            position = self.POSITION_CENTER

        # Determine window coordinates.
        coord_tuple = self._get_window_coords(lines, cols, position)

        # Create new window.
        return ModalWindow(
            self._curses,
            self._curses.newwin(lines, cols, *coord_tuple))


""" Defines a set of classes that are capable of using curses to produce
TUI effects such as loading indicators.

"""

import abc
import itertools

class AbstractSpinner(metaclass=abc.ABCMeta):
    """ Defines an abstract base class for a loading indicator rendered with the
    curses library.

    """
    def __init__(self, screen, window):
        self._screen = screen
        self._window = window

    @property
    @abc.abstractmethod
    def lines(self):
        """ Returns the total number of lines the effect spans when rendered to
        the screen.

        """
        pass

    @abc.abstractmethod
    def start(self, y, x):
        """ Display the effect.

        """
        pass

    @abc.abstractmethod
    def stop(self):
        """ Display the effect.

        """
        pass

    @property
    @abc.abstractmethod
    def cols(self):
        """ Returns the total number of columns the effect spans when rendered
        to the screen.

        """
        pass


class SimpleSpinner(AbstractSpinner):
    """ When started, produces a classic text-based spinner consisting of
    sequential alternation of characters in the set of forward slash, em dash,
    backslash, and pipe.

    """
    def __init__(self, screen, window):
        super().__init__(screen, window)

        self._cols = 1
        self._coord_y = 0
        self._coord_x = 0
        self._lines = 1
        self._spinner_chars = ('/', '―', '\\', '|')
        self._spinner_chars_iterator = itertools.cycle(self._spinner_chars)

        self.active = False

    def _handle_screen_render(self, **kwargs):
        """ Designed to serve as the slot for the screen's signal that the
        physical curses screen has been rendered.

        """
        self._render_next_character()

    def _render_next_character(self):
        self._window.addstr(
            self._coord_y,
            self._coord_x,
            next(self._spinner_chars_iterator))

    @property
    def cols(self):
        """ Returns the total number of columns the effect spans when rendered
        to the screen.

        """
        return self._cols

    @property
    def lines(self):
        """ Returns the total number of lines the effect spans when rendered to
        the screen.

        """
        return self._lines

    def start(self, y, x):
        """ Enable the display of the effect on the next render cycle(s).

        """
        if not self.active:
            self._coord_y = y
            self._coord_x = x
            self.active = True
            self._screen.signal_rendered.connect(self._handle_screen_render)

    def stop(self):
        """ Disable the display of the effect on the next render cycle(s).

        """
        if self.active:
            self._screen.signal_rendered.disconnect(self._handle_screen_render)
            self._window.delch(self._coord_y, self._coord_x)
            self.active = False


class EffectsFactory:
    """ A class the manages the creation of effects objects.

    """

    def __init__(self, screen):
        self._screen = screen

    def create_simple_spinner(self, window):
        """ Create and return a spinner effect object.

        """
        return SimpleSpinner(self._screen, window)



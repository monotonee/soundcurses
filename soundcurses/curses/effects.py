""" Defines a set of classes that are capable of using curses to produce
TUI effects such as loading indicators.

"""

import abc
import itertools

class AbstractLoadingIndicator(metaclass=abc.ABCMeta):
    """ Defines an abstract base class for a loading indicator rendered with the
    curses library.

    """
    def __init__(self, screen, window)
        self._screen = screen
        self._window = window

    @property
    @abc.abstractmethod
    def height(self):
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
    def width(self):
        """ Returns the total number of columns the effect spans when rendered
        to the screen.

        """
        pass


class InfiniteIterator:
    def __init__(self, iterable):
        self._iterable = iterable)
        self._current_iterator = iter(iterable)

    def __iter__(self):
        return self

    def next(self):



class SimpleSpinner(AbstractLoadingIndicator):
    """ When started, produces a classic text-based spinner consisting of
    sequential alternation of characters in the set of pipe, forward slash,
    backslash, and em dash.

    """
    def __init__(self, screen, window):
        super().__init__(screen, window)

        self._coord_y = 0
        self._coord_x = 0
        self._height = 1
        self._spinner_chars = ('/', '—', '\\', '|')
        self._spinner_chars_iterator = itertools.cycle(self._spinner_chars)
        self._width = 1
        self.active = False

        self._screen.signal_rendered.connect(self._handle_screen_render)

    # def _create_new_iterator(self, iterable):
        # return iter(iterable)

    # def _get_next_character(self):
        # try:
            # next_character = self._spinner_chars_iterator.next()
        # except StopIteration:
            # self._spinner_chars_iterator = self._create_new_iterator(
                # self._spinner_chars)
            # next_character = self._spinner_chars_iterator.next()

    def _handle_screen_render(self, **kwargs):
        """ Designed to serve as the slot for the screen's signal that the
        physical curses screen has been rendered.

        """
        if self.active:
            self._render_next_character()

    def _render_next_character(self):
        self._window.addch(
            self._coord_y,
            self._coord_x,
            self._spinner_chars_iterator.next())

    @property
    def height(self):
        """ Returns the total number of lines the effect spans when rendered to
        the screen.

        """
        return self._height

    def start(self, y, x):
        """ Display the effect.

        """
        if not self.active:
            self._coord_y = y
            self._coord_x = x
            self._active = True

    def stop(self):
        """ Cease display of the effect.

        """
        if self.active:
            self._window.delch(self._coord_y, self._coord_x)
            self._active = False

    @property
    def width(self):
        """ Returns the total number of columns the effect spans when rendered
        to the screen.

        """
        return self._width


class EffectsFactory:
    """ A class the manages the creation of effects objects.

    """

    def __init__(self, screen):
        self._screen = screen

    def create_simple_spinner(self, window):
        """ Create and return a spinner effect object.

        """
        return SimpleSpinner(self._screen, window)



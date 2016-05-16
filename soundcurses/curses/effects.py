""" Defines a set of classes that are capable of using curses to produce
TUI effects such as loading indicators.

"""

import abc
import functools
import itertools

class AbstractAnimation(metaclass=abc.ABCMeta):
    """
    Defines an ABC for an animation rendered with the curses library.

    Attributes:
        _screen (CursesScreen): A reference to the curses screen object.

    """
    def __init__(self, screen):
        """
        Constructor.

        """
        self._screen = screen

    @property
    @abc.abstractmethod
    def lines(self):
        """
        Returns total number of lines the effect spans when rendered to screen.

        Returns:
            int: The number of lines.

        """
        pass

    @abc.abstractmethod
    def start(self):
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


class SimpleSpinner(AbstractAnimation):
    """
    When started, produces a classic text-based spinner consisting of
    sequential alternation of characters in the set of forward slash, em dash,
    backslash, and pipe.

    Attributes:
        _render_targets (list): A list of bound callables (partials). When
            called, will render to bound window at bound coords.

    """
    def __init__(self, screen):
        super().__init__(screen)

        self._cols = 1
        self._lines = 1
        self._render_targets = []
        self._spinner_chars = ('/', '―', '\\', '|')
        self._spinner_chars_iterator = itertools.cycle(self._spinner_chars)

        self.active = False

    def _add_render_instance(self, window, y, x):
        """
        Define a coordinate within a window at which the effect will be
        rendered.

        """
        self._render_targets.append(
            functools.partial(self._write_character, window, y, x))

    def _handle_screen_render(self, **kwargs):
        """
        Handle a screen rendering event.

        Designed to serve as the slot for the screen's signal that the
        physical curses screen has completed a rendering pass.

        """
        self._update_all_targets()

    def _update_all_targets(self):
        """
        Render next spinner frame to all targets.

        """
        character = next(self._spinner_chars_iterator)
        for render in self._render_targets:
            render(character)

    def _write_character(self, window, y, x, character):
        """
        Add a character to a window, overwriting any currently at coords.

        """
        window.addstr(y, x, character)

    @property
    def cols(self):
        return self._cols

    @property
    def lines(self):
        return self._lines

    def start(self):
        if not self.active:
            self.active = True
            self._screen.signal_rendered.connect(self._handle_screen_render)

    def stop(self):
        if self.active:
            self._screen.signal_rendered.disconnect(self._handle_screen_render)
            self.active = False


class EffectsFactory:
    """ A class the manages the creation of effects objects.

    """

    def __init__(self, screen):
        self._screen = screen

    def create_simple_spinner(self):
        """ Create and return a spinner effect object.

        """
        return SimpleSpinner(self._screen)


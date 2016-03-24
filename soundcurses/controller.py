""" Defines control-type classes.

"""

class CursesController:
    """ Handles user input receipt and response.

    """

    def __init(self, key_window, view):
        """ The key_window is the curses window from which user input is taken.

        Curses is expected to

        """

        self._key_window = key_window
        self._view = view

    def _start(self):
        # self.key_window.getkey()

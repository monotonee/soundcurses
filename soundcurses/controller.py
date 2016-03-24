""" Defines control-type classes.

"""

import sys

class CursesController:
    """ Handles user input receipt and response.

    """

    def __init(self, input_window, view):
        """ The input_window is the curses window from which user input is taken.

        """

        self._input_window = input_window
        self._view = view

        self._start_main_loop()

    def _start_main_loop(self):
        """ Contains main loop that will wait for and handle input.

        """

        self._input_window.nodelay()
        while True:
            key = None
            try:
                key = self.key_window.getkey()
            except Exception:
                print(sys.exc_infor()[2]
                break


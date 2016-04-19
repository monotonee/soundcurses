""" Defines control-type classes.

"""

class CursesController:
    """ Handles user input receipt and response.

    """

    def __init__(self, input_window, view):
        """ input_window is the curses window from which user input is polled.

        input_window Is expected to have nodelay mode enabled but nothing
        should break if it is not.

        """

        self._input_window = input_window
        self._view = view

        self._start_main_loop()

    def _start_main_loop(self):
        """ Contains main loop that will wait for and handle input.

        """

        while True:
            key = None
            try:
                key = self._input_window.get_key()
            except self._input_window.input_exception:
                pass
            else:
                if key == 'q':
                    break


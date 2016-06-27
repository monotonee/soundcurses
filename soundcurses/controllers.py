"""
Defines classes that act as application or GUI component controllers.

"""

import math
import time

class MainController:
    """
    Top-evel interface for application controller actions.

    Implements a basic state pattern context to provide dynamic behavior change.

    """

    def __init__(self, input_mapper, state_factory, view, model):
        """
        Constructor.

        """
        self._application_is_running = False
        self._current_state = None
        self._input_mapper = input_mapper
        self._model = model
        self._view = view

        initial_state = state_factory.create_no_username(self)
        self.set_state(initial_state)

    def _run_main_loop(self):
        """
        Begin running the main application loop.

        Performs such functions as rendering the screen and polling for input.

        """
        while self._application_is_running:
            input_string = self._view.sample_input()
            action = self._input_mapper.resolve_input(input_string)

            self._current_state.handle_action(action)
            self._current_state.run_interval_tasks()

            self._view.render()
            self._model.run_interval_tasks()

    def set_state(self, state):
        """
        Set internal state. Part of state pattern implementation.

        Args:
            state (BaseState): From local states module.

        """
        if self._current_state:
            self._current_state.stop()
        self._current_state = state
        self._current_state.start()

    def start_application(self):
        """
        Start the application.

        """
        self._application_is_running = True
        self._view.render()
        self._run_main_loop()

    def stop_application(self):
        """
        Stop the application.

        Public but almost always called internally.

        """
        self._application_is_running = False
        self._view.destroy()


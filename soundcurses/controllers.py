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
    def __init__(self, input_mapper, state_factory, view):
        """
        Constructor.

        """
        self._application_is_running = False
        self._current_state = None
        self._input_mapper = input_mapper
        self._view = view
        self._view_render_interval = 0.1

        initial_state = state_factory.create_no_username(self)
        self.set_state(initial_state)

    def _render_view(self):
        """
        Render the view on a specified interval.

        """
        timestamp_new = time.time()
        timestmap_last_render = self._view.last_render_timestamp
        if timestamp_new - timestmap_last_render >= self._view_render_interval:
            self._view.render()

    def _run_main_loop(self):
        while self._application_is_running:
            input_string = self._view.sample_input()
            action = self._input_mapper.resolve_input(input_string)
            self._current_state.handle_input(action)
            self._current_state.run_interval_tasks()
            self._render_view()

    def set_state(self, state):
        """
        Set internal state. Part of state pattern implementation.

        Args:
            state (BaseState): From local states module.

        """
        self._current_state = state
        self._current_state.enter()

    def start_application(self):
        """
        Start the application.
        """
        self._application_is_running = True
        self._view.render()
        self._run_main_loop()

    def stop_application(self):
        """
        Stop the application. Public but likely called internally.
        """
        self._application_is_running = False
        self._view.destroy()


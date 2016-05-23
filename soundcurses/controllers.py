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
    def __init__(self, view, input_resolver, model):
        """
        Constructor.
        """
        self._application_is_running = False
        self._current_state = None
        self._input_resolver = input_resolver
        self._model = model
        self._view = view
        self._view_render_interval = 0.5

    def _run_main_loop(self):
        while self._application_is_running:
            input_string = self._view.sample_input()
            action = self._input_resolver.resolve_input(input_string)
            self._handle_input(input_string)
            self._render_view()

    def _render_view(self):
        timestamp_new = math.trunc(time.time())
        timestmap_last_render = math.trunc(self._view.last_render_timestamp)
        if timestamp_new - timestmap_last_render >= self._view_render_interval:
            self._view.render()

    def _handle_input(self, input_string):
        """
        Begin necessary tasks in reaction to user input.
        """
        if input_string == 'q':
            self.stop_application()
        elif input_string == 'u':
            username = self._view.prompt_username()
            self._view.show_loading_animation()
            # user = self._model.resolve_username(username)

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


"""
This module defines view classes that are designed to expose coarse
interfaces to controller classes for the manipulation of the curses TUI.

"""

import time

class MainView:
    """ Highest-level view designed to control broad functions often associated
    with curses' stdscr. Manipulated by the main controller class.

    """

    def __init__(self, input_source, screen, model,
        region_status, region_nav, region_content, modal_factory):
        """ Constructor.

        input_source - Provides an interface for receiving input events from
            the curses library.
        screen - An abstracted interface for the display of the various curses
            components in a "composited" TUI view.

        """
        self._input_source = input_source
        self._modal_factory = modal_factory
        self._modal_message = None
        self._model = model
        self._region_content = region_content
        self._region_status = region_status
        self._region_nav = region_nav
        self._screen = screen

        self._subscribe_to_model()

    def _subscribe_to_model(self):
        """
        Connect to the model object's events.

        """
        self._model.signal_change_current_track_set.connect(
            self._handle_current_track_set_change)
        self._model.signal_change_current_user.connect(
            self._handle_current_user_change)

    def _handle_current_user_change(self, **kwargs):
        """
        Respond to an update of the current user data.

        """
        self._region_status.username = self._model.current_user.username

    def _handle_current_track_set_change(self, **kwargs):
        """
        Respond to an update of the current track set data.

        """
        pass

    def destroy(self):
        """
        Relinquish control of the screen. Revert terminal settings.
        """
        self._screen.destroy()

    def hide_loading_animation(self):
        """
        Stop the loading animation and hide the modal window.

        """
        self._window_modal.stop_loading_animation()
        self._window_modal.hide()

    def hide_message(self):
        self._modal_message.destroy()

    @property
    def last_render_timestamp(self):
        return self._screen.last_render_timestamp

    def prompt_username(self):
        """
        Display a modal input window into which the user will enter a
        valid SoundCloud username.

        """
        modal_prompt = self._modal_factory.create_prompt('enter username: ')
        modal_prompt.show()
        username = modal_prompt.prompt()
        modal_prompt.destroy()

        return username

    def render(self):
        self._screen.render()

    def sample_input(self):
        """ Starts polling for input from curses windows.

        """
        return self._input_source.sample_input()

    def show_loading_animation(self):
        """ Displays a modal window in which an animated spinner is rendered.

        Designed to indicate that the program is waiting for some task to
        complete.

        """
        self._window_modal.start_loading_animation()
        self._window_modal.show()

    def show_message(self, message):
        """
        Display a message in a modal window.

        """
        self._modal_message = self._modal_factory.create_message(message)
        self._modal_message.show()

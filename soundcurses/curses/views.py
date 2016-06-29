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
        self._modal_loading = None
        self._modal_help = None
        self._modal_message = None
        self._model = model
        self._region_content = region_content
        self._region_status = region_status
        self._region_nav = region_nav
        self._screen = screen

        self._connect_to_model()

    def _connect_to_model(self):
        """
        Connect to the model object's events.

        """
        self._model.signal_change_current_user.connect(
            self._handle_current_user_change)

    def _handle_current_user_change(self, **kwargs):
        """
        Respond to an update of the current user data.

        """
        self._region_status.username = self._model.current_user.username

    @property
    def current_content_lines(self):
        """
        Get the lines currently displayed in the content region.

        Returns:
            list: A list of strings.

        """
        return self._region_content.content_lines

    @current_content_lines.setter
    def current_content_lines(self, lines_list):
        """
        Set the lines of content to be displayed in the content region.

        Args:
            lines_list (list): A list of strings.

        """
        self._region_content.content_lines = lines_list

    def destroy(self):
        """
        Relinquish control of the screen. Revert terminal settings.

        """
        self._screen.destroy()

    def hide_help(self):
        """
        Hide the help modal window.

        NOOP if no modal help has been created.

        """
        if self._modal_help:
            self._modal_help.destroy()
            self._modal_help = None

    def hide_loading_indicator(self):
        """
        Hide the loading indicator.

        NOOP if no loading indicator has been created.

        """
        if self._modal_loading:
            self._modal_loading.destroy()
            self._modal_loading = None

    def hide_message(self):
        """
        Hide the message modal window.

        NOOP if no modal message has been created.

        """
        if self._modal_message:
            self._modal_message.destroy()
            self._modal_message = None

    @property
    def last_render_timestamp(self):
        """
        Get the Unix timestamp of the last call to render the curses screen.

        Call is delegated to the screen abstraction object.

        Returns:
            int: A Unix timestamp.

        """
        return self._screen.last_render_timestamp

    def prompt_username(self):
        """
        Display a window into which the user will enter a SoundCloud username.

        Returns:
            string: A string of the user's input. Should be a SoundCloud
                username.

        """
        modal_prompt = self._modal_factory.create_prompt('enter username: ')
        modal_prompt.show()
        username = modal_prompt.prompt()
        modal_prompt.destroy()

        return username

    def render(self):
        """
        Execute a single rendering pass of the view.

        Delegated to the screen abstraction object.

        """
        self._screen.render()

    def sample_input(self):
        """
        Execute a single sampling of input from the designated polling window.

        """
        return self._input_source.sample_input()

    def select_next_nav_item(self):
        """
        Select the next nav item in the nav region.

        """
        self._region_nav.select_next_item()

    @property
    def selected_nav_item(self):
        """
        Return the currently-selected navigation item.

        Returns:
            string: The currently-selected nav item.

        """
        return self._region_nav.selected_item

    def show_help(self):
        """
        Display a modal window with help and/or a key map.

        """
        if self._modal_help:
            self._modal_help.destroy()
        self._modal_help = self._modal_factory.create_help()

    def show_loading_indicator(self):
        """
        Display an indication to the user that the application is waiting.

        Designed to indicate that the program is waiting for some task to
        complete.

        """
        if self._modal_loading:
            self._modal_loading.destroy()
        self._modal_loading = self._modal_factory.create_spinner()

    def show_message(self, message):
        """
        Display a message in a modal window.

        """
        if self._modal_message:
            self._modal_message.destroy()
        self._modal_message = self._modal_factory.create_message(message)

""" Main entry point

"""

# Standard library imports.
import curses
import locale

# Third-party imports.
import signalslot
import soundcloud

# Local imports.
import soundcurses.controllers
import soundcurses.models
from soundcurses.curses import (components, screen, views, windows)

def main(stdscr):
    """ Compose curses windows and pads.

    Note that stdscr is passed into the main function by curses.wrapper().

    """

    curses_wrapper = soundcurses.curses.components.CursesWrapper(curses, locale)

    # Compose curses window wrappers.
    signal_window_render_layer_changed = signalslot.Signal(
        args=['window', 'delta'])
    signal_window_state_changed = signalslot.Signal(
        args=['window'])
    window_stdscr = soundcurses.curses.windows.StdscrWindow(
        curses_wrapper,
        stdscr,
        signal_window_render_layer_changed,
        signal_window_state_changed)
    window_header = soundcurses.curses.windows.HeaderWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 0, 0),
        signal_window_render_layer_changed,
        signal_window_state_changed)
    window_nav = soundcurses.curses.windows.NavWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 3, 0),
        signal_window_render_layer_changed,
        signal_window_state_changed)
    window_content = soundcurses.curses.windows.ContentWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            curses_wrapper.LINES - 6,
            curses_wrapper.COLS,
            6, 0),
        signal_window_render_layer_changed,
        signal_window_state_changed)
    # Create reusable modal window 40% of screen size, centered in screen.
    # Is hidden by default.
    window_modal_dim_y = round(curses_wrapper.LINES * 0.4)
    window_modal_dim_x = round(curses_wrapper.COLS * 0.4)
    window_modal = soundcurses.curses.windows.ModalWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            window_modal_dim_y,
            window_modal_dim_x,
            round((curses_wrapper.LINES - window_modal_dim_y) / 2),
            round((curses_wrapper.COLS - window_modal_dim_x) / 2)),
        signal_window_render_layer_changed,
        signal_window_state_changed)

    # Compose screen.
    signal_rendered = signalslot.Signal()
    render_queue = soundcurses.curses.screen.WindowRenderQueue()
    curses_screen = soundcurses.curses.screen.CursesScreen(
        curses_wrapper,
        render_queue,
        signal_rendered,
        window_stdscr,
        window_header,
        window_nav,
        window_content,
        window_modal)

    # Compose input source.
    signal_keypress = signalslot.Signal(args=['code_point'])
    input_source = soundcurses.curses.components.InputSource(
        window_stdscr,
        signal_keypress)

    # Compose view(s).
    effects_factory = souncurses.effects.EffectsFactory(curses_screen)
    main_view = soundcurses.curses.views.MainView(
        input_source,
        curses_screen,
        window_header,
        window_nav,
        window_content,
        window_modal)

    # Compose model.
    soundcloud_client = soundcloud.Client(
        client_id='e9cd65934510bf631372af005c2f37b5',
        use_ssl=True)
    main_model = soundcurses.models.MainModel(soundcloud_client)

    # Compose controllers.
    nav_controller = soundcurses.controllers.NavRegionController(main_view)
    content_controller = soundcurses.controllers.ContentRegionController(
        main_view)
    main_controller = soundcurses.controllers.MainController(
        main_view,
        main_model,
        nav_controller,
        content_controller)
    signal_keypress.connect(main_controller.handle_input_keypress)

    main_controller.start_application()



curses.wrapper(main)

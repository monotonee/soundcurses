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
import soundcurses.model
import soundcurses.curses.components
import soundcurses.curses.views
import soundcurses.curses.windows

def main(stdscr):
    """ Compose curses windows and pads.

    Note that stdscr is passed into the main function by curses.wrapper().

    """

    curses_wrapper = soundcurses.curses.components.CursesWrapper(curses, locale)

    # Compose curses window wrappers.
    window_stdscr = soundcurses.curses.windows.StdscrWindow(curses_wrapper, stdscr)
    window_header = soundcurses.curses.windows.HeaderWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 0, 0))
    window_nav = soundcurses.curses.windows.NavWindow(
        curses_wrapper,
        curses_wrapper.newwin(3, curses_wrapper.COLS, 3, 0))
    window_content = soundcurses.curses.windows.ContentWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            curses_wrapper.LINES - 6,
            curses_wrapper.COLS,
            6, 0))
    window_modal_username = soundcurses.curses.windows.UsernameModalWindow(
        curses_wrapper,
        curses_wrapper.newwin(
            curses_wrapper.LINES - int(curses_wrapper.LINES * 0.3),
            curses_wrapper.COLS - int(curses_wrapper.COLS * 0.2),
            4, 4))

    # Compose screen.
    curses_screen = soundcurses.curses.components.CursesScreen(
        curses_wrapper,
        window_stdscr,
        window_header,
        window_nav,
        window_content,
        window_modal_username)

    # Compose input source.
    signal_keypress = signalslot.Signal(args=['code_point'])
    input_source = soundcurses.curses.components.InputSource(
        window_stdscr,
        signal_keypress)

    # Compose views.
    main_view = soundcurses.curses.views.MainView(
        input_source,
        curses_screen,
        window_header,
        window_nav,
        window_content,
        window_modal_username)

    # Compose controllers.
    nav_controller = soundcurses.controllers.NavRegionController(main_view)
    content_controller = soundcurses.controllers.ContentRegionController(
        main_view)
    main_controller = soundcurses.controllers.MainController(
        main_view,
        nav_controller,
        content_controller)
    signal_keypress.connect(main_controller.handle_input_keypress)
    main_controller.start_application()

    # Compose model.
    # soundcloud_client = soundcloud.Client(
        # client_id='e9cd65934510bf631372af005c2f37b5',
        # use_ssl=True)
    # print(
        # soundcloud_client.get(
            # '/resolve', url='https://soundcloud.com/monotonee'))

    # model = soundcurses.model.CursesModel(soundcloud_client)

curses.wrapper(main)

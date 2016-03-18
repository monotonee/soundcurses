""" Main entry point

"""

from soundcurses.views import CursesView
import sys
import time

def main():

    # Temporary try/catch during testing
    # This is bad form.
    view = None
    try:
        view = CursesView()
        time.sleep(5)
        view.destroy()
    finally:
        print('You dun goofed', sys.exc_info()[0])
        view.destroy()
        raise

main()

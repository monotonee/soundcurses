# Setuptools
# from setuptools import setup, find_packages

# setup(
    # # Standard data
    # name=  'soundcurses',
    # version = '0.1.0',
    # packages = find_packages(),
    # install_requires = [
        # 'pinject',
        # 'soundcoud',
    # ],

    # # PyPI metadata
    # author = 'monotonee',
    # author_email = 'monotonee@tuta.io',
    # description = 'A curses-based front end for the SoundCloud',
    # license = 'MIT',
    # keywords = 'cli curses  music ncurses soundcloud terminal',
    # url = '',
# )

# Distutils
# Example: https://github.com/google/pinject/blob/master/setup.py
from distutils.core import setup

setup(
    # Standard data
    name=  'soundcurses',
    version = '0.1.0',
    packages = ['signalslot', 'soundcurses'],

    # PyPI metadata
    author = 'monotonee',
    author_email = 'monotonee@tuta.io',
    description = 'A curses-based front end for the SoundCloud',
    license = 'MIT',
    url = '',
)

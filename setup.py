from setuptools import setup, find_packages

setup(
    name='soundcurses',
    version='0.0.1',
    author='monotonee',
    author_email='monotonee@tuta.io',
    packages=find_packages(),
    install_requires=[
        'requests',
        'signalslot',
        'soundcloud',
    ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    description='A curses-based terminal UI for SoundCloud.',
    license='MIT',
    keywords='cli curses  music ncurses soundcloud terminal',
    url='https://github.com/monotonee/soundcurses',
)

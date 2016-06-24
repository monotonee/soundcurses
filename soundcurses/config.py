"""
This module defines various classes and functions for interacting with
application configurations and exposing them to the application components
that need them at runtime.

"""

class UserInputMapper:
    """
    Responsible for resolving raw user input to application actions.

    Contains a series of constants that can be used by the application instead
    of raw character strings or code points, allowing for more flexible key
    mapping in the future. While currently very rudimentary, collecting this
    functionality in a class will make user-configurable mapping much easier to
    implement.

    Currently key mapping is constrained to one-to-one relationships.

    Note that in ncurses, there is a built-in delay with the escpe key.

    See: http://en.chys.info/2009/09/esdelay-ncurses/

    """

    ACTION_ENTER_USERNAME = 'Enter username'
    ACTION_CLOSE = 'Close window'
    ACTION_HELP = 'Help'
    ACTION_QUIT = 'Quit'

    def __init__(self):
        """
        Establish instance input-to-action mapping.

        """
        self._keymap = {}

        self._populate_keymap()

    def _populate_keymap(self):
        """
        Determine key mappings and populate the keymap dictionary.

        Listed in ascending alphanumerical order by key.

        """
        self._keymap['q'] = self.ACTION_QUIT
        self._keymap['u'] = self.ACTION_ENTER_USERNAME

        self._keymap['KEY_F(1)'] = self.ACTION_HELP
        self._keymap['c'] = self.ACTION_CLOSE

    @property
    def keymap(self):
        """
        Get the keymap dictionary.

        The keys are raw key value strings as received from the curses library.
        This is placed into a getter property so that callign code cannot change
        the dictionary, either intentionally or unintentionally.

        Returns:
            dictionary: Keys are raw input stirngs, values are action constants.

        """
        return self._keymap

    def resolve_input(self, input_string):
        """
        Translate a raw input string into an action constant.

        An input string is typically the string representation of a keypress
        or mouse event.

        Returns:
            Class ACTION_* constant if mapping exists, None otherwise.

        """
        return self._keymap.get(input_string, input_string)

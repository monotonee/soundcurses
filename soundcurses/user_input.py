"""
This module defines application actions and provides input mapping functions.

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

    """

    ACTION_ENTER_USERNAME = 'Enter username'
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

    def resolve_input(self, input_string):
        """
        Translate a raw input string into an action constant.

        An input string is typically the string representation of a keypress
        or mouse event.

        Returns:
            Class ACTION_* constant if mapping exists, None otherwise.

        """
        return self._keymap.get(input_string, input_string)

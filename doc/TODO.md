Enforce Python standard line widths
Add repo URL to setup.py
Fix setup.py dependencies and verify correct format
Decide on distutis or setuptools
Catch TUI window initialization errors
What if user tries to run entry script from outside terminal window?
Account for window resize
Change window title bar text if in window?
Reevaluate strict use of IoC. Favor unittest.mock instead?
Config file read and write to user home
Create facade services to reduce constructor injection param count
Move curses subwindow simension definitions into window classes?
Switch non-modal windows to subwindows of stdscr?
Evaluate and counter edge cases with modal window such as coord and dimension conflicts
Write proper doc blocks for all entities
Use PEP8/Pythonic style compliance checker (PyLint, flake8?)
Detect terminal color support and use color pallette if available.
Create Makefile with installation, tests, etc.
Before launch, update dependencies, test, and re-freeze.
Reevaluate prudence of storing locale and char encoding in curses wrapper
Write argument "type" checks using method and attribute presence (duck typing)?
alphabetize module entities in module files
Make state factory use object pool?
Reduce coupling between state objects and application components by using command objects?
Remove the MainController's depenence on the StateFactory?
Add more descriptive errors to soundcloud wrapper for various API conditions.
    Ex: One error for unresolved username, another for actual HTTP errors.
Hard-code in config the min column screen dimensions
    Gracefully handle too-narrow screen dimensions.
Hold weak references to windows in the the screen object?
Improve bute-force iterative window resizing check in ModalRegionPrompt
Ensure that a window cannot be added to the screen object twice.
Cache user subresources such as tracks and favorites lists in a local DB of some sort.

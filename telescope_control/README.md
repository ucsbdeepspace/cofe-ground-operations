TelescopeControl
================

Code for controlling Galil motion-control based telescopes

The main program is in main.py, and it can be run by entering 'python main.py' in a terminal, or by simply double clicking if on Windows. 

Requires:

 - Python 2.7
 - PyEphem
 - wxPython >= 2.8
 - BitString (https://code.google.com/p/python-bitstring/)
 - PyOpenGL (python-opengl)
 - pyftgl
 - numpy

Galil comms are handled by the PyGalil submodule, main repository at: https://github.com/fake-name/PyGalil

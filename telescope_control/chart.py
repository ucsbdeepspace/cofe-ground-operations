# chart.py
# wx widget for showing a chart of objects
#   (note: depends on python-opengl)

from OpenGL.GL import *
import sys
import wx
from wx import glcanvas

class Chart (glcanvas.GLCanvas):
    
    def __init__ (self, parent):
        super(Chart, self).__init__(self, parent, -1)
        self.context = glcanvas.GLContext(self)
        self.setCurrent(self.context)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        
        # initialize OpenGL
        width, height = self.GetSize()
        self.resize(width, height)
        glDisable(GL_DEPTH_TEST)
        
    def on_resize (self, event):
        width, height = event.GetSize()
        self.resize(width, height)
        
    # resize: update 2D OpenGL display with new size
    #   width, height: new chart size (pixels)
    def resize (self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)

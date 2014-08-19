# chart.py
# wx widget for showing a chart of objects
#   (note: depends on python-opengl)

from OpenGL.GL import *
import sys
import wx
from wx import glcanvas

class Chart (glcanvas.GLCanvas):
    
    def __init__ (self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        
        # drawing settings
        self.path = [] # list of points [x, y]
        self.center = [0, 0]
        self.h_fov = 20 # horizontal field of view
        
        # initialize OpenGL
        width, height = self.GetSize()
        self.resize(width, height)
        glDisable(GL_DEPTH_TEST)
    
    # event handlers
    def on_resize (self, event):
        width, height = event.GetSize()
        self.resize(width, height)
    
    def on_paint (self, event):
        wx.PaintDC(self)
        self.SetCurrent(self.context)
        self.draw()
        
    # resize: update 2D OpenGL display with new size
    #   width, height: new chart size (pixels)
    def resize (self, width, height):
        self.width = width
        self.height = height
        
        # set up view so top-left is (0, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)
    
    # project: convert from sky coordinates to screen coordinates
    #          using equirectangular projection
    #   sky_coord -> [crd_a, crd_b]: position of object in the sky
    def project (self, sky_coord):
        
        # find displacement of sky coordinate from center of screen
        displace = [(sky_coord[0] - self.center[0]) % 360,
                     sky_coord[1] - self.center[1]]
        
        # transform (-360, 360) -> [0, 360)
        if displace[0] < 0:
            displace[0] += 360
        # transform [0, 360) -> (-180, 180]
        if displace[0] > 180:
            displace[0] -= 360
        
        # compute pixels per degree from horizontal field of view
        pix_per_deg = self.width / self.h_fov
        
        # convert displacement from center in sky coordinates into displacement
        # in screen coordinates and compute final screen position
        return [0.5 * self.width  + displace[0] * pix_per_deg,
                0.5 * self.height - displace[1] * pix_per_deg]
    
    # draw: draw all objects onto the screen
    

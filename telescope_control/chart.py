# chart.py
# wx widget for showing a chart of objects
#   (depends: python-opengl, pyftgl)

import ephem
import FTGL
import math
from OpenGL.GL import *
import sys
import wx
from wx import glcanvas

import circle

class Chart (glcanvas.GLCanvas):
    
    def __init__ (self, parent, fov_ctrl, converter):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        self.converter = converter
        
        # load font
        self.font = FTGL.BitmapFont("fonts/DejaVuSans.ttf")
        self.font.FaceSize(12)
        
        # field of view indicator widget
        self.fov_ctrl = fov_ctrl
        
        # drawing settings
        self.path = [] # list of points [crd_a, crd_b]
        self.given_equ = False # whether the path points are equatorial
        self.scan_center = [0, 0] # center of scan
        self.curpos_h = [0, 0] # current pointing direction in horiz coordinates
        self.h_fov = 100.0 # horizontal field of view
        self.show_equ = False # whether to show in equatorial coordinates
        self.cen_curscan = False # center the current scan
                                 #   (otherwise, center current position)
        
        # event handlers
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.scroll_fov)
        
        self.initialized = False
    
        
    # initialize OpenGL
    def gl_init (self):
        self.initialized = True
        self.resize(self.width, self.height)
        
        glDisable(GL_DEPTH_TEST) # using 2D drawing, so no depth
        glClearColor(0, 0, 0, 1) # black background
        
        # enable antialiasing on lines
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    
    # event handlers
    def on_resize (self, event):
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.resize(size.width, size.height)
        
        self.Refresh()
        event.Skip()
    
    def on_paint (self, event):
        wx.PaintDC(self)
        self.SetCurrent(self.context)
        self.draw()
        self.SwapBuffers()
        
        event.Skip()
    
    # scrolling to change field of view directly on the sky chart
    def scroll_fov (self, event):
        if self.h_fov < 20 or \
                int(self.h_fov) == 20 and event.GetWheelRotation() > 0:
            self.h_fov += -1 * float(event.GetWheelRotation()) / 120
            
        elif self.h_fov < 60 or \
                int(self.h_fov) == 60 and event.GetWheelRotation() > 0:
            self.h_fov += -2 * float(event.GetWheelRotation()) / 120
            
        elif self.h_fov < 100 or \
                int(self.h_fov) == 100 and event.GetWheelRotation() > 0:
            self.h_fov += -4 * float(event.GetWheelRotation()) / 120
            
        elif self.h_fov < 180 or \
                int(self.h_fov) == 180 and event.GetWheelRotation() > 0:
            self.h_fov += -8 * float(event.GetWheelRotation()) / 120
            
        else:
            self.h_fov += -20 * float(event.GetWheelRotation()) / 120
        
        # constrain to range [1, 340]
        if self.h_fov > 340:
            self.h_fov = 340.0
        elif self.h_fov < 1:
            self.h_fov = 1.0
        
        # show new value on field of view indicator
        self.fov_ctrl.SetValue(self.h_fov)
        
        self.Refresh()
        event.Skip()


    # resize: update 2D OpenGL display with new size
    #   width, height: new chart size (pixels)
    def resize (self, width, height):
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        
        # set up view so top-left is (0, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


    # project: convert from sky coordinates to screen coordinates
    #          using equirectangular projection
    #   sky_coord -> [crd_a, crd_b]: position of object in the sky
    #   sky_center -> [crd_a, crd_b]: position to be centered on
    def project (self, sky_coord, sky_center):
        
        # find displacement of sky coordinate from center of screen
        displace = [(sky_coord[0] - sky_center[0]) % 360.0,
                     sky_coord[1] - sky_center[1]]
        
        # transform [0, 360) -> (-180, 180]
        if displace[0] > 180:
            displace[0] -= 360
        
        # compute pixels per degree from horizontal field of view
        pix_per_deg = self.width / self.h_fov
        
        # convert displacement from center in sky coordinates into displacement
        # in screen coordinates and compute final screen position
        if self.show_equ: # -> right ascension increases to the left
            return 0.5 * self.width  - displace[0] * pix_per_deg, \
                   0.5 * self.height - displace[1] * pix_per_deg
        else: # show horizontal system -> azimuth increases to the right
            return 0.5 * self.width  + displace[0] * pix_per_deg, \
                   0.5 * self.height - displace[1] * pix_per_deg

    # project_point: convert to display sky coordinates, then project
    #
    #   point -> [crd_a, crd_b]: position in given coordinate system
    def project_point (self, point):
        
        # convert to proper coordinate system
        if self.given_equ and not self.show_equ: # equatorial -> horizontal
            az, el = self.converter.radec_to_azel(
                math.radians(point[0]), math.radians(point[1]))
            sky_coord = [math.degrees(az), math.degrees(el)]
            
        elif not self.given_equ and self.show_equ: # horizontal -> equatorial
            ra, de = self.converter.azel_to_radec(
                math.radians(point[0]), math.radians(point[1]))
            sky_coord = [math.degrees(ra), math.degrees(de)]
        
        else: # already in correct coordinates
            sky_coord = point[:]
        
        return self.project (sky_coord, self.center_display())

    
    # center_display: get center of screen in display sky coordinates
    def center_display (self):
        
        # center on current position
        if not self.cen_curscan:
            
            # need to convert to equatorial
            if self.given_equ:
                cur_ra, cur_de = \
                self.converter.azel_to_radec(
                    math.radians(self.curpos_h[0]),
                    math.radians(self.curpos_h[1]))
                return [math.degrees(cur_ra), math.degrees(cur_de)]
            
            # no need to convert to equatorial
            else:
                return self.curpos_h[0], self.curpos_h[1]
        
        # find scan center in proper coordinate system
        elif self.given_equ and not self.show_equ: # equatorial -> horizontal
            cen_az, cen_el = \
                self.converter.radec_to_azel(
                    math.radians(self.scan_center[0]),
                    math.radians(self.scan_center[1]))
            return [math.degrees(cen_az), math.degrees(cen_el)]
        
        elif not self.given_equ and self.show_equ: # horizontal -> equatoria
            cen_ra, cen_de = \
                self.converter.azel_to_radec(
                    math.radians(self.scan_center[0]),
                    math.radians(self.scan_center[1]))
            return [math.degrees(cen_ra), math.degrees(cen_de)]
        
        else: # already in correct coordinates
            return self.scan_center[:]
    

    # draw: draw all objects onto the screen
    def draw (self):
        if not self.initialized:
            self.gl_init()
        
        glClear(GL_COLOR_BUFFER_BIT) # clear previous drawing
        
        ##
        # draw grid
        ##
        glLineWidth(2.5)          # width of 2.5px
        glColor(0.5, 0.5, 0.5)    # gray
        glLineStipple(2, 0xAAAA)  # dashed lines
        glEnable(GL_LINE_STIPPLE)
        
        # mark frequency
        if self.h_fov >= 150:
            mark = 30
        elif self.h_fov >= 50:
            mark = 10
        elif self.h_fov >= 25:
            mark = 5
        elif self.h_fov >= 10:
            mark = 2
        else: # self.h_fov < 10
            mark = 1
        
        # vertical lines
        for azi in range(0, 360/mark):
            point = self.project([azi * mark, 0], self.center_display())
            if -1 < point[0] < self.width - 30:
                # draw line
                glBegin(GL_LINES)
                glVertex(point[0], 0)
                glVertex(point[0], self.height - self.font.line_height)
                glEnd()
                
                # draw label
                text = str(azi * mark)
                glRasterPos(point[0] - 0.5 * self.font.Advance(text),
                            self.height - 5)
                self.font.Render(text)
        
        # horizontal lines
        for alt in range(-90/mark, 90/mark + 1):
            point = self.project([0, alt * mark], self.center_display())
            if -1 < point[1] < self.height - self.font.line_height:
                
                # draw line
                glBegin(GL_LINES)
                glVertex(0, point[1])
                glVertex(self.width - 30, point[1])
                glEnd()
                
                # draw label
                text = str(alt * mark)
                glRasterPos(self.width - self.font.Advance(text) - 5,
                            point[1] + 3)
                self.font.Render(text)
        
        glDisable(GL_LINE_STIPPLE)
        
        ##
        # draw the path
        ##
        glLineWidth(3)         # width of 3px
        glColor(0.8, 0.8, 0.8) # light gray
        glBegin(GL_LINE_STRIP)
        
        prev_pt = False # previous actual point specified in path
        prev_x, prev_y = 0, 0 # previous point including intermediate points
        for next_pt in self.path:
            
            # intermediate points
            if prev_pt:
                x, y = self.project_point(prev_pt)
                
                # check whether we need to break the list for wrap-around
                if x < 0 and prev_x > self.width or \
                   x > self.width and prev_x < 0 or \
                   y < 0 and prev_y > self.height or \
                   y > self.height and prev_y < 0:
                    glEnd()
                    glBegin(GL_LINE_STRIP)
                else:
                    glVertex(x, y)
                
                prev_x, prev_y = x, y
                ang_dist = circle.distance(prev_pt, next_pt)
                bearing = circle.bearing(prev_pt, next_pt)
                
                # generate list of intermediate points to slew to
                num_int = int(ang_dist) # one intermediate point per degree
                
                for i in range(1, num_int + 1):
                    a, b = circle.waypoint(prev_pt, bearing,
                        i * ang_dist / num_int)
                    x, y = self.project_point([a, b])
                    
                    # check whether we need to break the list for wrap-around
                    if x < 0 and prev_x > self.width or \
                       x > self.width and prev_x < 0 or \
                       y < 0 and prev_y > self.height or \
                       y > self.height and prev_y < 0:
                        glEnd()
                        glBegin(GL_LINE_STRIP)
                    else:
                        glVertex(x, y)
                    
                    prev_x, prev_y = x, y
                
            prev_pt = next_pt
        
        # add in last point
        if prev_pt:
            x, y = self.project_point(prev_pt)
            if not (x < 0 and prev_x > self.width or \
                    x > self.width and prev_x < 0 or \
                    y < 0 and prev_y > self.height or \
                    y > self.height and prev_y < 0):
                glVertex(x, y)
        
        glEnd()
        
        ##
        # show a cross-hair at the current position
        ##
        glColor(1, 1, 1)
        glLineWidth(4)
        
        # convert current position to be same as path coordinates
        if self.given_equ:
            cur_ra, cur_de = \
                self.converter.azel_to_radec(
                    math.radians(self.scan_center[0]), math.radians(self.scan_center[1]))
            curpos = [math.degrees(cur_ra), math.degrees(cur_de)]
        else: # already in horizontal coordinates
            curpos = self.curpos_h[:]
        
        x, y = self.project_point(curpos)
        
        # draw cross hair
        glBegin(GL_LINES)
        
        # top
        glVertex(x, y - 10)
        glVertex(x, y - 3)
        
        # right
        glVertex(x + 10, y)
        glVertex(x + 3, y)
        
        # bottom
        glVertex(x, y + 10)
        glVertex(x, y + 3)
        
        # left
        glVertex(x - 10, y)
        glVertex(x - 3, y)
        
        glEnd()
        
        glFlush()

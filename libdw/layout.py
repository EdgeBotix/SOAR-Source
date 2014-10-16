from Tkinter import *
import tkFileDialog
import math
import re
from tkMessageBox import *
import sig # new
import simulate
reload(simulate) # new

black = '#000000'
brown = '#AB6533'
red = '#FF0000'
# orange = '#FF7F00' # looks like red on windows
orange = '#FFBF3F'
yellow = '#FFFF00'
green = '#00FF00'
blue = '#0000FF'
violet = '#FF00FF'
gray = '#7F7F7F'
white = '#FFFFFF'
body = '#CFCFCF'

##############
# globals
##############

filename = ''       # saved filename
oldfilename = ''    # initial value for file dialogs and 'Revert'
simfilename = ''    # simulate filename

Changed = False
oldChanged = False
mousedown = False

# A primitive, one level unDo/Do is now on a button and 'u' key 

lastAction = None
lastComponent = None
# accumulated total motion for mouse dragging
movingdx = 0
movingdy = 0
newwireflag = False # when starting a new wire

# Set global Changed flag and put file name in window title bar

def setChanged(change):
    global Changed
    if Changed and change: return # ignore if already changed
    Changed = change
    if filename == '': title = 'CMax'
    else: title = filename
    if Changed: root.title(title + ' (*)') # indicate needs saving
    else: root.title(title) # just file name in window title 

def getChanged():
    return Changed

# Avoid placing duplicate components on top of each other, including resistors
# NOTE: this is *not* invoked after moving a component ...

def isDuplicate(c, clist):
    if c.label[0:2] == 'hr':
        for cl in clist:
            if cl.label[0:2] == 'hr' and cl.x == c.x and cl.y == c.y:
                removeComponent(cl)
                return False
        return False
    elif c.label[0:2] == 'vr':
        for cl in clist:
            if cl.label[0:2] == 'vr' and cl.x == c.x and cl.y == c.y:
                removeComponent(cl)
                return False
        return False
    else:   # not a resistor
        cstr = str(c)
        for cl in clist:
            if str(cl) == cstr:
                return True
        return False

def addComponent(c, canvas):
    global lastAction, lastComponent
    if isDuplicate(c, componentList):
        print 'Duplicated component %s.'%(c)
    else:
        lastComponent = c  # remember for Undo
        lastAction = 'add'
        setChanged(True)
        c.add(canvas)
        componentList.append(c)

def removeComponent(c):
    global lastAction, lastComponent
    setChanged(True)
    c.erase()
    lastComponent = c  # remember for Undo
    lastAction = 'remove'
    componentList.remove(c)

def unDo(): # primitive one level undo feature 
    global lastAction,lastComponent,movingdx,movingdy
    if lastAction == 'remove': 
        lastAction = None
        addComponent(lastComponent, workCanvas) 
        # gets put back as an 'add' (for Redo)
    elif lastAction == 'add':
        lastAction = None
        removeComponent(lastComponent)
        # gets put back as a 'remove' (for Redo)
    elif lastAction == 'moving':
        if movingdx != 0 or movingdy != 0:
            lastComponent.move(-movingdx,-movingdy)
            # flip sign (for Redo)
            movingdx = -movingdx
            movingdy = -movingdy
    elif lastAction == 'wiring':
        removeComponent(lastComponent)
        lastComponent.x -= movingdx
        lastComponent.y -= movingdy
        # check whether *both* ends need moving
        if lastComponent.label[0:2] == 'wi':
            if not lastComponent.atendflag: 
                lastComponent.x0 -= movingdx
                lastComponent.y0 -= movingdy
        addComponent(lastComponent, workCanvas)
        # flip sign (for Redo)
        movingdx = -movingdx
        movingdy = -movingdy
        lastAction = 'wiring'
    elif lastAction == 'rightshift':
        ShiftLeft()
    elif lastAction == 'leftshift':
        ShiftRight()

# grid(i,j) returns the pixel coordinates (x,y) of grid location i,j
# 1,1 -> upper right
# 63,23 -> lower left
# see proto.jpg
def gridx(i): # new
    return 12*(67-i)
def gridy(j): # new
    return 12*(j+3)
def grid(i,j):
#    return (12*(67-i),12*(j+3))
    return (gridx(i),gridy(j))

# ijgrid(x,y) returns the grid location (i,j) with pixel coordinates x,y
def igrid(x):
    return 67-x/12.
def jgrid(y):
    return y/12.-3
def ijgrid(x,y):
    return (igrid(x),jgrid(y))

# pin(i,j) returns the pixel coordinates (x,y) of pin i,j
# 1 <= i <= 63
# 1 <= j <= 10
def pin(i,j):
    if j>5:
        j += 3
    return grid(i,j+5)

# bus(i,j) returns the pixel coordinates (x,y) of bus i,j
# 1 <= i <= 63
# 1 <= j <= 4
# only certain bus locations are valid: see valid(i,j)
def bus(i,j):
    if j>2:
        j += 19
    j -= 5
    return grid(i,j+5)

# bussed(i) return true iff there is a bus connection at grid(i,*)
def bussed(i):
    return i>2 and i<62 and (i-2)%6!=0

# draw a connector at grid location z = (x,y)
def drawConnector(z):
    (x,y) = z
    workCanvas.create_rectangle(x-2,y-2,x+2,y+2,fill='gray',outline='gray')

# label grid location z = (x,y) as a
def label(z,a):
    (x,y) = z
    workCanvas.create_text(x,y,text=a,font=('Helvetica',9,'normal'))

# label a bus line
def busLine(y,a,color):
    (x0,y0) = grid(2,y)
    (x1,y1) = grid(62,y)
    workCanvas.create_line(x0,y0,x1,y1,fill=color)
    label(grid(0,y),a)
    label(grid(64,y),a)

id = 999
def getLabel(prefix):
    global id
    id += 1
    return prefix+str(id)[1:]

class component:
    def erase(self):
        setChanged(True)
        for p in self.parts:
            self.canvas.delete(p)
    def move(self,dx,dy):
        if dx == 0 and dy == 0: return # nothing to do 
        setChanged(True)
        self.x += dx
        self.y += dy
        for p in self.parts:
            self.canvas.move(p,dx,dy)

class hresistor(component):
    def __init__(self,z,c1,c2,c3):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1+24,y1)
        (self.c1,self.c2,self.c3) = (c1,c2,c3)
        self.label = getLabel('hr')
    def add(self, canvas):
        (x0,y0) = (self.x, self.y)
        (c1, c2,c3) = (self.c1,self.c2,self.c3)
        self.parts = [canvas.create_rectangle(x0-26,y0-2,x0+26,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-21,y0-8,x0+21,y0+8,fill=body,outline=gray,tags=self.label),
                      canvas.create_rectangle(x0-17,y0-7,x0-12,y0+7,fill=colors[c1],outline=colors[c1],tags=self.label),
                      canvas.create_rectangle(x0-7,y0-7,x0-2,y0+7,fill=colors[c2],outline=colors[c2],tags=self.label),
                      canvas.create_rectangle(x0+3,y0-7,x0+8,y0+7,fill=colors[c3],outline=colors[c3],tags=self.label)]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-21,y0-7,x0+21,y0+7,fill=None,outline=red,width=3,tags=('highlight',self.label))
        if shiftDown: # do this only if Shift key is down
            newValue[0]=self.c1 # transfer value of this resistor to newResistor
            newValue[1]=self.c2
            newValue[2]=self.c3
            menuCResCanvas.delete(newResistor,newResValue) # clear newResistor
            drawNewResistor()   # redraw newResistor
    def inside(self,x,y):
        return self.x-26<x<self.x+26 and self.y-8<y<self.y+8
    def in1(self,x,y):
        return self.y-10<y<self.y+10 and self.x-19<x<self.x-8
    def in2(self,x,y):
        return self.y-10<y<self.y+10 and self.x-9<x<self.x+2
    def in3(self,x,y):
        return self.y-10<y<self.y+10 and self.x+1<x<self.x+14
    def __str__(self):
        return 'resistor(%d,%d,%d): (%d,%d)--(%d,%d)'%(self.c1,self.c2,self.c3,
                          igrid(self.x-24),jgrid(self.y),igrid(self.x+24),jgrid(self.y))

class vresistor(component):
    def __init__(self,z,c1,c2,c3):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1-24)
        (self.c1,self.c2,self.c3) = (c1,c2,c3)
        self.label = getLabel('vr')
    def add(self,canvas):
        (x0,y0) = (self.x, self.y)
        (c1, c2,c3) = (self.c1,self.c2,self.c3)
        self.parts = [canvas.create_rectangle(x0-2,y0-26 ,x0+2,y0+26,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-8,y0-21 ,x0+8,y0+21,fill=body,outline=gray,tags=self.label),
                      canvas.create_rectangle(x0-7,y0-17 ,x0+7,y0-12,fill=colors[c1],outline=colors[c1],tags=self.label),
                      canvas.create_rectangle(x0-7,y0-7,x0+7,y0-2,fill=colors[c2],outline=colors[c2],tags=self.label),
                      canvas.create_rectangle(x0-7,y0+3,x0+7,y0+8,fill=colors[c3],outline=colors[c3],tags=self.label)]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-7,y0-21,x0+7,y0+21,fill=None,outline=red,width=3,tags=('highlight',self.label))
        if shiftDown: # do this only if Shift key is down
            newValue[0]=self.c1 # transfer value of this resistor to newResistor
            newValue[1]=self.c2
            newValue[2]=self.c3
            menuCResCanvas.delete(newResistor,newResValue)
            drawNewResistor()   # redraw newResistor
    def inside(self,x,y):
        return self.x-10<x<self.x+10 and self.y-26<y<self.y+26
    def in1(self,x,y):
        return self.x-10<x<self.x+10 and self.y-19<y<self.y-8
    def in2(self,x,y):
        return self.x-10<x<self.x+10 and self.y-9<y<self.y+2
    def in3(self,x,y):
        return self.x-10<x<self.x+10 and self.y+1<y<self.y+14
    def __str__(self):
        return 'resistor(%d,%d,%d): (%d,%d)--(%d,%d)'%(self.c1,self.c2,self.c3,
                          igrid(self.x),jgrid(self.y-24),igrid(self.x),jgrid(self.y+24))

class fopamp(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1+18,y1-24)
        self.label = getLabel('fo')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-20,y0-25,x0-16,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-8,y0-25,x0-4,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+4,y0-25,x0+8,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+16,y0-25,x0+20,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-24,y0-19,x0+24,y0+19,fill=gray,outline=black,tags=self.label),
                      canvas.create_oval(x0-21,y0+4,x0-11,y0+14,fill=body,outline=black,tags=self.label)]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-24,y0-19,x0+24,y0+19,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-24<x<self.x+24 and self.y-25<y<self.y+25
    def __str__(self):
        return 'opamp: (%d,%d)--(%d,%d)'%(igrid(self.x-18),jgrid(self.y+24),igrid(self.x-18),jgrid(self.y-24))

class iopamp(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1-18,y1+24)
        self.label = getLabel('io') # should be here
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
#       self.label = getLabel('io') # not here
        self.parts = [canvas.create_rectangle(x0-20,y0-25,x0-16,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-8,y0-25,x0-4,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+4,y0-25,x0+8,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+16,y0-25,x0+20,y0+25,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-24,y0-19,x0+24,y0+19,fill=gray,outline=black,tags=self.label),
                      canvas.create_oval(x0+21,y0-4,x0+11,y0-14,fill=body,outline=black,tags=self.label)]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-24,y0-19,x0+24,y0+19,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-24<x<self.x+24 and self.y-25<y<self.y+25
    def __str__(self):
        return 'opamp: (%d,%d)--(%d,%d)'%(igrid(self.x+18),jgrid(self.y-24),igrid(self.x+18),jgrid(self.y+24))

class fpot(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1+12,y1-12)
        self.label = getLabel('fp')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-20,y0-20,x0+20,y0+20,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-14,y0+9,x0-10,y0+13,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-13,x0+2,y0-9,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+10,y0+9,x0+14,y0+13,fill=black,outline=black,tags=self.label),
                      canvas.create_oval(x0-11,y0-9,x0+11,y0+13,fill=body,outline=black,tags=self.label),
                      canvas.create_text(x0,y0+2,text='pot',font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-20,y0-20,x0+20,y0+20,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-20<x<self.x+20 and self.y-15<y<self.y+15
    def __str__(self):
        return 'pot: (%d,%d)--(%d,%d)--(%d,%d)'%(igrid(self.x-12),jgrid(self.y+12),igrid(self.x),jgrid(self.y-12),igrid(self.x+12),jgrid(self.y+12))

class ipot(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1-12,y1+12)
        self.label = getLabel('ip')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-20,y0-20,x0+20,y0+20,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-14,y0-13,x0-10,y0-9,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-9,x0+2,y0+13,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+10,y0-13,x0+14,y0-9,fill=black,outline=black,tags=self.label),
                      canvas.create_oval(x0-11,y0-13,x0+11,y0+9,fill=body,outline=black,tags=self.label),
                      canvas.create_text(x0,y0-2,text='pot',font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-20,y0-20,x0+20,y0+20,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-20<x<self.x+20 and self.y-15<y<self.y+15
    def __str__(self):
        return 'pot: (%d,%d)--(%d,%d)--(%d,%d)'%(igrid(self.x+12),jgrid(self.y-12),igrid(self.x),jgrid(self.y+12),igrid(self.x-12),jgrid(self.y-12))

class fmotor(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('fm')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-76,y0+10,x0+16,y0-100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-62,y0-2,x0-58,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-50,y0-2,x0-46,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-38,y0-2,x0-34,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-26,y0-2,x0-22,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-14,y0-2,x0-10,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0-30,y0-65,text='Motor',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-30,y0-50,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0,y0-15,text='1',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-12,y0-15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-24,y0-15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-36,y0-15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-48,y0-15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-60,y0-15,text='6',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-76,y0+10,x0+16,y0-100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-76<x<self.x+16 and self.y-100<y<self.y+10
    def __str__(self):
        return 'motor: (%d,%d)--(%d,%d)'%(igrid(self.x-6),jgrid(self.y),igrid(self.x-68),jgrid(self.y))

class imotor(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('im')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-16,y0-10,x0+76,y0+100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+10,y0-2,x0+14,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+22,y0-2,x0+26,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+34,y0-2,x0+38,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+46,y0-2,x0+50,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+58,y0-2,x0+62,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0+30,y0+50,text='Motor',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+30,y0+65,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+60,y0+15,text='6',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+48,y0+15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+36,y0+15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+24,y0+15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+12,y0+15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+0,y0+15,text='1',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-16,y0-10,x0+76,y0+100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-16<x<self.x+76 and self.y-10<y<self.y+100
    def __str__(self):
        return 'motor: (%d,%d)--(%d,%d)'%(igrid(self.x-8),jgrid(self.y),igrid(self.x+54),jgrid(self.y))

class frobot(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('fr')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-100,y0+10,x0+16,y0-100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-86,y0-2,x0-82,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-74,y0-2,x0-70,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-62,y0-2,x0-58,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-50,y0-2,x0-46,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-38,y0-2,x0-34,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-26,y0-2,x0-22,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-14,y0-2,x0-10,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0-42,y0-65,text='Robot',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-42,y0-50,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0,y0-15,text='1',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-12,y0-15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-24,y0-15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-36,y0-15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-48,y0-15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-60,y0-15,text='6',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-72,y0-15,text='7',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-84,y0-15,text='8',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-100,y0+10,x0+16,y0-100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-100<x<self.x+16 and self.y-100<y<self.y+10
    def __str__(self):
        return 'robot: (%d,%d)--(%d,%d)'%(igrid(self.x-6),jgrid(self.y),igrid(self.x-92),jgrid(self.y))

class irobot(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('ir')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-16,y0-10,x0+100,y0+100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+10,y0-2,x0+14,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+22,y0-2,x0+26,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+34,y0-2,x0+38,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+46,y0-2,x0+50,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+58,y0-2,x0+62,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+70,y0-2,x0+74,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+82,y0-2,x0+86,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0+42,y0+50,text='Robot',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+42,y0+65,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+84,y0+15,text='8',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+72,y0+15,text='7',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+60,y0+15,text='6',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+48,y0+15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+36,y0+15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+24,y0+15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+12,y0+15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+0,y0+15,text='1',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-16,y0-10,x0+100,y0+100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-16<x<self.x+100 and self.y-10<y<self.y+100
    def __str__(self):
        return 'robot: (%d,%d)--(%d,%d)'%(igrid(self.x-8),jgrid(self.y),igrid(self.x+78),jgrid(self.y))

class fhead(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('fh')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-100,y0+10,x0+16,y0-100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-86,y0-2,x0-82,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-74,y0-2,x0-70,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-62,y0-2,x0-58,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-50,y0-2,x0-46,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-38,y0-2,x0-34,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-26,y0-2,x0-22,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-14,y0-2,x0-10,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0-42,y0-65,text='Head',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-42,y0-50,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0,y0-15,text='1',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-12,y0-15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-24,y0-15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-36,y0-15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-48,y0-15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-60,y0-15,text='6',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-72,y0-15,text='7',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0-84,y0-15,text='8',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-100,y0+10,x0+16,y0-100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-100<x<self.x+16 and self.y-100<y<self.y+10
    def __str__(self):
        return 'head: (%d,%d)--(%d,%d)'%(igrid(self.x-6),jgrid(self.y),igrid(self.x-92),jgrid(self.y))

class ihead(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('ih')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-16,y0-10,x0+100,y0+100,fill=gray,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+10,y0-2,x0+14,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+22,y0-2,x0+26,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+34,y0-2,x0+38,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+46,y0-2,x0+50,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+58,y0-2,x0+62,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+70,y0-2,x0+74,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_rectangle(x0+82,y0-2,x0+86,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0+42,y0+50,text='Head',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+42,y0+65,text='Connector',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+84,y0+15,text='8',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+72,y0+15,text='7',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+60,y0+15,text='6',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+48,y0+15,text='5',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+36,y0+15,text='4',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+24,y0+15,text='3',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+12,y0+15,text='2',fill=white,font=('Helvetica',9,'normal')),
                      canvas.create_text(x0+0,y0+15,text='1',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-16,y0-10,x0+100,y0+100,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-16<x<self.x+100 and self.y-10<y<self.y+100
    def __str__(self):
        return 'head: (%d,%d)--(%d,%d)'%(igrid(self.x-8),jgrid(self.y),igrid(self.x+78),jgrid(self.y))

class fpower(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('fv')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-10,y0-10,x0+30,y0+5,fill=red,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0+17,y0-2,text='+10',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-10,y0-10,x0+30,y0+5,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-10<x<self.x+30 and self.y-10<y<self.y+5
    def __str__(self):
        return '+10: (%d,%d)'%(igrid(self.x),jgrid(self.y))

class ipower(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('iv')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-10,y0-5,x0+30,y0+10,fill=blue,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0+17,y0+2,text='gnd',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-10,y0-5,x0+30,y0+10,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-10<x<self.x+30 and self.y-5<y<self.y+10
    def __str__(self):
        return 'gnd: (%d,%d)'%(igrid(self.x),jgrid(self.y))

class fmeter(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('fx')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-20,y0-5,x0+20,y0+20,fill=red,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0,y0+10,text='+probe',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-20,y0-5,x0+20,y0+20,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-20<x<self.x+20 and self.y-5<y<self.y+20
    def __str__(self):
        return '+probe: (%d,%d)'%(igrid(self.x),jgrid(self.y))

class imeter(component):
    def __init__(self,z):
        (x1,y1) = z
        (self.x,self.y) = (x0,y0) = (x1,y1)
        self.label = getLabel('ix')
    def add(self, canvas):
        (x0, y0) = (self.x, self.y)
        self.parts = [canvas.create_rectangle(x0-20,y0-5,x0+20,y0+20,fill=blue,outline=black,tags=self.label),
                      canvas.create_rectangle(x0-2,y0-2,x0+2,y0+2,fill=black,outline=black,tags=self.label),
                      canvas.create_text(x0,y0+10,text='-probe',fill=white,font=('Helvetica',9,'normal'))]
        self.canvas = canvas
    def highlight(self):
        (x0,y0) = (self.x,self.y)
        self.canvas.create_rectangle(x0-20,y0-5,x0+20,y0+20,fill=None,outline=red,width=3,tags=('highlight',self.label))
    def inside(self,x,y):
        return self.x-20<x<self.x+20 and self.y-5<y<self.y+20
    def __str__(self):
        return '-probe: (%d,%d)'%(igrid(self.x),jgrid(self.y))

# map from current CMax layout y-spacing to actual protoboard y-spacing
# yy = [0,1,2, 3,4,4, 5,6,7,8,9, 10,11,11, 12,13,14,15,16, 17,18,18, 19,20]

def yremap(y):
    return (y+4)*7/8-3

class wire(component):
    def __init__(self,z0,z1):
        (self.x0,self.y0) = z0
        (self.x,self.y) = z1
        self.label = getLabel('wi')
        self.atendflag=True
    def add(self, canvas):
        self.canvas = canvas
        self.render()
    def render(self):
        yai = int(jgrid(self.y)) # new
        ybi = int(jgrid(self.y0)) # new
        ya = gridy(yremap(yai))
        yb = gridy(yremap(ybi))
#       l = math.sqrt((self.x0-self.x)**2+(self.y0-self.y)**2)/12
        l = math.sqrt((self.x0-self.x)**2+(ya-yb)**2)/12
#       color = black
        color = white # new
        if 1<l<10:
            color = colors[int(l)]
        elif 10<=l<50:
            color = colors[int((l+9)/10)]
        outlinecolor = black # don't use black outline for black wire
        if color == black: outlinecolor = green # yellow # orange # white
        thickness=8 # new was 7
        if mousedown:
            outlinecolor = red 
            thickness = 10 # thickness in "highlighted" mode
        self.parts = [self.canvas.create_line(self.x0,self.y0,self.x,self.y,
                                             fill=outlinecolor,width=thickness,capstyle='round',tags=self.label),
                      self.canvas.create_line(self.x0,self.y0,self.x,self.y,
                                             fill=color,width=4,capstyle='round',tags=self.label)]
    def highlight(self):
        self.erase();
        self.render();
#       highlight for wires are awkward since the way things are set
#       up now, the highlighted graphic as first drawn is moved without redrawing.
#       Also, the wire was not re-rendering after the mouse button was released.
#       So it is now handeled by render above using global variable mousedown
        pass
    def nearend(self,x,y): # orginal 'inside' method
        if self.x-6<x<self.x+6 and self.y-6<y<self.y+6:
            return True
        elif self.x0-6<x<self.x0+6 and self.y0-6<y<self.y0+6:
            (self.x0,self.y0,self.x,self.y) = (self.x,self.y,self.x0,self.y0)
            return True
        return False
    def inside(self,x,y):
        self.atendflag = self.nearend(x,y)
        if self.atendflag: return True
        dxl = self.x0-self.x
        dyl = self.y0-self.y
        dx = x-self.x
        dy = y-self.y
        dx0 = x-self.x0
        dy0 = y-self.y0
        crs = dx*dyl - dy*dxl
        sqr = dxl*dxl + dyl*dyl
        if crs*crs > 6*6*sqr:
            return False # distance from line too large
        dend = dx*dxl + dy*dyl
        dend0 = dx0*dxl + dy0*dyl
        if (dend < 0) or (dend0 > 0):
            return False # outside of line segment
        if dend0*dend0 < dend*dend: # reverse if other end closer
            (self.x0,self.y0,self.x,self.y) = (self.x,self.y,self.x0,self.y0)
        return True
    def move(self,dx,dy):
        setChanged(True)
        self.erase()
        self.x += dx
        self.y += dy
        if not self.atendflag:
            self.x0 += dx
            self.y0 += dy
        self.render()
    def __str__(self):
        return 'wire: (%d,%d)--(%d,%d)'%(igrid(self.x0),jgrid(self.y0),igrid(self.x),jgrid(self.y))

# draw the protoboard
def drawProtoboard():
    for i in range(1,64):
        for j in range(1,11):
            drawConnector(pin(i,j))
        if bussed(i):
            for j in range(1,5):
                drawConnector(bus(i,j))
    for (y,a) in zip([1,2,3,4,5,6,7,8,9,10],['A','B','C','D','E','F','G','H','I','J']):
        label(pin(-0.5,y),a)
        label(pin(64.5,y),a)
    for x in [1,5,10,15,20,25,30,35,40,45,60,50,55,60]:
        label(pin(x,0),str(x))
        label(pin(x,11),str(x))
    busLine(0,'+','black')
    busLine(3,'-','black')
    busLine(21,'+','black')
    busLine(24,'-','black')

# limit coordinates to protoboard area (0,0) to (830,350)
# NOTE: make edge coordinates multiples of 12 so snap-to works properly

def boundtocanvas(x, y):
    return (min(max(x, 0+12), 830-2), min(max(y,0+12),350-2))

# mouse dragging action

class movingState:
    def push(self,event):
        global mousedown,oldChanged,movingdx,movingdy,newwireflag
        mousedown = True
        (xnew, ynew) = boundtocanvas(event.x,event.y) # limit excursion
        (self.x,self.y) = (xnew, ynew)
        movingdx=movingdy=0
        self.moving = []
        for c in componentList:
            if c.inside(self.x,self.y):
                self.moving = [c]
        newwireflag = False
        if len(self.moving)>0:
            if ctrlDown:
                removeComponent(self.moving[0])
                self.moving = []
            else:
                self.moving[0].highlight()
        else: # start a zero length wire here then
            oldChanged = getChanged() # save old state 
            (x,y) = (((xnew+6)//12)*12,((ynew+6)//12)*12) # snap to
            c = wire((x,y),(x,y))
            addComponent(c, workCanvas)
            self.moving = [c]
            newwireflag = True
#           c.highlight() # wire highlight not implemented this way

    def move(self,event):
        global movingdx,movingdy
        (xnew, ynew) = boundtocanvas(event.x,event.y)
        (dx,dy) = (((xnew-self.x+6)//12)*12,((ynew-self.y+6)//12)*12)
        if dx == 0 and dy == 0: return # nothing to do 
        for c in self.moving:
            c.move(dx,dy)
        for c in workCanvas.find_withtag('highlight'):
            workCanvas.move(c,dx,dy)
        (self.x,self.y) = (self.x+dx,self.y+dy)
        movingdx+=dx # accumulate motion
        movingdy+=dy # accumulate motion

    def release(self,event):
        global mousedown,oldChanged,movingdx, movingdy,newwireflag
        global lastAction,lastComponent
        mousedown = False
        self.move(event)
        for c in workCanvas.find_withtag('highlight'):
            workCanvas.delete(c)
        for c in self.moving:
            if c.label[0:2] == 'wi':
                if c.x == c.x0 and c.y == c.y0: # flush zero length wire
                    removeComponent(c)
                    setChanged(oldChanged) # restore if no wire placed 
                else: # for wires, erase "highlighted" version and redraw
                    c.erase()
                    c.render()
                    if newwireflag:
                        lastComponent = c
                        lastAction = 'add'
                    else:
                        lastComponent = c
                        lastAction = 'wiring'
            elif movingdx != 0 or movingdy != 0:
                lastComponent = c
                lastAction = 'moving'
            else:
                lastAction = None # just a click in one place
#        print 'lastAction (mouse up)', lastAction
#        sys.stdout.flush()

# Set global variables on keyPress and keyRelease for Shift, Control
# We want really instead to use equivalent of Windows GetASyncKeyState
# to get state of Shift, Control, and Alt keys are in at time of mouse click
# Otherwise problems when key state changed while window was not focus. bkph

def keyPress(event):
    global ctrlDown, shiftDown

    if event.keysym == "Control_L" or event.keysym == "Control_R":
        root.configure(cursor='pirate')
        ctrlDown = True
    elif event.keysym == "Shift_L" or event.keysym == "Shift_R":
        root.configure(cursor='exchange')
        shiftDown = True
    elif event.char == 'q': quit()
    elif event.char == 's': save()
    elif event.char == 'r': Simulate() 
    elif event.char == 'o': openFile()
    elif event.char == 'n': clear()
    elif event.char == 'p': revert()
    elif event.char == 'u': unDo()
    elif event.keysym == 'Right': ShiftRight()
    elif event.keysym == 'Left': ShiftLeft()
    elif event.char == '+' or event.char == '=': ShiftRight()
    elif event.char == '-' or event.char == '_': ShiftLeft()

def keyRelease(event):
    global ctrlDown, shiftDown
    if event.keysym == "Control_L" or event.keysym == "Control_R":
        root.configure(cursor='arrow')
        ctrlDown = False
    elif event.keysym == "Shift_L" or event.keysym == "Shift_R":
        root.configure(cursor='arrow')
        shiftDown = False 

# "stem cell" resistor

newValue = [1,0,2]
colors = [black,brown,red,orange,yellow,green,blue,violet,gray,white]
# how to do silver and gold :-)?
# suffix = ['','0','K','K','0K','M','M','0M','G','G']
suffix = [' ohm','0','K','K','0K','M','M','0M','G','G']
# could use Omega from Symbol font...

def drawNewResistor():
    global newResistor,newResValue

    newResistor = hresistor((12,30),newValue[0],newValue[1],newValue[2])
    newResistor.add(menuCResCanvas)
    vresistor((35,60),newValue[0],newValue[1],newValue[2]).add(menuVResCanvas)
    # hresistor((12,37),newValue[0],newValue[1],newValue[2]).add(menuHResCanvas)

#    menuCResCanvas.create_text(35,13,text='1.0K',font=('Helvetica',9,'bold'))
    menuCResCanvas.create_text(36,50,text='click color',font=('Helvetica',9,'bold'))
    menuCResCanvas.create_text(36,62,text='to change',font=('Helvetica',9,'bold'))

#   value = str(newValue[0])+str(newValue[1])
    if newValue[0] == 0: # deal with small values of resistance
        value = str(newValue[1])
        if newValue[2]%3 == 2: # indent
            value = '0'+'.'+value[0] # indent
    else:
        value = str(newValue[0])+str(newValue[1])
        if newValue[2]%3 == 2: # indent
            value = value[0]+'.'+value[1] # indent
    value += suffix[newValue[2]]
    newResValue = menuCResCanvas.create_text(35,13,text=value,font=('Helvetica',9,'bold'))

def cresButton(event):
    global newResistor,newResValue
    if newResistor.in1(event.x,event.y):
        if shiftDown: newValue[0] = (newValue[0]-1)%10 # allow zero going down...
        else: newValue[0] = newValue[0]%9+1 # normal wrap forward 
        menuCResCanvas.delete(newResistor,newResValue)
        drawNewResistor()
    elif newResistor.in2(event.x,event.y):
        if shiftDown: newValue[1] = (newValue[1]-1)%10
        else: newValue[1] = (newValue[1]+1)%10
        menuCResCanvas.delete(newResistor,newResValue)
        drawNewResistor()
    elif newResistor.in3(event.x,event.y):
        if shiftDown: newValue[2] = (newValue[2]-1)%10
        else: newValue[2] = (newValue[2]+1)%10
        menuCResCanvas.delete(newResistor,newResValue)
        drawNewResistor()
def cresEnter(event):
    menuCResCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def cresLeave(event):
    menuCResCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

xfresh=66       # x position where new instances appear
yfresh=18       # y position where new instances appear

def hresButton(event):
    if shiftDown: addComponent(vresistor(pin(xfresh-1,yfresh-2),newValue[0],newValue[1],newValue[2]),workCanvas)
    else: addComponent(hresistor(pin(xfresh-2,yfresh-1),newValue[0],newValue[1],newValue[2]),workCanvas)
def hresEnter(event):
    menuHResCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def hresLeave(event):
    menuHResCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def vresButton(event):
    if shiftDown: addComponent(hresistor(pin(xfresh-2,yfresh-1),newValue[0],newValue[1],newValue[2]),workCanvas)
    else: addComponent(vresistor(pin(xfresh-1,yfresh-2),newValue[0],newValue[1],newValue[2]),workCanvas)
def vresEnter(event):
    menuVResCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def vresLeave(event):
    menuVResCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def fampButton(event):
    if shiftDown: addComponent(iopamp(pin(xfresh-3,yfresh-4)),workCanvas)
    else: addComponent(fopamp(pin(xfresh,yfresh)),workCanvas)
def fampEnter(event):
    menufAmpCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def fampLeave(event):
    menufAmpCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def iampButton(event):
    if shiftDown: addComponent(fopamp(pin(xfresh,yfresh)),workCanvas)
    else: addComponent(iopamp(pin(xfresh-3,yfresh-4)),workCanvas)
def iampEnter(event):
    menuiAmpCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def iampLeave(event):
    menuiAmpCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def fpotButton(event):
    if shiftDown: addComponent(ipot(pin(xfresh-3,yfresh-3)),workCanvas)
    else: addComponent(fpot(pin(xfresh-1,yfresh-1)),workCanvas)
def fpotEnter(event):
    menufPotCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def fpotLeave(event):
    menufPotCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def ipotButton(event):
    if shiftDown: addComponent(fpot(pin(xfresh-1,yfresh-1)),workCanvas)
    else: addComponent(ipot(pin(xfresh-3,yfresh-3)),workCanvas)
def ipotEnter(event):
    menuiPotCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def ipotLeave(event):
    menuiPotCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def fMotorButton(event):
    if shiftDown: addComponent(imotor(pin(xfresh-2,yfresh-9)),workCanvas)
    else: addComponent(fmotor(pin(xfresh-7,yfresh-2)),workCanvas)
def fMotorEnter(event):
    menufMotorCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def fMotorLeave(event):
    menufMotorCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

#def iMotorButton(event):
#    if shiftDown: addComponent(fmotor(pin(xfresh-7,yfresh-2)),workCanvas)
#    else: addComponent(imotor(pin(xfresh-2,yfresh-9)),workCanvas)
#def iMotorEnter(event):
#    menuiMotorCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
#def iMotorLeave(event):
#    menuiMotorCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

#def fRobotButton(event):
#    if flipart: addComponent(irobot(pin(xfresh-1, yfresh-9)),workCanvas)
#    else: addComponent(frobot(pin(xfresh-8,yfresh-1)),workCanvas)
#def fRobotEnter(event):
#    menufRobotCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
#def fRobotLeave(event):
#    menufRobotCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def iRobotButton(event):
    if shiftDown: addComponent(frobot(pin(xfresh-8, yfresh-1)),workCanvas)
    else: addComponent(irobot(pin(xfresh-1, yfresh-9)),workCanvas)
def iRobotEnter(event):
    menuiRobotCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def iRobotLeave(event):
    menuiRobotCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def fHeadButton(event):
    if shiftDown: addComponent(ihead(pin(xfresh-2,yfresh-10)),workCanvas)
    else: addComponent(fhead(pin(xfresh-9,yfresh-2)),workCanvas)
def fHeadEnter(event):
    menufHeadCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def fHeadLeave(event):
    menufHeadCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

#def iHeadButton(event):
#    if shiftDown: addComponent(fhead(pin(xfresh-9,yfresh-2)),workCanvas)
#    else: addComponent(ihead(pin(xfresh-2, yfresh-10)),workCanvas)
#def iHeadEnter(event):
#    menuiHeadCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
#def iHeadLeave(event):
#    menuiHeadCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def powerButton(event):
    if shiftDown:
        addComponent(fpower(pin(3,-4)),workCanvas)
        addComponent(ipower(pin(3,-3)),workCanvas)
    else:
        addComponent(fpower(pin(3,14)),workCanvas)
        addComponent(ipower(pin(3,15)),workCanvas)
def powerEnter(event):
    menuPowerCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def powerLeave(event):
    menuPowerCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def meterButton(event):
    if shiftDown:
        addComponent(fmeter(pin(5,1)),workCanvas)
        addComponent(imeter(pin(1,1)),workCanvas)
    else:
        addComponent(fmeter(pin(5,10)),workCanvas)
        addComponent(imeter(pin(1,10)),workCanvas)
def meterEnter(event):
    menuMeterCanvas.create_rectangle(2,2,68,68,width=3,outline='red')
def meterLeave(event):
    menuMeterCanvas.create_rectangle(2,2,68,68,width=3,outline='black')

def filenameonly(filename):
    inx = filename.rfind('/')
    if inx == -1: return filename
    else: return filename[inx+1:]

def directoryonly(filename):
    inx = filename.rfind('/')
    if inx == -1: return ''
    else: return filename[:inx]

def save():
    global filename,oldfilename
    if filename == '':
        if oldfilename == '':
            filename = tkFileDialog.asksaveasfilename(title="Save As")
        else:
#           print 'filename ', filenameonly(oldfilename)
#           print 'directory ', directoryonly(oldfilename)
            filename = tkFileDialog.asksaveasfilename(title="Save",
                                initialfile=filenameonly(oldfilename),
                                initialdir=directoryonly(oldfilename)) 
        if filename == '':
            showwarning('Save As','Cancelled: file not saved')
            return
    oldfilename = filename
    file = open(filename,'w')
    for c in componentList:
        print >>file,c
    file.close()
    setChanged(False)

def saveAs():
    global filename,oldfilename
    oldfilename = filename  # save before resetting
    filename = ''
    save()

def clear():            # called by "New" button and openFile
    clearnew(True)

def clearnew(resetflag):    
    global componentList,filename,lastAction
    if len(componentList)!=0 and getChanged():
        if askquestion("OK","Current circuit not saved -- save?")=='yes':
            save()
    while componentList:
        removeComponent(componentList[0])
    if resetflag:
        oldfilename = filename  # save before resetting
        filename = ''
    setChanged(False)
    lastAction = None

def openFile():
    global filename,oldfilename
    filetypes = [('text files','.txt'),('all files','.*')]
#    filename = tkFileDialog.askopenfilename(filetypes=[('text files','.txt'),('all files','.*')],
#        title="Open File",initialfile=filenameonly(oldfilename),initialdir=directoryonly(filename))
    if filename == '':
        filename = tkFileDialog.askopenfilename(filetypes=filetypes)
    else:
        filename = tkFileDialog.askopenfilename(filetypes=filetypes,
                                                title="Open File",
                                                initialfile=filenameonly(oldfilename),
                                                initialdir=directoryonly(filename))
    if not filename:
        showwarning('Open File','Cancelled: file not opened')
    else:
#       oldfilename = filename
        readFile(filename)
        
def revert():
    global filename,oldfilename
    clearnew(False)
    if filename == '':
        return  # can't revert
    else:
        readFile(filename)
    
def readFile(filename):
    global componentList,lastAction,oldfilename
    oldfilename = filename
    clearnew(False) # clear only when actually about to read a file
    for line in open(filename):
        match = re.match(r'opamp: \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if int(y1)<int(y0):
                addComponent(fopamp(grid(int(x0),int(y0))),workCanvas)
            else:
                addComponent(iopamp(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'pot: \((\d+),(\d+)\)--\((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1,x2,y2) = match.groups()
            if int(y1)<int(y0):
                addComponent(fpot(grid(int(x0),int(y0))),workCanvas)
            else:
                addComponent(ipot(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'motor: \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if int(x1)>int(x0):
                addComponent(fmotor(grid(int(x0),int(y0))),workCanvas)
            else:
                addComponent(imotor(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'robot: \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if int(x1)>int(x0):
                addComponent(frobot(grid(int(x0),int(y0))),workCanvas)
            else:
                addComponent(irobot(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'head: \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if int(x1)>int(x0):
                addComponent(fhead(grid(int(x0),int(y0))),workCanvas)
            else:
                addComponent(ihead(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'resistor\((\d),(\d),(\d)\): \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (c1,c2,c3,x0,y0,x1,y1) = match.groups()
            if int(x0)==int(x1):
                addComponent(vresistor(grid(int(x0),int(y1)),int(c1),int(c2),int(c3)),workCanvas)
            else:
                addComponent(hresistor(grid(int(x0),int(y1)),int(c1),int(c2),int(c3)),workCanvas)
        match = re.match(r'\+10: \((\d+),(\d+)\)',line)
        if match:
            (x0,y0) = match.groups()
            addComponent(fpower(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'gnd: \((\d+),(\d+)\)',line)
        if match:
            (x0,y0) = match.groups()
            addComponent(ipower(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'\+probe: \((\d+),(\d+)\)',line)
        if match:
            (x0,y0) = match.groups()
            addComponent(fmeter(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'\-probe: \((\d+),(\d+)\)',line)
        if match:
            (x0,y0) = match.groups()
            addComponent(imeter(grid(int(x0),int(y0))),workCanvas)
        match = re.match(r'wire: \((\d+),(\d+)\)--\((\d+),(\d+)\)',line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            addComponent(wire(grid(int(x0),int(y0)),grid(int(x1),int(y1))),workCanvas)
    setChanged(False)             # hasn't changed yet...
    lastAction = None

def quit():
    if len(componentList)!=0 and getChanged():
        if askquestion("OK","Current circuit not saved -- save?")=='yes':
            save()
    print 'Quitting'
    workCanvas.quit()

# def runTest():
#    if len(componentList)!=0 and getChanged():
#        if askquestion("OK","Current circuit not saved -- save?")=='yes':
#            save()
#    print 'Running test'
#    simulate.runTest([str(c) for c in componentList], parent=root)

def Simulate():
    global simfilename
    if len(componentList) == 0:
        showwarning('Simulate','Circuit must be defined first')
        return
    if shiftDown or simfilename == '':
        filetypes = [('Python files','.py'),('all files','.*')]
        if simfilename:
            newsimfilename = tkFileDialog.askopenfilename(filetypes=filetypes,
                                                          initialfile=filenameonly(simfilename),
                                                          initialdir=directoryonly(simfilename))
        else:
            newsimfilename = tkFileDialog.askopenfilename(filetypes=filetypes)
        if not newsimfilename:
            showwarning('Open Simulate File','Cancelled: file not opened')
        else:
            simfilename = newsimfilename

    if simfilename:
        execfile(simfilename, globals())
        print runTest
        if len(componentList)!=0 and getChanged():
            if askquestion("OK","Current circuit not saved -- save?")=='yes':
                save()
        print 'Running test'
        runTest([str(c) for c in componentList], parent=root)

# Move parts within delimited range --- bkph

def MoveX(clist, xleft, xright, offset):
    for cl in clist:
        cl.erase()
        xi = igrid(cl.x)
        if xi >= xleft and xi <= xright:
            cl.x = gridx(igrid(cl.x)+offset)
        if cl.label[0:2] == 'wi':
            xi = igrid(cl.x0)
            if xi >= xleft and xi <= xright:
                cl.x0 = gridx(igrid(cl.x0)+offset)
        cl.add(workCanvas)

# Determine range of horizontal coordinates (note: decreasing to the right)
# Also try and detect two vertical wires running from above top rail to
# below bottom rail used to delimit areas to be moved --- bkph

def CoordinateRangeX(clist):
    xmin = 64
    xmax = 0
    xleft = -1
    xright = -1
    for cl in clist:
        if igrid(cl.x) < xmin:
            xmin = igrid(cl.x)
        if igrid(cl.x) > xmax:
            xmax = igrid(cl.x)
        if cl.label[0:2] == 'wi':
            if igrid(cl.x0) < xmin:
                xmin = igrid(cl.x0)
            if igrid(cl.x0) > xmax:
                xmax = igrid(cl.x0)
            if (jgrid(cl.y) <= 0 and jgrid(cl.y0) >= 24) or\
                   (jgrid(cl.y0) <= 0 and jgrid(cl.y) >= 24):
                if xleft == -1: 
                    xleft = igrid(cl.x) # first delimiter
                elif xright == -1:
                    xright = igrid(cl.x) # second delimiter
                else:
                    print "Too many delimiters"
    if xleft != -1 and xright == -1:
        xright = xleft  # move single column
    if (xleft > xright):
        (xleft, xright) = (xright, xleft) 
    if xleft == -1 or xright == -1: # zero or one delimiter
        xleft = 0
        xright = 64
    return (xmin, xmax, xleft, xright)

# Primitive right shift facility on '+' and right arrow key

def ShiftRight(): # bkph
    global lastAction
    if len(componentList) == 0:
        return (0,0) # nothing to do
#   check coordinate range before doing anything
    (xmin, xmax, xleft, xright) = CoordinateRangeX(componentList)
    if xmin < 2 and xright < 2:
        print 'Unable to shift right. Remove components on right edge.'
        sys.stdout.flush()
        return
#   now actually move
    MoveX(componentList, xleft, xright, -1)
    lastAction = 'rightshift'
    setChanged(True)
    sys.stdout.flush()

# Primitive left shift facility on '-' and left arrow key

def ShiftLeft(): # bkph
    global lastAction
    if len(componentList) == 0:
        return (0,0) # nothing to do
#   check coordinate range before doing anything
    (xmin, xmax, xleft, xright) = CoordinateRangeX(componentList)
    if xmax > 62 and xleft >= 62:
        print 'Unable to shift left.  Remove components on left edge.'
        sys.stdout.flush()
        return
#   now actually move
    MoveX(componentList, xleft, xright, +1)
    lastAction = 'leftshift'
    setChanged(True)
    sys.stdout.flush()

# main routine
root = Tk()
root.configure(cursor='arrow')
ctrlDown = False
shiftDown = False 
toolCanvas = Canvas(root, width=830, height=90)
toolCanvas.pack()
Button(toolCanvas, text="New", command = clear,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Open File", command = openFile,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Save As", command = saveAs,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Save", command = save,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Simulate", command = Simulate,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Undo", command = unDo,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Revert", command = revert,height=4,width=9).pack(side='left')
Button(toolCanvas, text="Quit", command = quit,height=4,width=9).pack(side='left')
moduleCanvas = Canvas(root, width=830, height=90)
moduleCanvas.pack()
menuVResCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menuVResCanvas.pack(side='left')
menuCResCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menuCResCanvas.pack(side='left')
# menuHResCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
# menuHResCanvas.pack(side='left')
menufAmpCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menufAmpCanvas.pack(side='left')
# menuiAmpCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
# menuiAmpCanvas.pack(side='left')
menufPotCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menufPotCanvas.pack(side='left')
# menuiPotCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
# menuiPotCanvas.pack(side='left')
# menuPowerCanvas = Canvas(toolCanvas, width=70, height=70, background='#DFDFDF')
menuPowerCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menuPowerCanvas.pack(side='left')
# menuMeterCanvas = Canvas(toolCanvas, width=70, height=70, background='#DFDFDF')
menuMeterCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menuMeterCanvas.pack(side='left')
menufMotorCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menufMotorCanvas.pack(side='left')
#menuiMotorCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
#menuiMotorCanvas.pack(side='left')
#menufRobotCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
#menufRobotCanvas.pack(side='left')
menuiRobotCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menuiRobotCanvas.pack(side='left')
menufHeadCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
menufHeadCanvas.pack(side='left')
#menuiHeadCanvas = Canvas(moduleCanvas, width=70, height=70, background='#DFDFDF')
#menuiHeadCanvas.pack(side='left')
workCanvas = Canvas(root, width=830, height=350, background='#FFFFFF')
workCanvas.pack()
drawProtoboard()
menufAmpCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
fopamp((18,60)).add(menufAmpCanvas)
# menuiAmpCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
# iopamp((54,12)).add(menuiAmpCanvas)
menufPotCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
fpot((24,48)).add(menufPotCanvas)
# menuiPotCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
# ipot((48,24)).add(menuiPotCanvas)
menuPowerCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
fpower((24,23)).add(menuPowerCanvas)
ipower((24,46)).add(menuPowerCanvas)
menuMeterCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
fmeter((35,12)).add(menuMeterCanvas)
imeter((35,41)).add(menuMeterCanvas)
menufMotorCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
menufMotorCanvas.create_text(34,20,text='Motor',font=('Helvetica',9,'bold'))
menufMotorCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
menufMotorCanvas.create_text(34,50,text='(top)',font=('Helvetica',9,'bold'))
#menuiMotorCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
#menuiMotorCanvas.create_text(34,20,text='Motor',font=('Helvetica',9,'bold'))
#menuiMotorCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
#menuiMotorCanvas.create_text(34,50,text='(bottom)',font=('Helvetica',9,'bold'))
#menufRobotCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
#menufRobotCanvas.create_text(34,20,text='Robot',font=('Helvetica',9,'bold'))
#menufRobotCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
#menufRobotCanvas.create_text(34,50,text='(top)',font=('Helvetica',9,'bold'))
menuiRobotCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
menuiRobotCanvas.create_text(34,20,text='Robot',font=('Helvetica',9,'bold'))
menuiRobotCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
menuiRobotCanvas.create_text(34,50,text='(bottom)',font=('Helvetica',9,'bold'))
menufHeadCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
menufHeadCanvas.create_text(34,20,text='Head',font=('Helvetica',9,'bold'))
menufHeadCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
menufHeadCanvas.create_text(34,50,text='(top)',font=('Helvetica',9,'bold'))
#menuiHeadCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
#menuiHeadCanvas.create_text(34,20,text='Head',font=('Helvetica',9,'bold'))
#menuiHeadCanvas.create_text(34,35,text='Connector',font=('Helvetica',9,'bold'))
#menuiHeadCanvas.create_text(34,50,text='(bottom)',font=('Helvetica',9,'bold'))
menuVResCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
menuCResCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
# menuHResCanvas.create_rectangle(2,2,68,68,width=3,fill='white',outline='black')
drawNewResistor()

moving = movingState()
workCanvas.bind('<Button-1>',moving.push)
workCanvas.bind('<B1-Motion>',moving.move)
workCanvas.bind('<ButtonRelease-1>',moving.release)
menufAmpCanvas.bind('<Button-1>',fampButton)
menufAmpCanvas.bind('<Enter>',fampEnter)
menufAmpCanvas.bind('<Leave>',fampLeave)
# menuiAmpCanvas.bind('<Button-1>',iampButton)
# menuiAmpCanvas.bind('<Enter>',iampEnter)
# menuiAmpCanvas.bind('<Leave>',iampLeave)
menufPotCanvas.bind('<Button-1>',fpotButton)
menufPotCanvas.bind('<Enter>',fpotEnter)
menufPotCanvas.bind('<Leave>',fpotLeave)
# menuiPotCanvas.bind('<Button-1>',ipotButton)
# menuiPotCanvas.bind('<Enter>',ipotEnter)
# menuiPotCanvas.bind('<Leave>',ipotLeave)
menuPowerCanvas.bind('<Button-1>',powerButton)
menuPowerCanvas.bind('<Enter>',powerEnter)
menuPowerCanvas.bind('<Leave>',powerLeave)
menuMeterCanvas.bind('<Button-1>',meterButton)
menuMeterCanvas.bind('<Enter>',meterEnter)
menuMeterCanvas.bind('<Leave>',meterLeave)
menufMotorCanvas.bind('<Button-1>',fMotorButton)
menufMotorCanvas.bind('<Enter>',fMotorEnter)
menufMotorCanvas.bind('<Leave>',fMotorLeave)
#menuiMotorCanvas.bind('<Button-1>',iMotorButton)
#menuiMotorCanvas.bind('<Enter>',iMotorEnter)
#menuiMotorCanvas.bind('<Leave>',iMotorLeave)
#menufRobotCanvas.bind('<Button-1>',fRobotButton)
#menufRobotCanvas.bind('<Enter>',fRobotEnter)
#menufRobotCanvas.bind('<Leave>',fRobotLeave)
menuiRobotCanvas.bind('<Button-1>',iRobotButton)
menuiRobotCanvas.bind('<Enter>',iRobotEnter)
menuiRobotCanvas.bind('<Leave>',iRobotLeave)
menufHeadCanvas.bind('<Button-1>',fHeadButton)
menufHeadCanvas.bind('<Enter>',fHeadEnter)
menufHeadCanvas.bind('<Leave>',fHeadLeave)
#menuiHeadCanvas.bind('<Button-1>',iHeadButton)
#menuiHeadCanvas.bind('<Enter>',iHeadEnter)
#menuiHeadCanvas.bind('<Leave>',iHeadLeave)
menuVResCanvas.bind('<Button-1>',vresButton)
menuVResCanvas.bind('<Enter>',vresEnter)
menuVResCanvas.bind('<Leave>',vresLeave)
# menuHResCanvas.bind('<Button-1>',hresButton)
# menuHResCanvas.bind('<Enter>',hresEnter)
# menuHResCanvas.bind('<Leave>',hresLeave)
menuCResCanvas.bind('<Button-1>',cresButton)
menuCResCanvas.bind('<Enter>',cresEnter)
menuCResCanvas.bind('<Leave>',cresLeave)

root.bind('<KeyPress>',keyPress)
root.bind('<KeyRelease>',keyRelease)
componentList = []
root.title('CMax') # set initial window title
root.mainloop()


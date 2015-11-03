"""
Abstract superclass for various grid maps.
"""

import util
import dw
import windows
import math
reload(dw)

robotRadius = 0.22
defaultWindowWidth = 400

class GridMap:
    def __init__(self, xMin, xMax, yMin, yMax, gridSquareSize,
                 windowWidth = defaultWindowWidth):
        """
        Basic initializer that determines the number of cells, and
        calls the C{makeStartingGrid} method that any subclass must
        provide, to get the initial values.  Makes a window and draws
        the initial world state in it.
        
        @param xMin: least real x coordinate
        @param xMax: greatest real x coordinate
        @param yMin: least real y coordinate
        @param yMax: greatest real y coordinate
        @param gridSquareSize: size, in world coordinates, of a grid
        square
        @param windowWidth: size, in pixels, to make the window for
        drawing this map  
        """
        self.xMin = xMin
        """X coordinate of left edge"""
        self.xMax = xMax
        """X coordinate of right edge"""
        self.yMin = yMin
        """Y coordinate of bottom edge"""
        self.yMax = yMax
        """Y coordinate of top edge"""
        self.xN = int(math.ceil((self.xMax - self.xMin) / gridSquareSize))
        """number of cells in x dimension"""
        self.yN = int(math.ceil((self.yMax - self.yMin) / gridSquareSize))
        """number of cells in y dimension"""
        self.xStep = gridSquareSize
        """size of a side of a cell in the x dimension"""
        self.yStep = gridSquareSize
        """size of a side of a cell in the y dimension"""

        ## Readjust the max dimensions to handle the fact that we need
        ## to have a discrete numer of grid cells
        self.xMax = gridSquareSize * self.xN + self.xMin
        self.yMax = gridSquareSize * self.yN + self.yMin

        self.grid = self.makeStartingGrid()
        """values stored in the grid cells"""
        self.graphicsGrid = util.make2DArray(self.xN, self.yN, None)
        """graphics objects"""

        self.makeWindow(windowWidth)
        self.drawWorld()

    def makeWindow(self, windowWidth = defaultWindowWidth, title = 'Grid Map'):
        """
        Create a window of the right dimensions representing the grid map.
        Store in C{self.window}.
        """
        dx = self.xMax - self.xMin
        dy = self.yMax - self.yMin
        maxWorldDim = float(max(dx, dy))
        margin = 0.01*maxWorldDim
        margin = 0.0*maxWorldDim
        self.window = dw.DrawingWindow(int(windowWidth*dx/maxWorldDim),
                                int(windowWidth*dy/maxWorldDim),
                                self.xMin - margin, self.xMax + margin,
                                self.yMin - margin, self.yMax + margin, 
                                title)
        windows.windowList.append(self.window)

    def xToIndex(self, x):
        """
        @param x: real world x coordinate
        @return: x grid index it maps into
        """
        shiftedX = x - self.xStep/2.0
        return util.clip(int(round((shiftedX-self.xMin)/self.xStep)),
                         0, self.xN-1)
    
    def yToIndex(self, y):
        """
        @param y: real world y coordinate
        @return: y grid index it maps into
        """
        shiftedY = y - self.yStep/2.0
        return util.clip(int(round((shiftedY-self.yMin)/self.yStep)),
                         0, self.yN-1)

    def indexToX(self, ix):
        """
        @param ix: grid index in the x dimension
        @return: the real x coordinate of the center of that grid cell
        """
        return self.xMin + float(ix)*self.xStep + self.xStep/2.0

    def indexToY(self, iy):
        """
        @param iy: grid index in the y dimension
        @return: the real y coordinate of the center of that grid cell
        """
        return self.yMin + float(iy)*self.yStep + self.yStep/2.0

    def pointToIndices(self, point):
        """
        @param point: real world point coordinates (instance of C{Point})
        @return: pair of (x, y) grid indices it maps into
        """
        return (self.xToIndex(point.x),self.yToIndex(point.y))

    def indicesToPoint(self, (ix,iy)):
        """
        @param ix: x index of grid cell
        @param iy: y index of grid cell
        @return: c{Point} in real world coordinates of center of cell
        """
        return util.Point(self.indexToX(ix), self.indexToY(iy))


    def boxDim(self):
        """
        @returns: size of a grid cell in the drawing window in pixels
        """
        pixelMargin = 10
        return int((self.window.windowWidth / float(self.xN)) - pixelMargin)

    def drawWorld(self):
        """
        Clears the whole window and redraws the grid
        """
        self.window.clear()
        for xIndex in range(self.xN):
            for yIndex in range(self.yN):
                self.graphicsGrid[xIndex][yIndex] = \
                               self.drawNewSquare((xIndex, yIndex))
                self.drawSquare((xIndex, yIndex))

    def drawNewSquare(self, indices, color = None):
        """
        @param indices: C{(ix, iy)} indices of grid cell
        @param color: Python color to draw the square;  if C{None}
        uses the C{self.squareColor} method to determine a color.
        Draws a box at the specified point, on top of whatever is there
        """
        if color == None:
            color = self.squareColor(indices)
        
        p = self.indicesToPoint(indices)

        return self.window.drawSquare(p.x, p.y, self.xStep*0.75, color)

    def drawSquare(self, indices, color = None):
        """
        Recolors the existing square
        @param indices: C{(ix, iy)} indices of grid cell
        @param color: Python color to draw the square;  if C{None}
        uses the C{self.squareColor} method to determine a color.
        """
        if color == None:
            color = self.squareColor(indices)
        (xIndex, yIndex) = indices
        item = self.graphicsGrid[xIndex][yIndex]
        self.window.canvas.itemconfig(item, fill = color, outline = color)

    def drawPath(self, path):
        """
        Draws list of cells;  first one is purple, last is yellow,
        rest are blue
        @param path: list of pairs of C{(ix, iy)} grid indices
        """
        self.drawSquare(path[0], 'purple')
        for p in path[1:-1]:
            self.drawSquare(p, color = 'blue')
        self.drawSquare(path[-1], 'gold')

    def undrawPath(self, path):
        """
        Draws list of cells using the underlying grid color scheme,
        effectively 'undrawing' a path.
        @param path: list of pairs of C{(ix, iy)} grid indices
        """
        for p in path:
            self.drawSquare(p)

    def squareColor(self, indices):
        """
        Default color scheme:  squares that the robot can occupy are
        white and others are black.
        """
        if self.robotCanOccupy(indices):
            return 'white'
        else:
            return 'black'

import gridMap
import math
import util
import colors

class DynamicCountingGridMap(gridMap.GridMap):
    """
    Implements the C{GridMap} interface.
    """
    def __init__(self, xMin, xMax, yMin, yMax, gridSquareSize):
        """
        @param fixMe
        """
        self.xMin = xMin
        """X coordinate of left edge"""
        self.xMax = xMax
        """X coordinate of right edge"""
        self.yMin = yMin
        """Y coordinate of bottom edge"""
        self.yMax = yMax
        """Y coordinate of top edge"""
        self.xN = int(math.ceil(self.xMax / gridSquareSize))
        """number of cells in x dimension"""
        self.yN = int(math.ceil(self.yMax / gridSquareSize))
        """number of cells in y dimension"""
        self.xStep = gridSquareSize
        """size of a side of a cell in the x dimension"""
        self.yStep = gridSquareSize
        """size of a side of a cell in the y dimension"""

        ## Readjust the max dimensions to handle the fact that we need
        ## to have a discrete numer of grid cells
        self.xMax = gridSquareSize * self.xN
        self.yMax = gridSquareSize * self.yN

        self.grid = util.make2DArray(self.xN, self.yN, 0)
        """values stored in the grid cells"""

        self.growRadiusInCells = int(math.ceil(gridMap.robotRadius\
                                               / gridSquareSize))
        self.makeWindow()
        self.drawWorld()

    def squareColor(self, indices):
        """
        @param documentme
        """
        (xIndex, yIndex) = indices
        maxValue = 10
        storedValue = util.clip(self.grid[xIndex][yIndex], -maxValue, maxValue)
        v = util.clip((maxValue - storedValue) / maxValue, 0, 1)
        s = util.clip((storedValue + maxValue) / maxValue, 0, 1)
        if self.robotCanOccupy(indices):
            hue = colors.greenHue
        else:
            hue = colors.redHue
        return colors.RGBToPyColor(colors.HSVtoRGB(hue, 0.2 + 0.8 * s, v))

    def setCell(self, (xIndex, yIndex)):
        self.grid[xIndex][yIndex] += 2
        self.drawSquare((xIndex, yIndex))
        
    def clearCell(self, (xIndex, yIndex)):
        self.grid[xIndex][yIndex] -= 0.25
        self.drawSquare((xIndex, yIndex))

    def occupied(self, (xIndex, yIndex)):
        return self.grid[xIndex][yIndex] > 2

    def robotCanOccupy(self, (xIndex, yIndex)):
        # Really inefficient.  Should cache this in another array and
        # update it when we update grid cells.
        for dx in range(0, self.growRadiusInCells + 1):
            for dy in range(0, self.growRadiusInCells + 1):
                xPlus = util.clip(xIndex+dx, 0, self.xN-1)
                xMinus = util.clip(xIndex-dx, 0, self.xN-1)
                yPlus = util.clip(yIndex+dy, 0, self.yN-1)
                yMinus = util.clip(yIndex-dy, 0, self.yN-1)
                if self.grid[xPlus][yPlus] > 2 or \
                   self.grid[xPlus][yMinus] > 2 or \
                   self.grid[xMinus][yPlus] > 2 or \
                   self.grid[xMinus][yMinus] > 2:
                    return False
        return True

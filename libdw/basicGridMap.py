"""
Simple grid map with values equal to C{True} and C{False}.
Initialized by reading in a soar world file.
"""

import gridMap
reload(gridMap)
import soarWorld
import math
import util

class BasicGridMap(gridMap.GridMap):
    """
    Implements the C{GridMap} interface.
    """
    def __init__(self, worldPath, gridSquareSize, windowWidth = 400):
        """
        Reads in a world file.  Gets boundary dimensions and aspect
        ratio from there.  Grid cells are square, with size gridSquareSize

        @param worldPath: String representing path to a soar world
        definition file  
        @param gridSquareSize: size, in world coordinates, of a grid
        square
        @param windowWidth: size, in pixels, to make the window for
        drawing this map  
        """
        self.world = soarWorld.SoarWorld(worldPath)
        gridMap.GridMap.__init__(self, 0, float(self.world.dimensions[0]),
                                 0, float(self.world.dimensions[1]),
                                 gridSquareSize, windowWidth)

    def makeStartingGrid(self):
        """
        Called by C{gridMap.GridMap.__init__}.  Returns the initial
        value for the grid, which will be stored in C{self.Grid}.
        """
        g = util.make2DArray(self.xN, self.yN, False)

        # write the walls into the grid, grown by robot radius
        # won't work if boxes are much bigger than robot
        for i in range(self.xN):
            for j in range(self.yN):
                boxSegs = self.indicesToBoxSegs((i, j))
                for wall in self.world.wallSegs:
                    for s in boxSegs:
                        if s.intersection(wall):
                            g[i][j] = True
        return g

    def robotCanOccupy(self, (xIndex, yIndex)):
        """
        Returns C{True} if the robot's center can be at any location
        within this cell and not cause a collision.
        """
        return not self.grid[xIndex][yIndex]

    def indicesToBoxSegs(self, indices):
        """
        @param indices: pair of C{(ix, iy)} indices of a grid cell
        @returns: list of four line segments that constitute the
        boundary of the cell, grown by the radius of the robot, which
        is found in C{gridMap.robotRadius}.
        """
        center = self.indicesToPoint(indices)
        xs = self.xStep/2 + gridMap.robotRadius
        ys = self.yStep/2 + gridMap.robotRadius
        vertices =  [center + util.Point(xs, ys),
                     center + util.Point(xs, -ys),
                     center + util.Point(-xs, -ys),
                     center + util.Point(-xs, ys)]
        segs = [util.LineSeg(vertices[0], vertices[1]),
                util.LineSeg(vertices[1], vertices[2]),
                util.LineSeg(vertices[2], vertices[3]),
                util.LineSeg(vertices[3], vertices[0])]
        return segs
                
                

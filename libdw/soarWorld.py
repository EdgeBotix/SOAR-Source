"""
Read in a soar simulated world file and represent its walls as lists
of line segments.
"""

import util
reload(util)

class SoarWorld:
    """
    Represents a world in the same way as the soar simulator
    """
    def __init__(self, path):
        """
        @param path: String representing location of world file
        """
        self.walls = []
        """
        Walls represented as list of pairs of endpoints
        """
        self.wallSegs = []
        """
        Walls represented as list of C{util.lineSeg}
        """
        # set the global world
        global world
        world = self
        # execute the file for side effect on world
        execfile(path)
        # put in the boundary walls
        (dx, dy) = self.dimensions
        wall((0,0), (0,dy))
        wall((0,0), (dx,0))
        wall((dx,0), (dx,dy))
        wall((0,dy), (dx,dy))
        
    def initialLoc(self, x, y):
        # Initial robot location
        self.initialRobotLoc = util.Point(x,y)
    def dims(self, dx, dy):
        # x and y dimensions
        self.dimensions = (dx, dy)
    def addWall(self, (xlo, ylo), (xhi, yhi)):
        # walls are defined by two points
        self.walls.append((util.Point(xlo, ylo), util.Point(xhi, yhi)))
        # also store representation as line segments
        self.wallSegs.append(util.LineSeg(util.Point(xlo, ylo),
                                          util.Point(xhi, yhi)))

### Gross stuff that lets the soar world file change the global world
def initialRobotLoc(x,y):
    world.initialLoc(x,y)
def dimensions(x,y):
    world.dims(x,y)
def wall(p1, p2):
    world.addWall(p1, p2)        
### Gross stuff that lets the soar world file change the global world


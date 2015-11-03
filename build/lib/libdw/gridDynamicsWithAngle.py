import sm
import util
import math
import gridMap

class GridDynamics(sm.SM):
    """
    An SM representing an abstract grid-based view of a world.
    Use the XY resolution of the underlying grid map.
    Action space is to move to a neighboring square
    States are grid coordinates
    Output is just the state

    To use this for planning, we need to supply both start and goal.
    """

    def __init__(self, theMap, rotationCost = None):
        """
        @param theMap: instance of {\tt gridMap.GridMap}
        """
        self.theMap = theMap
        """instance of C{gridMap.GridMap} representing locations of
        obstacles, with discretized poses"""
        self.startState = None
        self.legalInputs = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)\
                            if (dx != 0 or dy != 0)]
        """In any state, you can move to any of the eight neighboring
        squares or stay in place.  Actions are (dx, dy), where dx and dy
        changes in x and y indices, in the set (-1, 1, 0)."""
        if rotationCost is None:
            self.rotationCost = 0.5/math.pi # rotation of pi = 0.5 meters
        else:
            self.rotationCost = rotationCost

    def getNextValues(self, state, inp):
        """
        @param state: tuple of indices C{(ix, iy)} representing
        robot's location in grid map
        @param inp: an action, which is one of the legal inputs
        @returns: C{(nextState, cost)}
        """
        (ix, iy, angle) = state
        (dx, dy) = inp
        (newX, newY) = (ix + dx, iy + dy)
        if not self.legal(ix, iy, newX, newY):
            # Stay here; but every step has to have positive cost
            return (state, 10)
        else:
            # compute the distance (sq) in meters
            delta = math.sqrt((dx*self.theMap.xStep)**2 + \
                              (dy*self.theMap.yStep)**2)
            target = math.atan2(dy, dx)
            turn = abs(util.fixAnglePlusMinusPi(target - angle))
            return ((newX, newY, target), delta + self.rotationCost*turn)

    def legal(self, ix, iy, newX, newY):
        # Don't cut corners.
        for x in range(min(ix, newX), max(ix, newX) + 1):
            for y in range(min(iy, newY), max(iy, newY) + 1):
                if (x, y) != (ix, iy) and \
                       not self.theMap.robotCanOccupy((x, y)):
                    return False
        return True


import sm
import math

class GridDynamics(sm.SM):
#!    pass
    """
    An SM representing an abstract grid-based view of a world.
    Use the XY resolution of the underlying grid map.
    Action space is to move to a neighboring square
    States are grid coordinates
    Output is just the state

    To use this for planning, we need to supply both start and goal.
    """

    def __init__(self, theMap):
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

    def getNextValues(self, state, inp):
        """
        @param state: tuple of indices C{(ix, iy)} representing
        robot's location in grid map
        @param inp: an action, which is one of the legal inputs
        @returns: C{(nextState, cost)}
        """
        (ix, iy) = state
        (dx, dy) = inp
        (newX, newY) = (ix + dx, iy + dy)
        # compute the distance (sq) in meters
        delta = math.sqrt((dx*self.theMap.xStep)**2 + \
                          (dy*self.theMap.yStep)**2)
        if not self.legal(ix, iy, newX, newY):
            # Stay here; but every step has to have positive cost
            return (state, delta)
        else:
            return ((newX, newY), delta)

    def legal(self, ix, iy, newX, newY):
        # Stay on the map
        if ix < 0 or iy < 0 or ix >= self.theMap.xN or iy >= self.theMap.yN:
            return False
        
        # Don't cut corners.
        for x in range(min(ix, newX), max(ix, newX) + 1):
            for y in range(min(iy, newY), max(iy, newY) + 1):
                if (x, y) != (ix, iy) and \
                       not self.theMap.robotCanOccupy((x, y)):
                    return False
        return True



class GridCostDynamicsSM(sm.SM):
    """
    Fix me
    """

    def __init__(self, theMap):
        """
        @param theMap: instance of {\tt gridMap.GridMap}, with a
        C{cost} method on squares
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

    def getNextValues(self, state, inp):
        """
        @param state: tuple of indices C{(ix, iy)} representing
        robot's location in grid map
        @param inp: an action, which is one of the legal inputs
        @returns: C{(nextState, cost)}
        """
        multiplier = 3
        (ix, iy) = state
        (dx, dy) = inp
        (newX, newY) = (ix + dx, iy + dy)

        if not self.legal(newX, newY):
            # Stay here; but every step has to have positive cost
            return (state, 10)
        else:
#             denom = (1 - self.probCost((ix, iy), (newX, newY)))**4
#             return ((newX, newY), 1.0 / max(denom, .0001))
            p = max(1-self.probCost((ix, iy), (newX, newY)), 0.00001)
            return ((newX, newY), abs(math.log(p)**4))

# prob success = Prod pfree_i
# proportional to Sum log pfree_i
# minimize sum (- log pfree)
# Good:  costs are positive

    def probCost(self, (ix, iy), (newX, newY)):
        # max occ prob of squares we have to traverse
        cost = 0
        for x in range(min(ix, newX), max(ix, newX) + 1):
            for y in range(min(iy, newY), max(iy, newY) + 1):
                if not (x == ix and y == iy):
                    cost = max(cost, self.theMap.cost((x, y)))
        return cost


    def legal(self, ix, iy):
        return ix >= 0 and ix < self.theMap.xN and \
               iy >= 0 and iy < self.theMap.yN

#!

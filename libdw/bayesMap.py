import dist
import util
import colors
import ssm
import seFast
import dynamicGridMap

falsePos = 0.3
falseNeg = 0.3

initPOcc = 0.1
occThreshold = 0.8

#!
# Define the stochastic state-machine model for a given cell here.

# Observation model:  P(obs | state)
def oGivenS(s):
#!    pass    
    if s == 'empty':
        return dist.DDist({'hit': falsePos, 'free': 1 - falsePos})
    else: # occ
        return dist.DDist({'hit': 1 - falseNeg, 'free': falseNeg})
#!
# Transition model: P(newState | s | a)
def uGivenAS(a):
#!     pass    
    return lambda s: dist.DDist({s: 1.0})
#!
#!cellSSM = None   # Your code here
cellSSM = ssm.StochasticSM(dist.DDist({'occ': initPOcc, 'empty': 1 - initPOcc}),
                           uGivenAS, oGivenS)

#!

class BayesGridMap(dynamicGridMap.DynamicGridMap):

    def squareColor(self, (xIndex, yIndex)):
        p = self.occProb((xIndex, yIndex))
        if self.robotCanOccupy((xIndex,yIndex)):
            return colors.probToMapColor(p, colors.greenHue)
        elif self.occupied((xIndex, yIndex)):
            return 'black'
        else:
            return 'red'
        
    def occProb(self, (xIndex, yIndex)):
#!        pass        
        return self.grid[xIndex][yIndex].state.prob('occ')
#!
    def makeStartingGrid(self):
#!        pass        
        def makeEstimator(ix, iy):
            m = seFast.StateEstimator(cellSSM)
            m.start()
            return m
        return util.make2DArrayFill(self.xN, self.yN, makeEstimator)
#!
    def setCell(self, (xIndex, yIndex)):
#!        pass        
        
        self.grid[xIndex][yIndex].step(('hit', None))
        self.drawSquare((xIndex, yIndex))
#!        
    def clearCell(self, (xIndex, yIndex)):
#!        pass        
        self.grid[xIndex][yIndex].step(('free', None))
        self.drawSquare((xIndex, yIndex))
#!
    def occupied(self, (xIndex, yIndex)):
#!        pass        
        return self.occProb((xIndex, yIndex)) > occThreshold

    def explored(self, (xIndex, yIndex)):
        p = self.grid[xIndex][yIndex].state.prob('occ')
        return p > 0.8 or p < 0.1

    def cost(self, (xIndex, yIndex)):
        cost = 0
        for dx in range(0, self.growRadiusInCells + 1):
            for dy in range(0, self.growRadiusInCells + 1):
                xPlus = util.clip(xIndex+dx, 0, self.xN-1)
                xMinus = util.clip(xIndex-dx, 0, self.xN-1)
                yPlus = util.clip(yIndex+dy, 0, self.yN-1)
                yMinus = util.clip(yIndex-dy, 0, self.yN-1)
                cost = max(cost, self.cost1((xPlus, yPlus)),
                           self.cost1((xPlus,yMinus)),
                           self.cost1((xMinus, yPlus)),
                           self.cost1((xMinus, yMinus)))
        return cost

    def cost1(self, (xIndex, yIndex)):
        return self.grid[xIndex][yIndex].state.prob('occ')
#!

mostlyHits = [('hit', None), ('hit', None), ('hit', None), ('free', None)]
mostlyFree = [('free', None), ('free', None), ('free', None), ('hit', None)]

def testCellDynamics(cellSSM, input):
    se = seFast.StateEstimator(cellSSM)
    return se.transduce(input)


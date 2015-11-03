import math
import sonarDist
import sm
import util
import gridMap
import dynamicGridMap
import dynamicCountingGridMap
import bayesMap
reload(bayesMap)

class MapMaker(sm.SM):
#!    def __init__(self, xMin, xMax, yMin, yMax, gridSquareSize):
    """
    It violates the state machine protocol because it changes the grid
    map by side effect, rather than making a fresh copy each time.
    """
    def __init__(self, xMin, xMax, yMin, yMax, gridSquareSize,
                 useClearInfo = False, useCountingMap = False,
                 useBayesMap = True): 

        if useCountingMap:
            gm = dynamicCountingGridMap.DynamicCountingGridMap(\
                                        xMin, xMax, yMin, yMax, gridSquareSize)
        elif useBayesMap:
            gm = bayesMap.BayesGridMap(xMin, xMax, yMin, yMax, gridSquareSize)
        else:
            gm = dynamicGridMap.DynamicGridMap(xMin, xMax, yMin, yMax,
                                               gridSquareSize)
        self.startState = gm
        self.useClearInfo = useClearInfo or useBayesMap
        if useClearInfo: print 'Using clear info'
#!
#!         self.startState = None   # change this
#!
    def getNextValues(self, state, inp):
#!        pass        
        """
        @param inp: instance of C{SensorInput}
        @param state: is C{grid}
        Modifies grid
        """
        grid = state
        robotPose = inp.odometry
#         if self.useClearInfo:
#             self.clearUnderRobot(grid, robotPose)
        self.processSonarReadings(grid, robotPose, inp.sonars)
        return (grid, grid)

    def processSonarReadings(self, grid, robotPose, sonars):
        """
        For each reading that is less than the reliable length, set the
        point at the end to be occupied and the points along the ray up
        to that point to be free.
        """
        for (sonarPose, d) in zip(sonarDist.sonarPoses, sonars):
            # location of sensor in global frame
            s = grid.pointToIndices(robotPose.transformPoint(\
                sonarPose.point()))
            if d < sonarDist.sonarMax:
                # location of sonar 'hit point' in global frame
                h = grid.pointToIndices(\
                         sonarDist.sonarHit(d, sonarPose, robotPose))
                # clear list of grid points on the line between the sensor
                # and the hit point, not including the hit point
                if self.useClearInfo:
                    for ci in util.lineIndices(s, h)[:-1]:
                        grid.clearCell(ci)
                # Fill in the end point of the reading
                grid.setCell(h)
            else:
                # assume clear if no return (risky)
                d = sonarDist.sonarMax
                h = grid.pointToIndices(\
                         sonarDist.sonarHit(d, sonarPose, robotPose))
                # clear list of grid points on the line between the sensor
                # and the hit point, not including the hit point
                if self.useClearInfo:
                    for ci in util.lineIndices(s, h)[:-1]:
                        grid.clearCell(ci)
                
    def clearUnderRobot(self, grid, robotPose):
        rr =  (int(gridMap.robotRadius / grid.xStep) - 1) * grid.xStep
        corners = \
          [grid.pointToIndices(robotPose.transformPoint(util.Point(rr, rr))),
           grid.pointToIndices(robotPose.transformPoint(util.Point(rr, -rr))),
           grid.pointToIndices(robotPose.transformPoint(util.Point(-rr, rr))),
           grid.pointToIndices(robotPose.transformPoint(util.Point(-rr, -rr)))]
        minX = min([cx for (cx, cy) in corners])
        maxX = max([cx for (cx, cy) in corners])
        minY = min([cy for (cx, cy) in corners])
        maxY = max([cy for (cx, cy) in corners])
        for ix in range(minX, maxX+1):
            for iy in range(minY, maxY+1):
                grid.clearCell((ix, iy))

#!                
                
# For testing your map maker
class SensorInput:
    def __init__(self, sonars, odometry):
        self.sonars = sonars
        self.odometry = odometry

testData = [SensorInput([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                        util.Pose(1.0, 2.0, 0.0)),
            SensorInput([0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
                        util.Pose(4.0, 2.0, -math.pi))]

testClearData = [SensorInput([1.0, 5.0, 5.0, 1.0, 1.0, 5.0, 5.0, 1.0],
                             util.Pose(1.0, 2.0, 0.0)),
                 SensorInput([1.0, 5.0, 5.0, 1.0, 1.0, 5.0, 5.0, 1.0],
                             util.Pose(4.0, 2.0, -math.pi))]

def testMapMaker(data):
    (xMin, xMax, yMin, yMax, gridSquareSize) = (0, 5, 0, 5, 0.1)
    mapper = MapMaker(xMin, xMax, yMin, yMax, gridSquareSize)
    mapper.transduce(data)
    mapper.startState.drawWorld()

def testMapMakerClear(data):
    (xMin, xMax, yMin, yMax, gridSquareSize) = (0, 5, 0, 5, 0.1)
    mapper = MapMaker(xMin, xMax, yMin, yMax, gridSquareSize)
    for i in range(50):
        for j in range(50):
            mapper.startState.setCell((i, j))
    mapper.transduce(data)
    mapper.startState.drawWorld()

def testMapMakerN(n, data):
    (xMin, xMax, yMin, yMax, gridSquareSize) = (0, 5, 0, 5, 0.1)
    mapper = MapMaker(xMin, xMax, yMin, yMax, gridSquareSize)
    mapper.transduce(data*n)
    mapper.startState.drawWorld()

testClearData = [SensorInput([1.0, 5.0, 5.0, 1.0, 1.0, 5.0, 5.0, 1.0],
                             util.Pose(1.0, 2.0, 0.0)),
                 SensorInput([1.0, 5.0, 5.0, 1.0, 1.0, 5.0, 5.0, 1.0],
                             util.Pose(4.0, 2.0, -math.pi))]


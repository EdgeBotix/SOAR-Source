import util
import dist
import distPlot
import sm
import ssm
import sonarDist
import move
import seGraphics
import idealReadings

# For testing your preprocessor
class SensorInput:
    def __init__(self, sonars, odometry):
        self.sonars = sonars
        self.odometry = odometry

preProcessTestData = [SensorInput([0.8, 1.0], util.Pose(1.0, 0.5, 0.0)),
                       SensorInput([0.25, 1.2], util.Pose(2.4, 0.5, 0.0)),
                       SensorInput([0.16, 0.2], util.Pose(7.3, 0.5, 0.0))]
testIdealReadings = ( 5, 1, 1, 5, 1, 1, 1, 5, 1, 5 )
testIdealReadings100 = ( 50, 10, 10, 50, 10, 10, 10, 50, 10, 50 )

#!
sonarStDev = 0.02
odoStDev = 0.02

##########################################################################
#   Preprocessor
##########################################################################

#!
class PreProcess(sm.SM):
#!    
    """
    State machine that takes, as input, instances of {\tt
    io.SensorInput} and generates as output pairs of (observation,
    input).  The observation is a discretized sonar reading from time
    t-1; the input is an action, which is a discretized distance,
    computed from the difference between the x coordinate of the robot
    at time t and at time t-1.
    """
#!    
    def __init__(self, numObservations, stateWidth):
#!        pass
        """
	@param numObservations: number of discrete observations
        @param stateWidth: width, in meters, of a discrete state
	"""
        self.startState = (None, None)
        self.numObservations = numObservations
        self.stateWidth = stateWidth

    def getNextValues(self, state, inp):
        (lastUpdatePose, lastUpdateSonar) = state
        currentPose = inp.odometry
        currentSonar = idealReadings.discreteSonar(inp.sonars[0],
                                                   self.numObservations)
        # Handle the first step
        if lastUpdatePose == None:
            return ((currentPose, currentSonar), None)
        else:
            action = discreteAction(lastUpdatePose, currentPose,
                                    self.stateWidth)
            print (lastUpdateSonar, action)
            return ((currentPose, currentSonar), (lastUpdateSonar, action))

# Only works when headed to the right
def discreteAction(oldPose, newPose, stateWidth):
    return int(round(oldPose.distance(newPose) / stateWidth))

##########################################################################
#   Model for state estimator
##########################################################################

#!


def makeRobotNavModel(ideal, xMin, xMax, numStates, numObservations):
    
#!    startDistribution = None    # redefine this
    """
    Create a model of a robot navigating in a 1 dimensional world with
    a single sonar.

    @param ideal: list of ideal sonar readings
    @param xMin: minimum x coordinate for center of robot
    @param xMax: maximum x coordinate for center of robot
    @param numStates: number of discrete states into which to divide
    the range of x coordinates
    @param numObservations: number of discrete observations into which to
    divide the range of good sonar observations, between 0 and C{goodSonarRange}

    @returns: an instance of {\tt ssm.StochasticSM} that describes the
    dynamics of the world
    """
    # make initial distribution over states
    startDistribution = dist.UniformDist(range(numStates))

    ######################################################################
    ###  Define observation model
    ######################################################################
    # real width of triangle distribution, in meters
    # obsTriangleWidth = sonarStDev * 3
    obsTriangleWidth = .05
    obsDiscTriangleWidth = max(2,
                               int(obsTriangleWidth * \
                                   (numObservations / sonarDist.sonarMax)))
    
    # Part of distribution common to all observations
    obsBackground = dist.MixtureDist(dist.UniformDist(range(numObservations)),
                                     dist.DeltaDist(numObservations-1),
                                     0.5)
#!

    def observationModel(ix):
        # ix is a discrete location of the robot
        # return a distribution over observations in that state
#!        pass        
        return dist.MixtureDist(dist.triangleDist(ideal[ix],
                                                  obsDiscTriangleWidth,
                                                  0, numObservations),
                                obsBackground,
                                0.9)

    ######################################################################
    ###  Define transition model
    ######################################################################

    # real width of triangle distribution, in meters
    transTriangleWidth = odoStDev * 3
    transDiscTriangleWidth = max(2,
                                 int(transTriangleWidth *
                                     (numStates / (xMax-xMin))))
    transDiscTriangleWidth = 2
    teleportProb = 0

#!

    def transitionModel(a):
        # a is a discrete action
        # returns a conditional probability distribution on the next state
        # given the previous state
#!        pass        
        def transitionGivenState(s):
            # A uniform distribution we mix in to handle teleportation
            transUniform = dist.UniformDist(range(numStates))
            return dist.MixtureDist(dist.triangleDist(\
                                        util.clip(s+a, 0, numStates-1),
                                        transDiscTriangleWidth,
                                        0, numStates-1),
                             transUniform, 1 - teleportProb)
        return transitionGivenState

    ######################################################################
    ###  Create and return SSM
    ######################################################################
#!

    return ssm.StochasticSM(startDistribution, transitionModel,
                            observationModel)

# Main procedure
def makeLineLocalizer(numObservations, numStates, ideal, xMin, xMax, robotY):
#!    pass
    
    """
    Create behavior controlling robot to move in a line and to
                      localize itself in one dimension

    @param numObservations: number of discrete observations into which to
    divide the range of good sonar observations, between 0 and C{goodSonarRange}
    @param numStates: number of discrete states into which to divide
    the range of x coordinates
    @param ideal: list of ideal sonar readings
    @param xMin: minimum x coordinate for center of robot
    @param xMax: maximum x coordinate for center of robot
    @param robotY: constant y coordinate for center of robot

    @returns: an instance of {\tt sm.SM} that implements the behavior
    """

    # Size of a state in meters
    stateWidthMeters = (xMax - xMin) / float(numStates)

    preprocessor = PreProcess(numObservations, stateWidthMeters)
    navModel = makeRobotNavModel(ideal, xMin, xMax, numStates, numObservations)
    estimator = seGraphics.StateEstimator(navModel)
    driver = move.MoveToFixedPose(util.Pose(xMax, robotY, 0.0), maxVel = 0.5)
    
    return sm.Cascade(sm.Parallel(sm.Cascade(preprocessor, estimator),
                                  driver),
                      sm.Select(1))

#     metric = makeMetricMachine(xMin, xMax, robotY, numStates)
#     sensor = corruptInput.SensorCorrupter(sonarStDev, odoStDev)
#     return sm.Cascade(sm.Parallel(sm.Cascade(sm.Parallel(sm.Wire(),
#                                              sm.Cascade(sensor,
#                                                sm.Cascade(preprocessor,
#                                                           estimator))),
#                                              metric),
#                              driver), 
#                  sm.Select(1))
                        
######################################################################
###      Assess the quality of localization
######################################################################

def makeMetricMachine(xMin, xMax, y, numStates):
    """
    @param xMin: minimum x coordinate for center of robot
    @param xMax: maximum x coordinate for center of robot
    @param y: constant y coordinate for center of robot
    @param numStates: number of discrete states into which to divide
    the range of x coordinates
    @returns: a state machine that takes two inputs: C{(sensorInput,
    belief)}, where C{sensorInput} is the true sensor input (we can
    trust the pose in simulation to be the actual truth) and C{belief}
    is a distribution over possible discrete robot locations,
    delivered by the state estimator.  The state machine can deliver a
    metric (averaged over time) as output;  it should also print the
    metric value on each step.
    """

    probRange = 0.1
    stateWidth =  (xMax - xMin) / float(numStates)

    def xToState(x):
        return util.clip(int(round(numStates * (x - xMin) / (xMax - xMin))),
                         0, numStates-1)

    class Metric(sm.SM):
        startState = (0, 0)  # total and count
    
        def getNextValues(self, state, inp):
            # output is average probability mass in range of true loc
            (cheat, b) = inp
            (overallTotal, count) = state
            trueState = xToState(cheat.odometry.x)
            lo = xToState(cheat.odometry.x - probRange)
            hi = xToState(cheat.odometry.x + probRange)
            total = 0
            for i in range(util.clip(lo, 0, numStates-1),
                           util.clip(hi, 1, numStates)):
                total += b.prob(i)

#            print 'score', total, (overallTotal + total) / (count + 1.0)
            return ((overallTotal + total, count + 1),
                    (overallTotal + total) / (count + 1.0))

    return Metric()
        

#!

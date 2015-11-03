"""
State estimation example: localization in a colored hallway
"""

import util
import sm
import ssm
import se
import colors
import dist
import dw
from dw import DrawingWindow
reload(dw)

possibleColors = ('black', 'white', 'red', 'green', 'blue', 'purple', 'orange',
                  'darkGreen', 'gold', 'chocolate', 'PapayaWhip',
                  'MidnightBlue', 'HotPink', 'chartreuse')
"""
Possible colors for rooms in our hallway
"""

def makeObservationModel(hallwayColors, obsNoise):
    """
    @param hallwayColors: list of colors, one for each room in the
    hallway, from left to right
    @param obsNoise: conditional distribution specifying the
    probability of observing a color given the actual color of the room
    @returns: conditional distribution specifying probability of
    observing a color given the robot's location

    Remember that a conditional distribution P(A | B) is represented
    as a function from values of b to distributions over A.
    """
    return lambda loc: obsNoise(hallwayColors[loc])

def perfectObsNoiseModel(actualColor):
    """
    @param actualColor: actual color in a location
    @returns: C{DDist} over observed colors when in a room that has
    C{actualColor}.  In this case, we observe the actual color with
    probability 1.  
    """
    return dist.DDist({actualColor: 1.0})

def noisyObsNoiseModel(actualColor):
    """
    @param actualColor: actual color in a location
    @returns: C{DDist} over observed colors when in a room that has
    C{actualColor}.  In this case, we observe the actual color with
    probability 0.8, and the remaining 0.2 probability is divided
    uniformly over the other possible colors in this world.
    """
    d = {}
    for observedColor in possibleColors:
        if observedColor == actualColor:
            d[observedColor] = 0.8
        else:
            d[observedColor] = 0.2 / (len(possibleColors) - 1)
    return dist.DDist(d)

def makeTransitionModel(dynamics, noiseDist, hallwayLength):
    """
    @param dynamics: function that takes the robot's current location,
    action, and hallwaylength, and returns its nominal new location
    @param noiseDist: P(actualResultingLocation | nominalResultingLoc)
    represented as a function from ideal location to the actual
    location the robot will end up in
    @param hallwayLength: number of rooms in the hallway
    @returns: P(actualResultingLoc | previousLoc, action) represented
    as a function that takes an action and returns a function that
    takes a previous location and returns a distribution over actual
    resulting locations.
    """
    return lambda act: lambda loc: noiseDist(dynamics(loc, act, hallwayLength),
                                             hallwayLength)

def standardDynamics(loc, act, hallwayLength):
    """
    @param loc: current loc (integer index) of the robot
    @param act: a positive or negative integer (or 0) indicating the
    nominal number of squares moved
    @param hallwayLength: number of cells in the hallway
    @returns: new loc of the robot assuming perfect execution.  If the action
    would take it out of bounds, the robot stays where it is.
    """
    return util.clip(loc + act, 0, hallwayLength-1)

def ringDynamics(loc, act, hallwayLength):
    """
    @param loc: current loc (integer index) of the robot
    @param act: positive or negative integer offset
    @param hallwayLength: number of cells in the hallway
    @returns: new loc of the robot, assuming perfect execution where
    the hallway is actually a ring (so that location 0 is next to
    location C{hallwayLength -1}).
    """
    return (loc + act) % hallwayLength

def perfectTransNoiseModel(nominalLoc, hallwayLength):
    """
    @param nominalLoc: location that the robot would have ended up
    given perfect dynamics
    @param hallwayLength: length of the hallway
    @returns: distribution over resulting locations, modeling noisy
    execution of commands;  in this case, the robot goes to the
    nominal location with probability 1.0
    """
    return dist.DDist({nominalLoc : 1.0})

def noisyTransNoiseModel(nominalLoc, hallwayLength):
    """
    @param nominalLoc: location that the robot would have ended up
    given perfect dynamics
    @param hallwayLength: length of the hallway
    @returns: distribution over resulting locations, modeling noisy
    execution of commands;  in this case, the robot goes to the
    nominal location with probability 0.8, goes one step too far left with
    probability 0.1, and goes one step too far right with probability 0.1.
    If any of these locations are out of bounds, then the associated
    probability mass goes is assigned to the boundary location (either
    0 or C{hallwayLength-1}).  
    """
    d = {}
    dist.incrDictEntry(d, util.clip(nominalLoc-1, 0, hallwayLength-1), 0.1)
    dist.incrDictEntry(d, util.clip(nominalLoc, 0, hallwayLength-1), 0.8)
    dist.incrDictEntry(d, util.clip(nominalLoc+1, 0, hallwayLength-1), 0.1)
    return dist.DDist(d)


def leftSlipTransNoiseModel(nominalLoc, hallwayLength):
    """
    @param nominalLoc: location that the robot would have ended up
    given perfect dynamics
    @param hallwayLength: length of the hallway
    @returns: distribution over resulting locations, modeling noisy
    execution of commands;  in this case, the robot goes to the
    nominal location with probability 0.9, and goes one step too far
    left with probability 0.1.
    If any of these locations are out of bounds, then the associated
    probability mass stays at C{nominalLoc}.
    """
    d = {}
    dist.incrDictEntry(d, util.clip(loc-1, 0, n-1), 0.1)
    dist.incrDictEntry(d, util.clip(loc, 0, n-1), 0.9)
    return dist.DDist(d)
    
######################################################################
##
##  UI stuff
##
######################################################################

def textOutput(result):
    print 'Machine output:', result

class TextInputSM(sm.SM):
    """
    Machine that prompts a user for an input on each step.  That input
    is the output of this machine.  If the user types 'quit', then the
    machine terminates.
    """
    def __init__(self, legalInputs):
        self.legalInputs = legalInputs + ['quit']
    startState = False
    def getNextValues(self, state, inp):
        out = None
        first = True
        while not out in self.legalInputs:
            if not first: print 'Illegal input:', out
            out = raw_input('Type an input (' + \
                            util.prettyString(self.legalInputs) + \
                            ' ): ')
            if not out == 'quit': out = int(out)
            first = False
        return (out == 'quit', out)
    def done(self, state):
        return state

def wrapTextUI(m):
    """
    @param m: An instance of C{sm.SM}
    @returns: A composite machine that prompts the user for input to, and
    prints the output of C{m} on each step.
    """
    return sm.Cascade(sm.Cascade(TextInputSM(),
                                 m),
                      sm.PureFunction(textOutput))

def wrapWindowUI(m, worldColors, legalInputs, windowName = 'Belief',
                 initBelief = None):
    """
    @param m: A machine created by applying
    C{se.makeStateEstimationSimulation} to a hallway world, which
    take movement commands as input and generates as output structures
    of the form C{(b, (o, a))}, where C{b} is a belief state, C{a} is
    the action command, and C{o} is the observable output generated by
    the world.
    @param worldColors: A list of the colors of the rooms in the
    hallway, from left to right.
    @returns: A composite machine that prompts the user for input to, and
    graphically displays the output of C{m} on each step.
    """
    def drawWorld(size):
        y = 0
        for x in range(size):
            window.drawRect((x, y), (x+1, y+1), color = worldColors[x])

    def processOutput(stuff):
        (dist, (o, a)) = stuff
        drawWorld(dim)
        drawBelief(dist, window, dim)
        return (o, a)

    def processInput(stuff):
        if stuff == 'quit':
            print 'Taking action 0 before quitting'
            return 0
        else:
            return int(stuff)
        
    dim = len(worldColors)
    if not initBelief:
        initBelief = dist.UniformDist(range(dim))
    ydim = 1
    window = DrawingWindow(dim*50, ydim*50+10, -0.2, dim+0.2, -0.2,
                           ydim+0.2, windowName)
    drawWorld(dim)
    drawBelief(initBelief, window, dim)
    return sm.Cascade(sm.Cascade(sm.Cascade(TextInputSM(legalInputs),
                                            sm.PureFunction(processInput)),
                                 m),
                      sm.PureFunction(processOutput))

def drawBelief(belief, window, numStates, drawNums = True):
    unifP = 1.0/numStates
    y = 0
    for x in range(numStates):
        # The last arg to the color selection is a rough estimate of
        # the highest probability that will actually occur.  Should
        # always be 1 or less.
        window.drawRect((x + 0.2, y + 0.2), (x + 0.8, y + 0.8),
                     color = colors.probToPyColor(belief.prob(x), unifP,
                                          (unifP + 0.3) / 1.3))
        if drawNums:
            window.drawText(x + 0.5, y + 0.5, "%3.2f" % belief.prob(x),
                            color = 'white')

######################################################################
##
##   Making state estimator machines
##
######################################################################

standardHallway = ['white', 'white', 'green', 'white', 'white']
"""Our favorite configuration of hallway colors"""

def makeSESwithGUI(worldSM, realColors, legalInputs, initBelief = None,
                   verbose = False, title = 'hallway'):
    """
    Makes a colored hallway simulator and state estimator.  Text input
    for actions and graphical display of world and belief state.
    @param worldSM: instance of C{ssm.StochasticSM} representing the
    world
    @param realColors: A list of the colors of the rooms in the
    hallway, from left to right.
    @param legalInputs: A list of the possible action commands
    @param verbose: if C{True} then print out belief state after each update
    @param title: title of window being created
    """
    return wrapWindowUI(se.makeStateEstimationSimulation(worldSM, verbose),
                        realColors, legalInputs, title, initBelief = initBelief)

def makeSim(hallwayColors, legalInputs, obsNoise, dynamics, transNoise,
            title = 'sim', initialDist = None):
    """
    Make an instance of the simulator with noisy motion and sensing models.
    @param hallwayColors: A list of the colors of the rooms in the
    hallway, from left to right.
    @param legalInputs: A list of the possible action commands
    @param obsNoise: conditional distribution specifying the
    probability of observing a color given the actual color of the room
    @param dynamics: function that takes the robot's current location,
    action, and hallwaylength, and returns its nominal new location
    @param transNoise: P(actualResultingLocation | nominalResultingLoc)
    represented as a function from ideal location to the actual
    location the robot will end up in
    @param title: String specifying title for simulator window
    """
    n = len(hallwayColors)
    if not initialDist:
        initialDist = dist.UniformDist(range(n))
    worldSM = ssm.StochasticSM(initialDist,
                               makeTransitionModel(dynamics, transNoise, n),
                               makeObservationModel(hallwayColors, obsNoise))
    return makeSESwithGUI(worldSM, hallwayColors, legalInputs,
                          verbose = True, title = title,
                          initBelief = initialDist)

def hallSE(hallwayColors, legalInputs, obsNoise, dynamics, transNoise,
           initialDist = None, verbose = True):
    n = len(hallwayColors)
    if not initialDist:
        initialDist = dist.UniformDist(range(n))
    worldSM = ssm.StochasticSM(initialDist,
                               makeTransitionModel(dynamics, transNoise, n),
                               makeObservationModel(hallwayColors, obsNoise))
    return se.StateEstimator(worldSM, verbose)

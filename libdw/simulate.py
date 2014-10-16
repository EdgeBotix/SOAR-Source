# simulate.py
#import inspect
#try:
#    name = inspect.getmodule(inspect.stack()[1][0]).__name__
#except:
#    name = None

#if name == '__main__':                  # CMax
#    import cc
#else:
#    import nlcc as cc
import nlcc as cc
import sm
import sig
import ts
import util

import re
import operator
import types
import sys
import math

# nodes on protoboard
# 't+', 't-', 'b+', 'b-', 'tX', 'bX' for X in [1,64]
# t stands for top, b for bottom

sourceVoltage = 10

# Set to true to show x-axis labels in seconds
# Set to false to show number of samples in plot
xtruescaleflag = True

plotno = 1   # global counter for plot window title bar
plotWindows = []

## Extensions to layout
# Impossible connections

class Circ:
    def __init__(self):
        self.components = []
        self.groundNode = None
        self.probes = []
        self.motorConnections = []
        self.robotConnections = []
        self.headConnections = []
        self.pots = []
        self.componentDict = None
        self.componentDictFull = None

## Simulate netlists

def readLines(filename):
    return [line for line in open(filename)]

# This reads a netlist from a file and returns a list of lists
def readCircuit(lines):
    componentList = []
    opampPattern = r'opamp: \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    resistorPattern = r'resistor\((\d),(\d),(\d)\): \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    wirePattern = r'wire: \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    potPattern = r'pot: \((\d+),(\d+)\)--\((\d+),(\d+)\)--\((\d+),(\d+)\)'
    motorPattern = r'motor: \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    robotPattern = r'robot: \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    powerPattern = r'\+10: \((\d+),(\d+)\)'
    groundPattern = r'gnd: \((\d+),(\d+)\)'
    posprobePattern = r'\+probe: \((\d+),(\d+)\)'
    negprobePattern = r'\-probe: \((\d+),(\d+)\)'
    headPattern = r'head: \((\d+),(\d+)\)--\((\d+),(\d+)\)'
    valid = False
    for line in lines:
        match = re.match(opampPattern,line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Op Amp is not in valid holes, ignoring! '+line
            else:
                componentList.extend(opAmpsFromPins((int(x0),int(y0)),
                                                    (int(x1),int(y1))))
        match = re.match(resistorPattern,line)
        if match:
            (c1,c2,c3,x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Resistor is not in valid holes, ignoring! '+line
            else:
                componentList.extend(resistorFromPins((int(c1),int(c2),int(c3)),
                                                      (int(x0),int(y0)),
                                                      (int(x1), int(y1))))
        match = re.match(wirePattern,line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Wire is not in valid holes, ignoring! '+line
            else:
                componentList.extend(wireFromPins((int(x0),int(y0)),
                                                  (int(x1),int(y1))))
        match = re.match(potPattern,line)
        if match:
            (x0,y0,x1,y1,x2,y2) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and \
                    nodeNameForPin(int(x1),int(y1)) and \
                    nodeNameForPin(int(x2),int(y2))):
                print 'Pot is not in valid holes, ignoring! '+line
            else:
                componentList.extend(potFromPins((int(x0),int(y0)),
                                                 (int(x1),int(y1)),
                                                 (int(x2),int(y2))))
        match = re.match(robotPattern,line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Robot connector is not in valid holes, ignoring! '+line
            else:
                componentList.extend(robotFromPins((int(x0),int(y0)),
                                                   (int(x1),int(y1))))
        match = re.match(motorPattern,line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Motor connector is not in valid holes, ignoring! '+line
            else:
                componentList.extend(motorFromPins((int(x0),int(y0)),
                                                   (int(x1),int(y1))))
        match = re.match(headPattern,line)
        if match:
            (x0,y0,x1,y1) = match.groups()
            if not (nodeNameForPin(int(x0),int(y0)) and nodeNameForPin(int(x1),int(y1))):
                print 'Head connector is not in valid holes, ignoring! '+line
            else:
                componentList.extend(headFromPins((int(x0),int(y0)),
                                                  (int(x1),int(y1))))
        match = re.match(posprobePattern,line)
        if match:
            (x0,y0) = match.groups()
            if not nodeNameForPin(int(x0),int(y0)):
                print 'Positive probe is not in valid hole, ignoring! '+line
            else:
                componentList.extend(probeFromPins('Pos', (int(x0),int(y0))))
        match = re.match(negprobePattern,line)
        if match:
            (x0,y0) = match.groups()
            if not nodeNameForPin(int(x0),int(y0)):
                print 'Negative probe is not in valid hole, ignoring! '+line
            else:
                componentList.extend(probeFromPins('Neg', (int(x0),int(y0))))
        match = re.match(powerPattern,line)
        if match:
            (x0,y0) = match.groups()
            if not nodeNameForPin(int(x0),int(y0)):
                print 'Power connector is not in valid hole, ignoring! '+line
            else:
                componentList.extend(powerFromPins((int(x0),int(y0))))
        match = re.match(groundPattern,line)
        if match:
            (x0,y0) = match.groups()
            if not nodeNameForPin(int(x0),int(y0)):
                print 'Ground connector is not in valid hole, ignoring! '+line
            else:
                componentList.extend(groundFromPins((int(x0),int(y0))))
    return componentList

def componentDict(componentList):
    dict = {}
    for element in componentList:
        for node in element.nodeNames:
            if node != None:
                if node in dict:
                    dict[node] += [element]
                else:
                    dict[node] = [element]
    # print 'componentDict for', componentList, 'is', dict
    return dict

def nodeNameForPin(x, y):
    if x < 1 or x > 63:
        warn('Illegal pin %s,%s'%(x,y))
        return False
    if y == 1: return 't+'
    elif y == 2: return 't-'
    elif y == 19: return 'b+'
    elif y == 20: return 'b-'
    elif 4 < y < 10: return 't'+str(x)
    elif 11 < y < 17: return 'b'+str(x)
    else:
        warn('Illegal pin %s,%s'%(x,y))
        return False       # illegal pin
        #raise Exception, 'Illegal pin %s,%s'%(x,y)

# opamp: (x, y0), (x, y1)
# outputs are on y0, inputs are on y1
# if y0 > y1, pins are [x, x+4] e.g. x = 25, pins = [25,26,27,28]
# if y0 < y1, pins are [x-3, x+1] e.g. x = 33, pins = [30,31,32,33]

def opAmpsFromPins(pin0, pin1):
    (x, y0) = pin0
    (x, y1) = pin1
    # Need to check the power and gnd connection somewhere...
    if y0 < y1:                         # output on top
        return [cc.OpAmp(nodeNameForPin(x-1,y1), nodeNameForPin(x,y1), nodeNameForPin(x,y0)),
                cc.OpAmp(nodeNameForPin(x-2,y1), nodeNameForPin(x-3,y1), nodeNameForPin(x-2,y0)),
                PowerInput('Opamp', nodeNameForPin(x-1, y0)),
                GroundInput('Opamp', nodeNameForPin(x-3, y0))]
    else:                               # output on bottom
        return [cc.OpAmp(nodeNameForPin(x+1,y1), nodeNameForPin(x,y1), nodeNameForPin(x,y0)),
                cc.OpAmp(nodeNameForPin(x+2,y1), nodeNameForPin(x+3,y1), nodeNameForPin(x+2,y0)),
                PowerInput('Opamp', nodeNameForPin(x+1, y0)),
                GroundInput('Opamp', nodeNameForPin(x+3, y0))]

def potFromPins(pin0, pin1, pin2):
    (x0, y0) = pin0
    (x1, y1) = pin1
    (x2, y2) = pin2
    return [Pot(nodeNameForPin(x0,y0), nodeNameForPin(x1,y1), nodeNameForPin(x2,y2))]

def robotFromPins(pin0, pin1):
    (x0, y) = pin0
    (x1, y) = pin1
    print 'robotFromPins', pin0, pin1
    # Pins start at pin0 and increase number until pin1
    if x0 < x1:
        print 'x0 < x1'
        return [Connector('Robot', [nodeNameForPin(x0+i,y) for i in range(8)]),
                Power(nodeNameForPin(x0+1,y)),
                Ground(nodeNameForPin(x0+3,y))]
    else:
        print 'x1 <= x0'
        return [Connector('Robot', [nodeNameForPin(x0-i,y) for i in range(8)]),
                Power(nodeNameForPin(x0-1,y)),
                Ground(nodeNameForPin(x0-3,y))]

def headFromPins(pin0, pin1):
    (x0, y) = pin0
    (x1, y) = pin1
    # Pins start at pin0 and increase number until pin1
    if x0 < x1:
        return [Connector('Head', [nodeNameForPin(x0+i,y) for i in range(8)])]
    else:
        return [Connector('Head', [nodeNameForPin(x0-i,y) for i in range(8)])]

def motorFromPins(pin0, pin1):
    (x0, y) = pin0
    (x1, y) = pin1
    # Pins start at pin0 and increase number until pin1
    if x0 < x1:
        return [Connector('Motor', [nodeNameForPin(x0+i,y) for i in range(6)])]
    else:
        return [Connector('Motor', [nodeNameForPin(x0-i,y) for i in range(6)])]

def powerFromPins(pin0):
    (x0, y0) = pin0
    return [Power(nodeNameForPin(x0,y0))]

def groundFromPins(pin0):
    (x0, y0) = pin0
    return [Ground(nodeNameForPin(x0,y0))]

def probeFromPins(sign, pin0):
    (x0, y0) = pin0
    return [Probe(sign, nodeNameForPin(x0,y0))]

def resistorValue(c):
    return (c[0]*10+c[1])*(10**c[2])

def resistorFromPins(colors, pin0, pin1):
    (x0, y0) = pin0
    (x1, y1) = pin1
    return [cc.Resistor(resistorValue(colors), nodeNameForPin(x0,y0), nodeNameForPin(x1,y1))]

def wireFromPins(pin0, pin1):
    (x0, y0) = pin0
    (x1, y1) = pin1
    return [cc.Wire(nodeNameForPin(x0,y0), nodeNameForPin(x1,y1))]

#  runCircuit(), the caller, forces print output, so no need for flush()  here

def verifyCircuit(componentList):
    circuit = Circ()
    cdict = componentDict(componentList)
    circuit.componentDictFull = cdict
    discard = []
    powerNodes = traceElement('Power', componentList, cdict)
    groundNodes = traceElement('Ground', componentList, cdict)
    powerSrc = []
    groundSrc = []
    probePos = []
    probeNeg = []
    print 'powerNodes=', powerNodes
    print 'groundNodes=', groundNodes
    for element in componentList:
        name = element.__class__.__name__
        if name == 'GroundInput':
            discard.append(element)
            node = element.v1Name
            if not connectedTo(cdict[node], groundNodes):
                warn('%s ground at %s not connected to ground'%(element.type, node))
                return None
        elif name == 'PowerInput':
            discard.append(element)
            node = element.v1Name
            if not connectedTo(cdict[node], powerNodes):
                warn('%s power at %s not connected to power'%(element.type, node))
                return None
        elif name == 'Power':
            discard.append(element)
            powerSrc.append(element.v1Name)
        elif name == 'Ground':
            discard.append(element)
            groundSrc.append(element.v1Name)
        elif name == 'Probe':
            discard.append(element)
            if element.type == 'Pos':
                probePos.append(element.v1Name)
            elif element.type == 'Neg':
                probeNeg.append(element.v1Name)
        elif name == 'Pot':
            discard.append(element)
            circuit.pots.append(element.nodeNames)
        elif name == 'Connector':
            discard.append(element)
            if element.type == 'Robot':
                circuit.robotConnections = element.nodeNames
            if element.type == 'Head':
                circuit.headConnections = element.nodeNames
            elif element.type == 'Motor':
                circuit.motorConnections = element.nodeNames
        else:
            connection = False
            for node in element.nodeNames:
                connections = cdict[node]
                if len(connections) == 1:
                    warn('Element %s not connected to anything at node %s'%(str(element), node))
                else:
                    connection = True
            if connection == False:
                warn('Element %s is disconnected, discarding it'%(str(element)))
                discard.append(element)
            if hasDuplicate(element.nodeNames):
                warn('Element %s has duplicate nodes, discarding it'%(str(element)))
                discard.append(element)
                return None

    # print componentList
    
    if len(groundSrc) != 1:
        warn('There should be exactly one ground!')
        return None
    else:
        circuit.groundNode = groundSrc[0]

    if len(powerSrc) < 1:
        warn('There should be power going to the circuit!')
        return None

    if len(probePos) == 1 and len(probeNeg) == 1:
        circuit.probes = [probePos[0], probeNeg[0]]
    else:
        if len(probePos) > 1 or len(probeNeg) > 1:
            warn('Only one set of probes is supported.')
            return None
        if len(probePos) != len(probeNeg):
            warn('There must be exactly one positive and one negative probe.')
            return None
    # add Vsrcs
    for power in powerSrc:
        componentList.append(cc.VSrc(sourceVoltage, power, groundSrc[0]))

    if circuit.headConnections and circuit.motorConnections:
        warn('Only one motor connector at a time is supported.')
        return None

    circuit.components = [element for element in componentList if not element in discard]
    circuit.componentDict = componentDict(circuit.components)

    return circuit

def connectedTo(connections, targets):
    for c in connections:
        if c.__class__.__name__ == 'Wire' and (c.v1Name in targets or c.v2Name in targets):
            return True
    return False

def hasDuplicate(l):
    for (i, x) in enumerate(l):
        if x in l[i+1:]: return True
    return False

def traceWires(node, dict, done):
    done += [node]
    for c in dict[node]:
        if c.__class__.__name__ == 'Wire':
            if c.v1Name == node and not c.v2Name in done:
                done = addNew(traceWires(c.v2Name, dict, done), done)
            elif not c.v1Name in done:
                done = addNew(traceWires(c.v1Name, dict, done), done)
    return done
        
def addNew(entries, l):
    for e in entries:
        if not e in l:
            l += [e]
    return l

def traceElement(etype, components, dict):
    connected = []
    for element in components:
        name = element.__class__.__name__
        if name == etype:
            addNew(traceWires(element.v1Name, dict, []), connected)
    return connected

class GroundInput:
    def __init__(self, ctype, v1):
        self.type = ctype
        self.v1Name = v1
        self.nodeNames = [v1]

class PowerInput:
    def __init__(self, ctype, v1):
        self.type = ctype
        self.v1Name = v1
        self.nodeNames = [v1]

class Probe:
    def __init__(self, ctype, v1):
        self.type = ctype
        self.v1Name = v1
        self.nodeNames = [v1]

class Pot:
    def __init__(self, v0, v1, v2):
        self.nodeNames = [v0, v1, v2]

class Power:
    def __init__(self, v1):
        self.v1Name = v1
        self.nodeNames = [v1]

class Ground:
    def __init__(self, v1):
        self.v1Name = v1
        self.nodeNames = [v1]

class Connector:
    def __init__(self, ctype, nodeNames):
        self.type = ctype
        self.nodeNames = nodeNames

# An extension to the Feedback combinator that allows a machine on the
# feedback path.
class Feedback (sm.SM):

    def __init__(self, m1, m2, name = None):
        self.m1 = m1
        self.m2 = m2
        self.name = name

    def startState(self):
        return (self.m1.getStartState(), self.m2.getStartState())

    def getNextValues(self, state, inp):
        (s1, s2) = state
        # Will only compute output
        (ignore, o1) = self.m1.getNextValues(s1, 'undefined')
        (ignore, o2) = self.m2.getNextValues(s2, o1)
        assert o2 != 'undefined', 'Error in feedback; machine has no delay'
        # Will only compute next state
        (newS1, o1) = self.m1.getNextValues(s1, o2)
        (newS2, o2) = self.m2.getNextValues(s2, o1)
        return ((newS1, newS2), o1)

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

class Feedback2 (Feedback):
    """
    Like previous C{Feedback}, but takes a machine with two inps and 
    one output at initialization time.  Feeds the output back to the
    second inp.  Result is a machine with a single inp and single
    output.  
    """
    def getNextValues(self, state, inp):
        (s1, s2) = state
        # Will only compute output
        (ignore, o1) = self.m1.getNextValues(s1, (inp, 'undefined'))
        (ignore, o2) = self.m2.getNextValues(s2, o1)
        assert o2 != 'undefined', 'Error in feedback; machine has no delay'
        # Will only compute next state
        (newS1, o1) = self.m1.getNextValues(s1, (inp, o2))
        (newS2, o2) = self.m2.getNextValues(s2, o1)
        return ((newS1, newS2), o1)

######################################################################
##
##  To work in feedback situations we need to propagate 'undefined'
##  through various operations. 

def isDefined(v):
    return not v == 'undefined'
def allDefined(struct):
    if struct == 'undefined':
        return False
    elif isinstance(struct, list) or isinstance(struct, tuple):
        return reduce(operator.and_, [allDefined(x) for x in struct])
    else:
        return True

# Only binary functions for now
def safe(f):
    def safef(a1, a2):
        if allDefined(a1) and allDefined(a2):
            return f(a1, a2)
        else:
            return 'undefined'
    return safef

safeAdd = safe(operator.add)
safeMul = safe(operator.mul)
safeSub = safe(operator.sub)

############
# MOTOR MODEL
############

def signum(x):
    if x < 0: return -1
    elif x > 0: return +1
    else: return 0

#  To use old motor model set this to True
oldMotorModel = False

# Model the effects of friction (disable for comparing with ideal)
modelfriction = True

# opamp outputs can only be in the range [0..sourceVoltage]
clipmotorvoltages = True

# KA334 opamp shouldn't (can't?) supply more than 1 Amp
clipmotorcurrent = True

# To model the effect of Lm we have to include motor current in the state
# Does not make much of a differene...
# NOTE: Don't try and use this with the old motor model...
modelinductance = True 

# Can now freely specify Tsim (simulation interval) and
# Tplot (plotting interval) --- need *not* be integer ratio.

# NOTE: need to change simulation driver files if Tsim is changed
# or, have the driver files use Tsim to figure out the number of samples...
# e.g. nsteps = int(10.0/simulate.Tsim) for a 10 second signal

# Tsim = 0.01 # second - time step --- bkph
Tsim = 0.02 # second - time step --- accurate enough

## Constants for old motor model (now defunct)

# damping factor on velocity in one time step (Tsim = 0.1 sec)
# (that means velocity drops to 11% of starting velocity in one second)
B = 0.8 # value if lacking back EMF implementation in current calculation
# NOTE: B must be changed if time step Tsim is changed...

# Compare time constant of motor under S/C conditions of about 1 second
# this decays to 0.925 of original value in one time step
# Need to adjust B to 0.865 if we implement back EMF in motor
# so the combination of the two comes back to 0.8
Bnew = 0.865 # if back EMF implemented in current calculation
# B = 1 # for testing without frictional damping in old model

mincurrent = 0.03 # amps "static friction current"
minvelocity = 0.1 # amps/(rad/sec) "dynamic friction coefficient"

## Constant for new motor model

KB = 0.48 # volt/(radians/sec) - back EMF constant
KM = 250  # (radians/sec^2)/amp - angular acceleration constant
# Electro-mechanical time constant Rm/(Km*Kb) = 0.037 seconds

Kt = 0.317 # torque constant Newton-meter/amp --- not used

Lm = 0.005 # Henries motor winding inductance (measured)
# Electrical time constant = L/R = 0.001 seconds
# If inductance was an order of magnitude larger it would matter...

istiction = 0.055   # Amp -> current needed to overcome stiction
ifricstatic = 0.022 # Amp -> current to support static friction
ifricslope = 0.0020 # Amp/(rad/sec) -> current to support dynamic friction

# Rm is in ohms - motor winding resistance -
if oldMotorModel:
    Rm = 5.0
    potAngle = 2 * math.pi
else:
#    Rm = 5.5 # original measurements
    Rm = 4.5 # improved measurements
    potAngle = 2 * math.pi * 3 / 4 # total angular range of potentiometer

# The motor is a state machine that takes in the voltages at the
# terminals and which outputs the motor velocity and angular position (and current).

# old dynamic model --- acceleration proportional to current
def oldDynamics(vm0, vm1, state):
    (vel, pos) = state
    current = (vm0 - vm1) / 5 # voltage/5 is input current
    if abs(current) < mincurrent and abs(vel) < minvelocity:
        return (0, pos) # stalled
    else:
        newPos = pos+T*vel
        newVel = B*(vel+KM*current*Tsim)
        if (newPos >= potAngle and newVel >= 0) or (newPos <= 0 and newVel <= 0):
            newPos = util.clip(newPos, 0.0, potAngle)
            newVel = 0
        return (newVel, newPos)

# the new dynamic model
def newDynamics(vm0, vm1, state):
    if modelinductance:
        (vel, pos,curr) = state
    else:
        (vel, pos) = state
    if clipmotorvoltages: # limit outputs from opamp
        vm0 = util.clip(vm0, 0, sourceVoltage)
        vm1 = util.clip(vm1, 0, sourceVoltage)
    voltage = (vm0 - vm1) - vel * KB # subtract back EMF
    if modelinductance:
        newCurr = (voltage + Lm/Tsim*curr) / (Rm+Lm/Tsim)
    else:
        newCurr = voltage / Rm
    if clipmotorcurrent:             # KA344 opamp limitation
        newCurr = util.clip(newCurr,-1.0,+1.0)
    # check whether stationary and current too small
    if modelfriction and vel == 0 and abs(newCurr) < istiction:
        newPos = pos
        newVel = 0 # stalled
    else:  # calculate current needed to support friction
        if modelfriction:
            if vel == 0:
                sgn = signum(newCurr)
            else:
                sgn = signum(vel)
            ifric = sgn * ifricstatic + ifricslope * vel
        else:
            ifric = 0
        newVel = vel + KM * (newCurr - ifric) * Tsim
        if vel * newVel > 0 or vel == newVel: # normal case
            newPos = pos + Tsim * (vel + newVel) / 2
        else: # velocity changes sign
            # at zero velocity now, determine whether stalled...
            if modelfriction and abs(newCurr) < istiction:
                kTsim = vel / (vel - newVel) * Tsim # time of zero crossing
                newPos = pos + kTsim * vel / 2
                newVel = 0 # stalled
            else: # there is enough current to keep going
                newPos = pos + Tsim * (vel + newVel) / 2

    if (newPos >= potAngle and newVel >= 0) or (newPos <= 0 and newVel <= 0):
        # crashed into the pot limits
        newPos = util.clip(newPos, 0.0, potAngle)
        newVel = 0
    if modelinductance:
        return (newVel, newPos, newCurr)
    else:
        return (newVel, newPos)

class MotorAccel(sm.SM):
    def __init__(self, init, motorNodes):
        self.startState = init
        self.motorNodes = motorNodes
    def getNextValues(self, state, inp):
        if not allDefined(inp):
            return (state, 'undefined')
        vm0 = inp.translate(self.motorNodes[0])
        vm1 = inp.translate(self.motorNodes[1])
        if oldMotorModel:
            newState = oldDynamics(vm0, vm1, state)
        else:
            newState = newDynamics(vm0, vm1, state)
        return (newState, newState)

############
# Model the circuit with the world as a composite state machine
############

# The CircuitSM has as input a set of parameters (pot angle, motor
# speed, light intensity) which are specified in a dictionary and it
# outputs a solution for the circuit (which specifies the voltages and
# currents).   One of the initialization parameters is a list of
# functions, each of which takes the machine input (the parameters)
# and returns a list of components (resistors, sources).

class CircuitSM(sm.SM):
    def __init__(self, components, inComponents, groundNode):
        self.components = components    # the permanent circuit components
        self.inComponents = inComponents # list of functions
        self.groundNode = groundNode     # zero potential

    # in these circuits, there is no meaningful state (the world has state)
    def getNextValues(self, state, inp):
        if not allDefined(inp):
            return (state, 'undefined')
        components = self.components[:] # permanent components
        inpDict = reduceToDict(inp)     # combine dictionaries in input
        for f in self.inComponents:
            components.extend(f(inpDict)) # add new components
        sol = circuitSolve(components, self.groundNode)
        print '.',                      # progress indicator
        sys.stdout.flush()
        return (state, sol)

def reduceToDict(inp):
    if isinstance(inp, dict):
        return inp
    elif isinstance(inp, (list, tuple)):
        new = {}
        for d in inp:
            new.update(reduceToDict(d))
        return new
    else:
        raise Exception, '%s is neither a list or dict'%inp

def circuitSolve(components, groundNode):
    ckt = cc.Circuit(components).makeEquationSet(groundNode)
    return ckt.solve()
    try:
        sol = ckt.solve()
    except Exception:
        sol = None
        warn('Failed to solve equations!  Check for short circuit or redundant wire.')
        raise Exception, 'Circuit solver failed'
    return sol

def systemSM(circuit, inComponents, motorNodes, initState):

    # circuit takes input which is a dictionary of values (or list of them)
    # output is a le.Solution instance.
    cSM = CircuitSM(circuit.components, inComponents, circuit.groundNode)
    # motor input is Solution instance, output is (vel, angle)
    motorSM = sm.Cascade(MotorAccel(initState, motorNodes), sm.R(initState))
    # world has Solution as input, ((vel, angle), sol) as output
    wSM = sm.Parallel(motorSM, sm.Wire())

    if inComponents:
        # there's another input besides motor feedback
        return Feedback2(sm.Cascade(cSM,wSM), MotorFeedback())
    else:
        # only motor feedback
        return Feedback(sm.Cascade(cSM,wSM), MotorFeedback())

class MotorFeedback(sm.SM):
    def getNextValues(self, state, inp):
        # inp is (motorOutput, circuitSol)
        if modelinductance:
            (vel, pos,curr) = inp[0]
        else:
            (vel, pos) = inp[0]
        return (state, {'motorAngleVel':vel, 'motorAngle':pos})

def makePot(alpha, nodes, value = 5000):
    alpha = util.clip(alpha, 0.01, 0.99)
    return [cc.Resistor(value*alpha, nodes[0], nodes[1]),
            cc.Resistor(value*(1-alpha), nodes[1], nodes[2])]

def makeMotor(emf, nodes):
    return [cc.Resistor(Rm, nodes[0], 'emf'),
            cc.VSrc(emf, 'emf', nodes[1])]

def motorAngleAlpha(angle):
    return util.clip(angle/potAngle, 0, 1)

def makeVoltage(value, nodes):
    return [cc.VSrc(value, nodes[0], nodes[1])]

def makePhoto(headAngle, lightAngle, lightDist, nodes):
    (iL, iR) = intensityFromAngles(headAngle, lightAngle, lightDist)
    return makePhotoFromIntensity(iL, iR, nodes)

lightTransitionK = 1.0
lightSourceIntensityInLux = 10000

def intensityFromAngles(headAngle, lightAngle, lightDist):
    # lightDist is nominally one, less than one means closer to head.
    intensity = lightSourceIntensityInLux/(lightDist**2)
    left = intensity*0.5*(1+math.tanh(lightTransitionK*(headAngle - lightAngle)))
    right = intensity*0.5*(1+math.tanh(-lightTransitionK*(headAngle - lightAngle)))
    return (left, right)

lightTransitionK1 = 2.0
lightTransitionK2 = 5.0
# lightSourceIntensityInLux1 = 1500
ambientLightInLux = 100

# update from Berthold (spring 2011):
# 60 watt light bulb typically 850 lumens
# diameter about 0.06 m, expanded by reflector to 0.14 m
# --> bulb + reflector equivalent to 4627 lumens
# at 1 meter, this is about 368 lux (not 1500)
lightSourceIntensityInLux1 = 368

def intensityFromAngles(headAngle, lightAngle, lightDist):

    # print 'headAngle', headAngle, 'lightAngle', lightAngle
    
    # lightDist is nominally one, less than one means closer to head.
    intensity = lightSourceIntensityInLux1/(lightDist**2)
    angle = lightAngle - headAngle
    offset = math.pi/10
    shift = 0.3
    left1 = intensity*0.5*(1+math.tanh(lightTransitionK1*(angle+offset)+shift))
    left2 = intensity*0.5*(1+math.tanh(lightTransitionK2*(-angle+offset)-shift))
    right1 = intensity*0.5*(1+math.tanh(-lightTransitionK1*(angle-offset)+shift))
    right2 = intensity*0.5*(1+math.tanh(-lightTransitionK2*(-angle-offset)-shift))
    ## Originally reversed -- so labels here are wrong, right is left and vv.
    return (min(right1+0.3*ambientLightInLux, right2)+ambientLightInLux,
            min(left1+0.3*ambientLightInLux,left2)+ambientLightInLux)

def makePhotoFromIntensity(intensityL, intensityR, nodes):
    # linear in log-log (ohms vs lux)
    # resistance is 5K at 100 lux, slope is -0.9 (per Denny)
    x = 0
    resistors = []
    for i in (intensityL, intensityR):
        if i <= 1:
            lR = 5.5
        else:
            lI = math.log(i, 10)
            lR = 5.5 - lI*0.9
        # print 'intensity', i, 'resistance', 10**lR
        resistors.append(cc.Resistor(10**lR, nodes[x], nodes[x+1]))
        x += 1
    return resistors

def checkConnected(circuit, nodes):
    for node in nodes:
        if not (node in circuit.componentDictFull and \
                len(circuit.componentDictFull[node]) > 1):
            return False
    return True

def getMotorNodes(circuit, warning=False):
    if circuit.motorConnections or circuit.headConnections:
        if circuit.motorConnections:
            p1 = circuit.motorConnections[4]
            p2 = circuit.motorConnections[5]
        else:
            # Originally were switched
            #p1 = circuit.headConnections[7]
            #p2 = circuit.headConnections[6]
            p1 = circuit.headConnections[6]
            p2 = circuit.headConnections[7]
        if checkConnected(circuit, [p1, p2]):
            # there are connections to the motor
            return [p1, p2]
        else:
            if warning: warn('Motor is not connected')
            return []
    else: return []

def getHeadPotNodes(circuit, warning=False):
    if circuit.headConnections:
        headPotNodes = [circuit.headConnections[i] for i in (0, 1, 2)]
        if not checkConnected(circuit, headPotNodes):
            if warning: warn('Head potentiometer is not connected')
            return []
        return headPotNodes
    else: return []

def getHeadPhotoNodes(circuit, warning=False):
    if circuit.headConnections:
        # left eye is pin 4, right eye is pin6, common node is pin 5.
        headPhotoNodes = [circuit.headConnections[i] for i in (3, 4, 5)]
        if not checkConnected(circuit, headPhotoNodes):
            if warning: warn('Head photosensors are not connected')
            return []
        return headPhotoNodes
    else: return []

def getAnalogVoNodes(circuit, warning=False):
    if circuit.robotConnections:
        Vo = circuit.robotConnections[5]
        if Vo in circuit.componentDict:
            # analog input and ground
            return [Vo, circuit.robotConnections[3]]
        else: return []
    else: return []

def getAnalogViNodes(circuit, warning=False):
    if circuit.robotConnections:
        Vi = [(i, circuit.robotConnections[i]) for i in (0, 2, 4, 6)]
        ViConnected = [(i, n) for (i, n) in Vi if n in circuit.componentDict]
        return ViConnected
    else: return []

def getPotNodes(circuit, warning=False):
    if circuit.pots:
        potNodes = circuit.pots[0]
        if not checkConnected(circuit, [potNodes[0], potNodes[2]]):
            if warning: warn('Input potentiometer is not connected')
            return []
        return potNodes
    else: return []

def nodeVals(sol, nodes):
    vals = []
    for node in nodes:
        if node in sol.n2i.names():
            vals.append(sol.translate(node))
        else:
            warn('There is no value in circuit solutions for %s'%node)
            return None
    return vals

def diagnoseCircuit(circuit, sigIn):
    motorN = getMotorNodes(circuit, warning=True)
    headPotN = getHeadPotNodes(circuit, warning=True)
    potN = getPotNodes(circuit, warning=True)
    analogVoN = getAnalogVoNodes(circuit)
    analogViN = getAnalogViNodes(circuit)
    if not sigIn:                       # no input specified
        if headPotN or potN:
            warn('There is no input specified for the pots in this circuit.')
            return False
    else:
        sig0 = sigIn.sample(0)
        if not isinstance(sig0, dict):
            warn('The input signal should return a dictionary.')
            return False
        if motorN and 'pot2' in sig0:
            warn('This test specifcies Pot2, the motor must be disconnected.')
            return False
        if 'pot1' in sig0 and not potN:
            warn('This test specifcies Pot1, you need an input potentiometer.')
            return False
        if 'pot2' in sig0 and not headPotN:
            warn('This test specifcies Pot2, you need to connect the pot in the head connector.')
            return False
        if headPotN and not ('pot2' in sig0 or motorN):
            warn('This test does not specify Pot2, you need to connect the motor.')
            return False
    if not (circuit.probes or motorN or analogViN):
        warn('''There is nothing to observe about this circuit.
Add a probe or a connection to a motor.''')
        return False
    # Otherwise, ok
    return True

######## Plotting 

# The old way: where we directly specified integer subsampling ratio...

# subsample=1 # plot all values
# subsample=4 # plot only every fourth value
# subsample=4.5 # test for non-integer subsampling

# The new way: we can specify an arbitrary subsampling interval instead...

# Tplot = 0.01 # plot all values...
Tplot = 0.04 # subsampling interval for plotting graphs
# Tplot = 0.04357 # test for non-integer subsampling
# Tplot = 0.05 # subsampling interval for plotting graphs

# following changed to use sig.ListSignalSampled(...)
# NOTE: additional similar changes in runCircuit(...) for plotting vel and alpha
# following also changed to support non-integer subsampling intervals

def plotparams(Tsim, Tplot, nlen): # calculate plotting subsampling parameters - bkph
    if Tplot < Tsim:
        warn('Subsampling interval %s less than sampling interval %s'%(Tplot,T))
    subsample = Tplot/Tsim # samples per subsampling interval
    if subsample == int(subsample):
        subsample = int(subsample) # use simple integer ratio method
    if subsample < 1: # sanity check
        subsample = 1
    nplot = int(nlen/subsample) # number of samples in output plot
    if xtruescaleflag: # what value to use on horizontal axis
        naxis = nplot*subsample*Tsim
    else:
        naxis = nplot
    return (subsample, nplot, naxis)

def plotInputs(inValues, parent):
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(inValues))
    for (inp, title) in (('pot1', 'pot1 alpha '),
                         ('pot2', 'pot2 alpha '),
                         ('lightAngle', 'light angle ')):
        if inp in inValues[0]:
            values = [d[inp] for d in inValues]
            if subsample > 1:
                inp = sig.ListSignalSampled(values,subsample)
            else:
                inp = sig.ListSignal(values)
            inp.plot(end = nplot, color = 'blue', parent = parent,
                       newWindow = "Input "+title+str(plotno),
                       xmaxlabel = naxis) # bkph
            plotWindows.append(inp._Signal__w)

def plotAnalogOutputs(inValues, parent):
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(inValues))
    for source in ('analog',):
        if source in inValues[0]:
            if subsample > 1:
                inp = sig.ListSignalSampled([d[source] for d in inValues],subsample)
            else:
                inp = sig.ListSignal([d[source] for d in inValues])
            inp.plot(end = nplot, color = 'blue', parent = parent,
                     newWindow = '%s output voltage '%inp+str(plotno),
                     xmaxlabel = naxis) # bkph
            plotWindows.append(inp._Signal__w)

def plotProbes(probes, sols, parent):
    if not probes:
        return
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(sols))
    vals = [nodeVals(sol, probes) for sol in sols]
    if subsample > 1:
        probe = sig.ListSignalSampled([v[0] - v[1] for v in vals], subsample)
    else:
        probe = sig.ListSignal([v[0] - v[1] for v in vals])
    probe.plot(end = nplot, color = 'green', parent = parent,
        newWindow = 'Probe voltage '+str(plotno),
        xmaxlabel = naxis) # bkph
    plotWindows.append(probe._Signal__w)

def plotAnalogInputs(inputs, sols, parent):
    if not inputs:
        return
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(sols))
    vals = [nodeVals(sol, [n for (i, n) in inputs]) for sol in sols]
    for i, (pin, node) in enumerate(inputs):
        if subsample > 1:
            inp = sig.ListSignalSampled([v[i] for v in vals],subsample)
        else:
            inp = sig.ListSignal([v[i] for v in vals])
        inp.plot(end = nplot, color = 'green', parent = parent,
            newWindow = 'Analog input %s voltage '%(pin+1)+str(plotno),
            xmaxlabel = naxis) # bkph
        plotWindows.append(inp._Signal__w)

###########

def plotMotorVelocity(outValues, parent):
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(outValues))
    if subsample > 1:
        vel = sig.ListSignalSampled([x[0][0] for x in outValues],subsample)
    else:
        vel = sig.ListSignal([x[0][0] for x in outValues])
    vel.plot(end = nplot, color = 'red', parent = parent,
            newWindow = 'Motor rotational velocity '+str(plotno),
            xmaxlabel = naxis) # bkph
    plotWindows.append(vel._Signal__w)

def plotMotorPotAlpha(outValues, parent):
    (subsample, nplot, naxis)=plotparams(Tsim, Tplot, len(outValues))
    if subsample > 1:
        alpha = sig.ListSignalSampled([motorAngleAlpha(x[0][1]) for x in outValues],subsample)
    else:
        alpha = sig.ListSignal([motorAngleAlpha(x[0][1]) for x in outValues])
    alpha.plot(end = nplot, color = 'red', parent = parent,
                   newWindow = 'Motor pot alpha '+str(plotno),
                   xmaxlabel = naxis) # bkph
    plotWindows.append(alpha._Signal__w)

###########

# The input "signal" has a value at each sample which is a dictionary.
# The keys in the dictionary can be:
# 'pot1', 'pot2', 'photo1', 'photo2', 'motorAngle', 'motorAngleVel'

def runCircuit(lines, sigIn, parent = None, nsteps = 50):
    runRealCircuit(readCircuit(lines), sigIn, parent, nsteps)

def runRealCircuit(icircuit, sigIn, parent = None, nsteps = 50):
    global plotno
    sys.stdout.flush() # force out any verification error messages

    if plotno > 1:
        for w in plotWindows: 
            if w: w.destroy()
        plotno = 1

    circuit = verifyCircuit(icircuit)
    if circuit == None:
        warn('There was an error in the circuit.')
        return None
    if not diagnoseCircuit(circuit, sigIn):
        return None
    motorN = getMotorNodes(circuit)
    headPotN = getHeadPotNodes(circuit)
    potN = getPotNodes(circuit)
    headPhotoN = getHeadPhotoNodes(circuit)
    analogVoN = getAnalogVoNodes(circuit)
    analogViN = getAnalogViNodes(circuit)
    sig0 = None
    if sigIn:
        sig0 = sigIn.sample(0)
        nsteps = sigIn.length # don't trust nsteps arg...bkph

    # Collect the input functions for the dynamic components
    inComponents = []
    if motorN:
        motorFn = lambda d: makeMotor(d['motorAngleVel']*KB, motorN)
        inComponents.append(motorFn)
    if headPotN:
        if sig0 and 'pot2' in sig0:
            headPotFn = lambda d: makePot(d['pot2'], headPotN)
        else:
            headPotFn = lambda d: makePot(d['motorAngle']/potAngle, headPotN)
        inComponents.append(headPotFn)
    if headPhotoN:
        headPhototFn = lambda d: makePhoto(d['motorAngle'], d['lightAngle'], d['lightDist'], headPhotoN)
        inComponents.append(headPhototFn)
    if potN:
        potFn = lambda d: makePot(d['pot1'], potN)
        inComponents.append(potFn)
    if analogVoN:
        aFn = lambda d: makeVoltage(d['analog'], analogVoN)
        inComponents.append(aFn)
    inputN = (potN or headPotN or headPhotoN or analogVoN)

    if circuit.probes and not (motorN or inputN):
        sol = circuitSolve(circuit.components, circuit.groundNode)
        vals = nodeVals(sol, circuit.probes)
        warn('The voltage difference across the (+, -) probes is: %s'%(vals[0] - vals[1]))
    elif circuit.probes and not motorN and inputN: # no motor
        m = CircuitSM(circuit.components, inComponents, circuit.groundNode)
        sigOut = ts.TransducedSignal(sigIn, m)
        inps = [sigIn.sample(i) for i in range(nsteps)]
        plotInputs(inps, parent)
        plotAnalogOutputs(inps, parent)
        sols = [sigOut.sample(i) for i in range(nsteps)]
        plotProbes(circuit.probes, sols, parent)
        plotAnalogInputs(analogViN, sols, parent)
    else:
        # Test involves the motor.
        if modelinductance:
            m = systemSM(circuit, inComponents, motorN, (0, potAngle/2, 0))
        else:
            m = systemSM(circuit, inComponents, motorN, (0, potAngle/2))
        sigOut = ts.TransducedSignal(sigIn, m)
        inps = [sigIn.sample(i) for i in range(nsteps)]
        plotInputs(inps, parent)
        plotAnalogOutputs(inps, parent)
        outValues = [sigOut.sample(i) for i in range(nsteps)]
        sols = [x[1] for x in outValues]
        plotProbes(circuit.probes, sols, parent)
        plotAnalogInputs(analogViN, sols, parent)
        # entries are ((vel, angle), sol)
        plotMotorVelocity(outValues, parent)
        plotMotorPotAlpha(outValues, parent)

    plotno = plotno + 1           # increment for next time

    print '\n'                    # newline after sequence of dots
    warn('Done')

def warn (message):
    print message
    sys.stdout.flush() # force out

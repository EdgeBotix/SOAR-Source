import soar.util as util
from soar.util import *

robotRadius = 0.2

def configure_io(namespace):
    global soarwideDiscreteStepLength
    soarwideDiscreteStepLength = None

def setDiscreteStepLength(stepLength=None):
    global soarwideDiscreteStepLength
    soarwideDiscreteStepLength = stepLength

def enableTeleportation(prob, pose):
    app.soar.output.enableTeleportation(prob, pose)

class SensorInput:
    """
    Represents one set of sensor readings from the robot, incluing
    sonars, odometry, and readings from the analogInputs
    """
    def __init__(self, cheat = False):
        """
        @param cheat: If C{True}, then get odometry readings in
        absolute coordinate frame of simulated world.  Otherwise,
        odometry frame is defined by robot's initial pose when powered on
        or simulated world is reset.  Should never be set to C{True} on
        the real robot.
        """
        self.sonars = app.soar.output.storedsonars.get()[:]
        """List of 8 sonar readings, in meters."""
        if cheat == True:
            self.odometry = \
                util.valueListToPose(app.soar.output.abspose.get())
            """Instance of util.Pose, representing robot's pose in the global frame if C{cheat = True} and the odometry frame if C{cheat = False}."""
        else:
            self.odometry = \
                util.valueListToPose(app.soar.output.odpose.get())
        self.analogInputs = app.soar.output.analogInputs.get()
        """List of 4 analog input values."""

    def __str__(self):
        return 'Sonar: ' + util.prettyString(self.sonars) + \
               "; Odo: " + util.prettyString(self.odometry) +\
               "; Analog: " + util.prettyString(self.analogInputs)

referenceVoltage = 5.0
class Action:
    """
    One set of commands to send to the robot
    """
    def __init__(self, fvel = 0.0, rvel = 0.0, 
                 voltage = referenceVoltage):
        """
        @param fvel: signed number indicating forward velocity in m/s
        @param rvel: signed number indicating rotational velocity in
        rad/sec;  positive is left, negative is right
        @param voltage: voltage to send to analog input port of
        control board;  should be between 0 and 10v ??
        @param discreteStepLength: if C{None}, then the robot
        continues driving at the last commanded velocity until a new
        action command is received;  if set to a positive value, the
        robot will drive at the last commanded velocity until
        """
        self.fvel = fvel
        self.rvel = rvel
        self.voltage = voltage
        # ignore the input argument for the actions, and just use the
        # global variable set via the function above
        self.discreteStepLength = soarwideDiscreteStepLength

    def execute(self):
        if self.discreteStepLength:
            app.soar.output.discreteMotorOutput(self.fvel, self.rvel,
                                                self.discreteStepLength)
        else:
            app.soar.output.motorOutput(self.fvel, self.rvel)
        app.soar.output.analogOutput(self.voltage)

    def __str__(self):
        return 'Act: ' + \
               util.prettyString([self.fvel, self.rvel, self.voltage])

def registerUserFunction(type, f):
    app.soar.registerUserFunction(type, f)

def done(donep = True):
    if donep:
        app.soar.stopall()

def sonarMonitor(on=True):
    if on:
        app.soar.openSonarMonitor()
    else:
        app.soar.closeSonarMonitor()
            
def oscilloscope(on=True):
    if on:
        app.soar.openOscillo()
    else:
        app.soar.closeOscillo()
            
def addScopeProbeFunction(name, func):
    app.soar.openOscillo()
    app.soar.addScopeProbeFunction(name, func)

def clearScope():
    app.soar.clearScope()
    
#def beep(beepFreq = 440, beepDuration = 0.5):
#    app.soar.output.cmdSay(beepFreq, beepDuration)

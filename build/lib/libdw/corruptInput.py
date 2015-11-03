"""
State machine to add random noise to sonar and odometry
"""
import util
import sm
import random

class CorruptedSensorInput:
    """
    This class has the same interface as C{io.SensorInput}, so
    instances can be used anywhere we use instances of
    C{io.SensorInput}
    """
    def __init__(self, sonars, odometry):
        self.sonars = sonars
        #CHANGED: 8 to 6 sonar readings
        """List of 6 sonar readings"""
        self.odometry = odometry
        """Instance of C{util.Pose}"""
        self.analogInputs = [0]*8
        """Analog inputs are 0"""

class SensorCorrupter(sm.SM):
    """
    State machine that takes instances of C{io.SensorInput} and adds
    noise to them.  Sonars have additive noise, drawn from a Gaussian
    with 0 mean and C{sonarStDev} standard deviation.  Odometry is
    changed only in the x dimension, with additive noise with 0 mean
    and C{odoStDev} standard deviation.  Output of the state machine
    are instances of C{CorruptedSensorInput}.
    """
    def __init__(self, sonarStDev, odoStDev):
        self.sonarStDev = sonarStDev
        self.odoStDev = odoStDev
        self.startState = None # this is a pure function

    def getNextValues(self, state, inp):
        return (None, CorruptedSensorInput(\
                      [random.gauss(s, self.sonarStDev) for s in inp.sonars],
                       util.Pose(random.gauss(inp.odometry.x, self.odoStDev),
                                 inp.odometry.y, inp.odometry.theta)))

        

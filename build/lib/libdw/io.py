import util

class FakeSensorInput:
    """
    Fake version that takes values at init time
    Represents one set of sensor readings from the robot, incluing
    sonars, odometry, and readings from the analogInputs
    """
    def __init__(self, sonars, odometry, analogInputs = [0.0]*8):
        """
        @param cheat: If C{True}, then get odometry readings in
        absolute coordinate frame of simulated world.  Otherwise,
        odometry frame is defined by robot's initial pose when powered on
        or simulated world is reset.  Should never be set to C{True} on
        the real robot.
        """
        self.sonars = sonars
        #CHANGED: 8 to 6 sonar readings
        """List of 6 sonar readings, in meters."""
        self.odometry = odometry
        self.analogInputs = analogInputs

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
        """
        self.fvel = fvel
        self.rvel = rvel
        self.voltage = voltage

    def execute(self):
        print 'Not connected to soar, change your import io statement.'

    def __str__(self):
        return 'Act: ' + '(fvel = ' + util.prettyString(self.fvel) + \
               ', rvel = ' + util.prettyString(self.rvel) + ')'
    __repr__ = __str__


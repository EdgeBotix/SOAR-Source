"""
Useful constants and utilities for dealing with sonar readings in soar.
"""

import math
import util

#CHANGED: commented out two sonar poses
##sonarPoses = [util.Pose(0.08, 0.134, math.pi/2),
##              util.Pose(0.122, 0.118, 5*math.pi/18),
##              util.Pose(0.156, 0.077, math.pi/6),
##              util.Pose(0.174, 0.0266, math.pi/18),
##              util.Pose(0.174, -0.0266, -math.pi/18),
##              util.Pose(0.156, -0.077, -math.pi/6),
##              util.Pose(0.122, -0.118, -5*math.pi/18),
##              util.Pose(0.08, -0.134, -math.pi/2)]

#onarPoses = [util.Pose(0.073,  0.105,  90*math.pi/180),
#             util.Pose(0.130,  0.078,  41*math.pi/180),
#             util.Pose(0.154,  0.030,  15*math.pi/180),
#             util.Pose(0.154, -0.030, -15*math.pi/180),
#             util.Pose(0.130, -0.078, -41*math.pi/180),
#             util.Pose(0.073, -0.105, -90*math.pi/180)]

#eBot Sonars
sonarPoses = [util.Pose(-0.04,  -0.012,  90*math.pi/180),
             util.Pose(-0.028,  0.012,  45*math.pi/180),
             util.Pose(0,     0.029,   0*math.pi/180),
             util.Pose(0.028,0.012,  -45*math.pi/180),
             util.Pose(0.04, -0.012,  -90*math.pi/180),
             util.Pose(0,    -0.029, 180*math.pi/180)]

"""Positions and orientations of sonar sensors with respect to the
              center of the robot.""" 

sonarMax = 1.5
"""Maximum good sonar reading."""

#TODO: check if returning right value
def getDistanceRight(sonarValues):
    #CHANGED: 8 to 6 sonar readings
    """
    @param sonarValues: list of 6 sonar readings
    @return: the perpendicular distance to a surface on the right of
    the robot, assuming there is a linear surface.
    """
    return getDistanceRightAndAngle(sonarValues)[0]
    
def getDistanceRightAndAngle(sonarValues):
    #CHANGED: 8 to 6 sonar readings
    """
    @param sonarValues: list of 6 sonar readings
    @return: (d, a) where, d is the perpendicular distance to a
    surface on the right of the robot, assuming there is a linear
    surface;  and a is the angle to that surface.

    Change to use C{sonarHit}, or at least point and pose transforms.
    """
    hits = []
    for (spose, d) in zip(sonarPoses, sonarValues):
        if d < sonarMax:
            hits.append((spose.x + d*math.cos(spose.theta),
                         spose.y + d*math.sin(spose.theta)))
        else:
            hits.append(None)
    return distAndAngle(hits[3], hits[4])

def sonarHit(distance, sonarPose, robotPose):
    """
    @param distance: distance along ray that the sonar hit something
    @param sonarPose: C{util.Pose} of the sonar on the robot
    @param robotPose: C{util.Pose} of the robot in the global frame
    @return: C{util.Point} representing position of the sonar hit in the
    global frame.  
    """
    return robotPose.transformPoint(sonarPose.transformPoint(\
                                                     util.Point(distance,0)))


### Should replace this stuff with appropriate calls to the util.Line class

def distAndAngle(h0, h1):
    if h0 and h1:
        (linex, liney, lined) = line(h0, h1)
        return (abs(lined), math.pi/2-math.atan2(liney,linex))
    elif h0:
        (hx, hy) = h0
        return (math.sqrt(hx*hx + hy*hy), None)
    elif h1:
        (hx, hy) = h1
        return (math.sqrt(hx*hx + hy*hy), None)
    else:
        return (sonarMax, None)

def line(h0, h1):
    (h0x, h0y) = h0
    (h1x, h1y) = h1
    dx = h1x - h0x
    dy = h1y - h0y
    mag = math.sqrt(dx*dx + dy*dy)
    nx = dy/mag
    ny = -dx/mag
    d = (nx*h0x + ny*h0y)
    return (nx, ny, d)

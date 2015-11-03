import math
import libdw.util as util
import libdw.sm as sm
import libdw.gfx as gfx
from soar.io import io
import time
import libdw.eBotsonarDist as eBotsonarDist

class MySMClass(sm.SM):
    startState=['SX',0,0,0,False,0]
    def getNextValues(self, state, inp):
        #ebot
        frontsensor=inp.sonars[2]
        rightsensor=inp.sonars[4]
        leftsensor=inp.sonars[0]
        #amingobot
        # frontsensor=(inp.sonars[2]+inp.sonars[3])/2
        # rightsensor=inp.sonars[0]
        # leftsensor=inp.sonars[5]
        fvel=0
        rvel=0
        if state[0]=='SX':
            if inp.sonars[2]>0.3:
                if rightsensor<1.5:
                        k1=30
                        k2=-29.97
                        e1=0.7-eBotsonarDist.getDistanceRight(inp.sonars)
                        e0=state[3]
                        nextstate=['SX',1,state[2],e1,state[4],state[5]]
                        rvel=k1*e1+k2*e0
                        fvel=0.1
                else:
                    fvel=0
                    rvel=0
                print frontsensor,rightsensor,leftsensor,rvel
                state[5] = rvel
                #nextstate=['SX',state[1],state[2],state[3],state[4],state[5]]
            else:
                fvel=0.0
                rvel=0.0
                print "XA,stop"
                nextstate=['XA',state[1],inp.odometry.theta,state[3],state[4],state[5]]
        if state[0]=='XA':
            if state[1]==0:
                if inp.odometry.theta-state[2]<math.pi:
                    rvel=0.5
                    print inp.odometry.theta-state[2]
                    nextstate=['XA',state[1],state[2],state[3],state[4],state[5]]
                else:
                    rvel=0.0
                    print "XA,Uturn done"
                    nextstate=['XA',1,state[2],rightsensor]

            if state[1]==1:
                if frontsensor>0.5:
                    if rightsensor<5:
                        k1=10
                        k2=-9.97
                        e1=1.1-rightsensor
                        e0=state[3]
                        print rvel
                        nextstate=['XA',1,state[2],e1]
                        rvel=k1*e1+k2*e0
                        fvel=0.3
                    else:
                        fvel=0.0
                        print "XA,right,stop",rightsensor
                        nextstate=['XA',2,inp.odometry.theta,state[3],state[4],state[5]]
                else:
                    fvel=0
                    print "XA,stop"
                    nextstate=['XA',3,state[2],state[3],state[4],state[5]]

            if state[1]==2:
                if inp.odometry.theta>0 and inp.odometry.theta<0.1:
                    rvel=0
                    fvel=0
                    nextstate=['XA',1,state[2],state[3],state[4],state[5]]
                else:
                    if (inp.odometry.theta-state[2])*-1<math.pi/2:
                        rvel=-0.3
                        fvel=0.25
                        print "XA,turn right 90 degrees"
                        nextstate=['XA',2,state[2],state[3],state[4],state[5]]
                    else:
                        rvel=0
                        fvel=0
                        print "XA,stop"
                        nextstate=['XA',1,state[2],state[3],state[4],state[5]]
                
            if state[1]==3:
                time.sleep(3)
                print "XA,sleep"
                nextstate=['AX',0,inp.odometry.theta,0,state[4],state[5]]



        if state[0]=='AX':
            if state[1]==0:
                if inp.odometry.theta-state[2]<math.pi:
                    rvel=0.5
                    print "AX,Uturn"
                    nextstate=['AX',state[1],state[2],state[3],state[4],state[5]]
                else:
                    rvel=0.0
                    print "AX,stop"
                    nextstate=['AX',1,state[2],rightsensor]

            if state[1]==1:
                if frontsensor>0.5:
                    if rightsensor<5:
                        k1=10
                        k2=-9.97
                        e1=1.1-rightsensor
                        e0=state[3]
                        print k1*e1+k2*e0
                        nextstate=['AX',1,state[2],e1]
                        rvel=(k1*e1+k2*e0)
                        fvel=0.3
                    else:
                        fvel=0.0
                        print "AX,stop"
                        nextstate=['AX',2,inp.odometry.theta,state[3],state[4],state[5]]
                else:
                    fvel=0
                    print "AX,stop"
                    nextstate=['AX',3,state[2],state[3],state[4],state[5]]

            if state[1]==2:
                if inp.odometry.theta>0 and inp.odometry.theta<0.1:
                    rvel=0
                    fvel=0
                    nextstate=['AX',1,state[2],state[3],state[4],state[5]]
                else:
                    if (inp.odometry.theta-state[2])<math.pi/2:
                        rvel=0.3
                        fvel=0.3
                        print inp.odometry.theta-state[2]
                        nextstate=['AX',2,state[2],state[3],state[4],state[5]]
                    else:
                        rvel=0
                        fvel=0
                        print "AX,stop"
                        nextstate=['AX',1,state[2],state[3],state[4],state[5]]

            if state[1]==3:
                time.sleep(3)
                print "AX,sleep"

                nextstate=['XB',0,inp.odometry.theta,0]    
        return nextstate, io.Action(fvel,rvel)
mySM = MySMClass()
mySM.name = 'brainSM'

######################################################################
###
###          Brain methods
###
######################################################################

def plotSonar(sonarNum):
    robot.gfx.addDynamicPlotFunction(y=('sonar'+str(sonarNum),
                                        lambda: 
                                        io.SensorInput().sonars[sonarNum]))

# this function is called when the brain is (re)loaded
def setup():
    robot.gfx = gfx.RobotGraphics(drawSlimeTrail=False, # slime trails
                                  sonarMonitor=False) # sonar monitor widget
    
    # set robot's behavior
    robot.behavior = mySM

# this function is called when the start button is pushed
def brainStart():
    robot.behavior.start(traceTasks = robot.gfx.tasks())

# this function is called 10 times per second
def step():
    inp = io.SensorInput()
    # print inp.sonars[3]
    robot.behavior.step(inp).execute()
    io.done(robot.behavior.isDone())

# called when the stop button is pushed
def brainStop():
    pass

# called when brain or world is reloaded (before setup)
def shutdown():
    pass

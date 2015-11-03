import math
import libdw.util as util
import libdw.sm as sm
import libdw.gfx as gfx
from soar.io import io
#Experimental
import libdw.eBotsonarDist as sonarDist

class MySMClass(sm.SM):
    #Code by Swee Yee
    def __init__(self):
        #Code to process the list of instructions should go here.
        instList = ['R','S','D','L','X']
        #instList = ['S','S','X','R','R','A','S','R','C','S','L','S','X']
        self.startState = (0,instList,0)
        #Pos[0] for target gap, Pos[1] for dest. list, Pos[2] for prev. gap/state
     
    def getNextValues(self, state, inp):
        #Here are some global variables/settings
        mySpd = 0.2
        targetStop = 0.5
        junctionTrigger = 1.5
        #Variables for turning speed
        rotSpd = math.pi/8           
        linSpd = rotSpd*float(state[0])

        #In order not to refer to the same thing too many times:
        sonarR = inp.sonars[4]                          #Sonar readings
        sonarL = inp.sonars[0]                          #Sonar readings
        sonarF = inp.sonars[2]                          #Sonar readings
        wallR = sonarDist.getDistanceRight(inp.sonars)  #Calculated dist.
        
        #This block of code runs only @ the start, till robot senses right wall
        if state[0]==0 and state[2]==0:
            if sonarR<2.4: #If no wall on right
                print round(sonarR,5), round(sonarL,5), round(wallR,5), "Step 1"
                newState=(0,state[1],(sonarR,sonarL,wallR))
            else:
                newState=state
            return (newState, io.Action(fvel = mySpd, rvel = 0))
        elif state[0]==0:
            print round(sonarR,5), round(sonarL,5), round(wallR,5), "Step 2"
            errorGap = sonarR-(state[2][0]+state[2][1]+sonarR+sonarL)/4.0
            wallGap = (state[2][2]+wallR)/2.0-errorGap
            
            newState = (wallGap,state[1],wallR)
            return (newState, io.Action(fvel = mySpd, rvel = 0))

        #Beyond here the robot has completed initialisation steps
        print "Curr. gap %8.5g, Target gap %.5g" %(wallR,state[0]),

        #State specific actions
        if state[2] in range(91,93):
            LR = (-1)**(state[2]%2)   #91 for right, 92 for left
            newState = (state[0],state[1],state[2],state[3]+1)
            if newState[3]>40:
                newState = (newState[0],state[1],93,1)
                print "Done turning! Go straight no. 1"
                return (newState, io.Action(fvel = mySpd, rvel = 0))
            else:
                print "Turn no. %3.f" %newState[3]
                return (newState, io.Action(fvel = linSpd, rvel = LR*rotSpd))
        elif state[2]==93:
            #After turning at junction go straight first
            newState = (state[0],state[1],93,state[3]+1)
            if newState[3]>5:
                newState = (newState[0],state[1],wallR)
                print "Cleared the corner!"
                return (newState, io.Action(fvel = mySpd, rvel = 0))
            else:
                print "Go straight no. %2.f" %newState[3]
                return (newState, io.Action(fvel = mySpd, rvel = 0))
        elif state[2]==99:
            #Just go straight at junction
            if sonarR>2.4 or sonarL>2.4:
                newState = state
            else:
                newState = (state[0],state[1],wallR)
            print "Heading straight!"
            return (newState, io.Action(fvel = mySpd, rvel = 0))

            
        elif state[2]==80:
            #Arrived at dead end, time to wait
            if state[3]>=150:
                print "Done waiting!"
                newState = (state[0],state[1],81,1)
                return (newState, io.Action(fvel = 0, rvel = rotSpd))
            else:
                newState = (state[0],state[1],80,state[3]+1)
                print "Waiting %4.1f seconds" %(newState[3]/10.0)
                return (newState, io.Action(fvel = 0, rvel = 0))
        elif state[2]==81:
            #Turn after waiting state
            newState = (state[0],state[1],81,state[3]+1)
            if newState[3]>80:
                newState=(newState[0],state[1],wallR)
                print "Done turning!"
                return (newState, io.Action(fvel = mySpd, rvel = 0))
            else:
                print "Right turn no. %3.f" %newState[3]
                return (newState, io.Action(fvel = 0, rvel = rotSpd))
        elif state[2]==88:
            #Completed job, stay at final position
            print "Completed job, now resting."
            newState=state
            return (newState, io.Action(fvel = 0, rvel = 0))
        
        #This section of code is for normal state
        elif sonarF<targetStop:
            #Robot senses wall right in front
            if state[1]==None:
                newState = (state[0],None,80,1)
                print "Start waiting ..."
            else:
                destList = state[1]
                if len(destList)==1:
                    print "Finished all deliveries!"
                    newState = (state[0],state[1],88)
                    return (newState,io.Action(fvel = 0, rvel = 0))
                currPos = destList.pop(0)
                newState = (state[0],destList,80,1)
                if currPos == "X":
                    print "Collecting plates at X!"
                else:
                    print "Exposing plates at %s!" %currPos
                
            #Start waiting
            return (newState, io.Action(fvel = 0.0, rvel = 0))

        elif sonarF<2*targetStop:
            #Robot senses wall in front is near
            newState = state
            newSpd = min(5*(sonarF-targetStop),mySpd)
            if newSpd == mySpd:
                print "Target lock!"
            else:
                print "Slowing down! %.3f left" %sonarF
            return (newState, io.Action(fvel = newSpd, rvel = 0))

        elif sonarL>junctionTrigger or sonarR>junctionTrigger:
            #See a junction. What to do next depends on the instruction list!
            #But for now we determine the direction ourselves
            #91 for right, 92 for left, 99 for straight
            if state[1]==None:
                #Set your default direction here yo!
                nextDir = 99
                newState = (state[0],None,nextDir,1)
            else:
                dirRef = {"R":91,"L":92,"S":99,}
                dirList = state[1]
                nextDir = dirRef[dirList.pop(0)]
                newState = (state[0],dirList,nextDir,1)
            print linSpd, mySpd,
            if newState[2] in range(91,93):
                LR = (-1)**(newState[2]%2)   #91 for right, 92 for left
                print "First turn"
                return (newState, io.Action(fvel = linSpd, rvel = LR*rotSpd))
            else:
                print "Go straight!"
                return (newState, io.Action(fvel = mySpd, rvel = 0))
            
##        #elif inp.sonars[4]>state[0]+1:#If wall disappears:
##        elif sonarL>2.4:#If wall disappears:
##            newState=(state[0],10,1)
##            print "First turn"
##            return (newState, io.Action(fvel = linSpd, rvel = 1*rotSpd))
        else:

            #If nothing else, check for wall spacing and adjust accordingly
            desiredRight = state[0]
            prevRight = state[2]
            currRight = wallR
            newState=(state[0],state[1],currRight)
            k1=100
            k2=-95
            
            rotSpd = k1*(desiredRight-currRight) + k2*(desiredRight-prevRight)

            #Following section of code ensures robot doesn't just spin around
            maxRotSpd = mySpd/currRight
            if abs(rotSpd)<maxRotSpd:
                if abs(rotSpd)<0.10:
                    rotSpd=0
            elif rotSpd > maxRotSpd:
                rotSpd = maxRotSpd
            else:
                rotSpd = -1*maxRotSpd
            if rotSpd == 0:
                print "Just moving along"
            else:
                print "Slight turn %8.5f" %rotSpd
            
            return (newState,io.Action(fvel = mySpd,rvel=rotSpd))

##            Depreciated code kept for reference
##            ratio = inp.sonars[3]/inp.sonars[4]
##            tolerance = 0.02        
##            print ratio,            
##            if inp.sonars[4]>desiredRight + tolerance:
##                command= "RIGHT"
##            elif inp.sonars[4]<desiredRight - tolerance:
##                command= "LEFT"
##            elif ratio > 2**0.5+ tolerance:
##                command= "RIGHT"
##            elif ratio < 2**0.5-tolerance:
##                command= "LEFT"
##            else:
##                print "NOT GAY!!"
##                return (newState, io.Action(fvel = mySpd, rvel = 0))
## 
##            if command == "RIGHT":
##                print "Adjust to the right"
##                return (newState, io.Action(fvel = mySpd, rvel = -1*mySpd))
##            elif command == "LEFT":
##                print "LEANING LEFT"
##                return (newState, io.Action(fvel = mySpd, rvel = 1*mySpd))
                
    
    #Uncomment this function for Checkoff 2, comment for Checkoff 4
    '''def getNextValues(self, state, inp): 
        epilson=0.02 #Tolerance for accuracy
        stopPos=0.5 #Stop position
        noMovements = 7 #No of movements
        currentPos = inp.sonars[2]

        if state[0]==0:
            if currentPos>(epilson+stopPos):
                return (1,1),io.Action(fvel = 0.20)
            elif currentPos<(stopPos-epilson):
                return (-1,1),io.Action(fvel = -0.20)
            else:
                return (0,1),io.Action(fvel = 0.00)
        
        elif state[0]!=0 and state[1]<noMovements:
            multiplier=1-state[1]/float(noMovements)
            if currentPos>(epilson+stopPos):
                if state[0]==1:
                    return (1,state[1]),io.Action(fvel = 0.20*multiplier)
                else:
                    return (1,state[1]+1),io.Action(fvel = 0.20*multiplier)
            elif currentPos<(stopPos-epilson):
                if state[0]==-1:
                    return (-1,state[1]),io.Action(fvel = -0.20*multiplier)
                else:
                    return (-1,state[1]+1),io.Action(fvel = -0.20*multiplier)
            else:
                return (0,state[1]),io.Action(fvel = 0.00)
        else:
            return (0,state[1]),io.Action(fvel = 0.00)
        #return (state, io.Action(fvel = 0.00, rvel = 0.0))'''

    #Uncomment this function for Checkoff 4, comment for Checkoff 2
    '''def getNextValues(self, state, inp):

        #First check for wall in front:
        if state[0]==1:
            rightWallDis=inp.sonars[4]
            if state[2]<state[3] and state[3]<rightWallDis:
                return (2,0),io.Action(fvel = 0.20,rvel=0.0)
            else:
                return (1,state[2],state[3],rightWallDis),io.Action(fvel = 0.00,rvel=1.0)

        elif inp.sonars[2]<0.2:
            #Start turning away from wall
            return (1,1000,999,inp.sonars[4]),io.Action(fvel = 0.00,rvel=1.0)
        
        elif state[0]==2:
            rightWallDis=inp.sonars[4]
            
            #Check for walls on the right:
            if rightWallDis>0.3 and rightWallDis<0.5:
                #Stay at current course
                return (2,0),io.Action(fvel = 0.20,rvel=0.0)
            elif rightWallDis<0.3:
                #Turn left a bit
                return (4,0),io.Action(fvel = 0.10,rvel=1.0)
            else:
                #Turn right a bit
                return (3,0),io.Action(fvel = 0.10,rvel=-1.0)
        elif state[0]==3:
            #See which stage I am in now:
            if state[1]==0:
                #Check sensor 3
                newWallDis=inp.sonars[3]
                if newWallDis<0.5:
                    #Turn back and straighten
                    return (3,1),io.Action(fvel = 0.10,rvel=1.0)
                else:
                    return (3,0),io.Action(fvel = 0.10,rvel=-1.0)
            else:
                #Check sensor 4
                newWallDis=inp.sonars[4]
                if newWallDis>0.5:
                    #Turn back and straighten
                    return (3,1),io.Action(fvel = 0.10,rvel=1.0)
                else:
                    return (2,0),io.Action(fvel = 0.20,rvel=0.0)
                

        elif state[0]==4:
            #Check sensor 3
            newWallDis=inp.sonars[3]
            if newWallDis<0.5:
                #Turn right until no wall
                return (4,0),io.Action(fvel = 0.05,rvel=1.0)
            else:
                return (2,0),io.Action(fvel = 0.20,rvel=0.0)'''



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
    robot.gfx = gfx.RobotGraphics(drawSlimeTrail=True, # slime trails
                                  sonarMonitor=False) # sonar monitor widget
    
    # set robot's behavior
    robot.behavior = mySM

# this function is called when the start button is pushed
def brainStart():
    robot.behavior.start(traceTasks = robot.gfx.tasks())

# this function is called 10 times per second
def step():
    inp = io.SensorInput()
    #print inp.sonars[3]
    #print "%8.2f,%8.2f,%8.2f" %(inp.sonars[2],inp.sonars[3],inp.sonars[4])
    robot.behavior.step(inp).execute()
    io.done(robot.behavior.isDone())

# called when the stop button is pushed
def brainStop():
    pass

# called when brain or world is reloaded (before setup)
def shutdown():
    pass

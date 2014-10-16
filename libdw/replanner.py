"""
State machine classes for planning paths in a grid map.
"""

import sm
import math
import ucSearch
import gridDynamics

class Replanner(sm.SM):
    """
    This replanner state machine has a fixed map, which it constructs
    at initialization time.  Input to the machine is an instance of
    C{io.SensorInput};  output is an instance of C{util.Point},
    representing the desired next subgoal.  The planner should
    guarantee that a straight-line path from the current pose to the
    output pose is collision-free.
    """
    
    def __init__(self, goalPoint, worldPath, gridSquareSize, mapClass):
        """
        @param goalPoint: instance of util.Point, representing the
        desired robot location in odometry coordinates.
        @param worldPath: pathname of a file containing a soar world
        description, which will be used to construct the gridmap for
        planning
        @param gridSquareSize: size of the grid squares in the map to
        be constructed
        @param mapClass: a subclass of C{gridMap.GridMap};  it needs
        to take a path and a grid square size as input in its
        initializer.
        """
        self.worldMap = mapClass(worldPath, gridSquareSize)
        self.dynamicsModel = gridDynamics.GridDynamics(self.worldMap)
        self.goalPoint = goalPoint
        self.startState = None

    def getNextValues(self, state, inp):
        return newPathAndSubgoal(self.worldMap, inp, self.goalPoint,
                                 self.dynamicsModel, state,
                                 timeToReplanStaticMap)

def newPathAndSubgoal(worldMap, sensorInput, goalPoint, dynamicsModel, path,
                      timeToReplan, scale = 1):
    """
    This procedure does the primary work of both replanner classes.
    It tests to see if the current plan is empty or invalid.  If so,
    it calls the planner to make a new plan.  Then, given a plan, if
    the robot has reached the first grid cell in the plan, it removes
    that grid cell from the front of the plan.  Finally, it gets the 
    the center of the current first grid-cell in the plan, in odometry 
    coordinates, and generates that as the subgoal.

    It uses a heuristic in the planning, which is the Cartesian
    distance between the current location of the robot in odometry
    coordinates (determined by finding the center of the grid square)
    and the goal location.

    Whenever a new plan is made, it is drawn into the map.  Whenever a
    subgoal is achieved, it is removed from the path drawn in the map.

    @param worldMap: instance of a subclass of C{gridMap.GridMap}
    @param sensorInput: instance of C{io.SensorInput}, containing current
                      robot pose
    @param goalPoint: instance of C{util.Point}, specifying goal
    @param dynamicsModel: a state machine that specifies the
                      transition dynamics for the robot in the grid map
    @param path: the path (represented as a list of pairs of indices
                      in the map) that the robot is currently
                      following.  Can be C{None} or C{[]}.                      
    @param timeToReplan: a procedure that takes C{path}, the robot's
                      current indices in the grid, the map, and the
                      indices of the goal, and returns C{True} or
                      C{False} indicating whether a new plan needs to
                      be constructed.
    @returns: a tuple C{(path, subgoal)}, where C{path} is a list of
                      pairs of indices indicating a path through the
                      grid, and C{subgoal} is an instance of
                      C{util.Point} indicating the point in odometry
                      coordinates that the robot should drive to.
    """
    currentIndices = worldMap.pointToIndices(sensorInput.odometry.point())
    if isinstance(goalPoint, tuple):
        goalIndices = goalPoint
        goalPoint = worldMap.indicesToPoint(goalIndices)
    else:
        goalIndices = worldMap.pointToIndices(goalPoint)
    if timeToReplan(path, currentIndices, worldMap, goalIndices):
        if path: worldMap.undrawPath(path)
        def h(s):
            return scale * goalPoint.distance(worldMap.indicesToPoint(s))
        plan = ucSearch.smSearch(dynamicsModel,
                                 currentIndices,
                                 lambda s: s == goalIndices,
                                 heuristic = h,
                                 maxNodes = 20000)
        if plan:
            path = [s for (a, s) in plan]
            worldMap.drawPath(path)
            print 'New plan', path
        else:
            worldMap.drawPath([currentIndices, goalIndices])
            worldMap.drawWorld()
            path = None
        
    if not path:
        return (path, sensorInput.odometry)
    else:
        if currentIndices == path[0] and len(path) > 1:
            worldMap.drawSquare(path[0])
            path = path[1:]
            worldMap.drawPath(path)
        return (path, worldMap.indicesToPoint(path[0]))

def timeToReplanStaticMap(plan, currentIndices, worldMap, goalIndices):
    """
    When the map is static, we just test for kidnapping.  Replan if
    the current plan is C{None} or if the robot is not in a grid cell
    that is adjacent to the first one in the plan.
    """
    return plan == None or not adjacent(currentIndices, plan[0])

def adjacent((x1, y1), (x2, y2)):
    return abs(x1 - x2) < 2 and abs(y1 - y2) < 2

class ReplannerWithDynamicMap(sm.SM):
    """
    This replanner state machine has a dynamic map, which is an input
    to the state machine.  Input to the machine is a pair C{(map,
    sensors)}, where C{map} is an instance of a subclass of
    C{gridMap.GridMap} and C{sensors} is an instance of
    C{io.SensorInput};  output is an instance of C{util.Point},
    representing the desired next subgoal.  The planner should
    guarantee that a straight-line path from the current pose to the
    output pose is collision-free in the current map.
    """
    def __init__(self, goalPoint, useCostDynamics = False):
        """
        @param goalPoint: fixed goal that the planner keeps trying to
        reach
        @param useCostDynamics: if C{True}, use
        C{gridDynamics.GridCostDynamicsSM} (which penalizes motion
        through cells according to the likelihood that they are
        occupied), otherwise, use C{gridDynamics.GridDynamics} which
        only allows motion through cells that are marked occupiable,
        and uses step length as a cost.
        """
        
        self.goalPoint = goalPoint
        self.startState = None
        self.useCostDynamics = useCostDynamics

    def getNextValues(self, state, inp):
        (map, sensors) = inp
        if self.useCostDynamics:
            dynamicsModel = gridDynamics.GridCostDynamicsSM(map)
            scale = 10.0 / (1.0 - 0.5)**4
        else:
            scale = 1
            dynamicsModel = gridDynamics.GridDynamics(map)
        goalIndices = map.pointToIndices(self.goalPoint)
        currentIndices = map.pointToIndices(sensors.odometry)
        return newPathAndSubgoal(map, sensors, self.goalPoint,
                                 dynamicsModel, state,
                                 timeToReplanDynamicMap,
                                 scale)

def timeToReplanDynamicMap(plan, currentIndices, map, goalIndices):
    """
    Replan if the current plan is C{None}, if the plan is invalid in
    the map (because it is blocked), or if the plan is empty and we
    are not at the goal (which implies that the last time we tried to
    plan, we failed).
    """
    return plan == None or planInvalidInMap(map, plan) or \
            (plan == [] and not goalIndices == currentIndices) 

def timeToReplanDynamicMapAndGoal(plan, currentIndices, map, goalIndices):
    """
    Replan if the current plan is C{None}, if the plan is invalid in
    the map (because it is blocked), if the plan is empty and we
    are not at the goal (which implies that the last time we tried to
    plan, we failed), or if the end of the plan is not the same as the
    goal indices (which means the goal changed).
    """
    return plan == None or planInvalidInMap(map, plan) or \
            (plan == [] and not goalIndices == currentIndices) or \
            not (plan[-1] == goalIndices)

def planInvalidInMap(map, state):
    """
    Just checks to be sure the first two cells are occupiable.  In low
    noise conditions, it's good to check the whole plan, so failures
    are discovered earlier;  but in high noise, we often have to get
    close to a location before we decide that it is really not safe to
    traverse. 
    """
    end = min(2, len(state))
    for s in state[:end]:
        if not map.robotCanOccupy(s):
            return True
    return False

def timeToReplanDynamicMapWithKidnap(state, currentIndices, map, goalIndices):
    """
    Replan if the current plan is C{None}, if the plan is invalid in
    the map (because it is blocked), or if the robot is not in a grid cell
    that is adjacent to the first one in the plan.
    """
    return state == None or \
           (not state == [] and not adjacent(currentIndices, state[0]) \
            or planInvalidInMap(map, state)) or \
            (state == [] and not goalIndices == currentIndices)

class ReplannerWithDynamicMapAndGoal(sm.SM):
    """
    This replanner state machine has a dynamic map and a dynamic goal,
    both of which are inputs to the state machine.  Input to the
    machine is a structure C{(goal, (map, sensors))}, where C{map} is
    an instance of a subclass of C{gridMap.GridMap}, C{goal} is an
    instance of C{util.Point}, and C{sensors} is
    an instance of C{io.SensorInput}; output is an instance of
    C{util.Point}, representing the desired next subgoal.  The planner
    should guarantee that a straight-line path from the current pose
    to the output pose is collision-free in the current map.
    """
    def __init__(self, useCostDynamics = False):
        """
        @param useCostDynamics: if C{True}, use
        C{gridDynamics.GridCostDynamicsSM} (which penalizes motion
        through cells according to the likelihood that they are
        occupied), otherwise, use C{gridDynamics.GridDynamics} which
        only allows motion through cells that are marked occupiable,
        and uses step length as a cost.
        """
        
        self.startState = None
        self.useCostDynamics = useCostDynamics

    def getNextValues(self, state, inp):
        (goalIndices, (map, sensors)) = inp
        if self.useCostDynamics:
            dynamicsModel = gridDynamics.GridCostDynamicsSM(map)
            scale = 10.0 / (1.0 - 0.5)**4
        else:
            scale = 1
            dynamicsModel = gridDynamics.GridDynamics(map)
        currentIndices = map.pointToIndices(sensors.odometry)
        (path, subgoal) =  newPathAndSubgoal(map, sensors, goalIndices,
                                             dynamicsModel, state,
                                             timeToReplanDynamicMapAndGoal,
                                             scale)
        return (path, (subgoal, path == None))


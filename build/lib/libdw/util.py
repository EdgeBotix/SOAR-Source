"""
A wide variety of utility procedures and classes.
"""

import math

class Pose:
    """
    Represent the x, y, theta pose of an object in 2D space
    """
    x = 0.0
    y = 0.0
    theta = 0.0
    def __init__(self, x, y, theta):
        self.x = x
        """x coordinate"""
        self.y = y
        """y coordinate"""
        self.theta = theta
        """rotation in radians"""

    def point(self):
        """
        Return just the x, y parts represented as a C{util.Point}
        """
        return Point(self.x, self.y)

    def transform(self):
        """
        Return a transformation matrix that corresponds to rotating by theta 
        and then translating by x,y (in the original coordinate frame).
        """
        cosTh = math.cos(self.theta)
        sinTh = math.sin(self.theta)
        return Transform([[cosTh, -sinTh, self.x],
                          [sinTh, cosTh, self.y],
                          [0, 0, 1]])

    def transformPoint(self, point):
        """
        Applies the pose.transform to point and returns new point.
        @param point: an instance of C{util.Point}
        """
        cosTh = math.cos(self.theta)
        sinTh = math.sin(self.theta)
        return Point(self.x + cosTh * point.x - sinTh * point.y,
                     self.y + sinTh * point.x + cosTh * point.y)

    def transformDelta(self, point):
        """
        Does the rotation by theta of the pose but does not add the
        x,y offset. This is useful in transforming the difference(delta)
        between two points.
        @param point: an instance of C{util.Point}
        @returns: a C{util.Point}.
        """
        cosTh = math.cos(self.theta)
        sinTh = math.sin(self.theta)
        return Point(cosTh * point.x - sinTh * point.y,
                     sinTh * point.x + cosTh * point.y)

    def transformPose(self, pose):
        """
        Make self into a transformation matrix and apply it to pose.
        @returns: Af new C{util.pose}.
        """
        return self.transform().applyToPose(pose)

    def isNear(self, pose, distEps, angleEps):
        """
        @returns: True if pose is within distEps and angleEps of self
        """
        return self.point().isNear(pose.point(), distEps) and \
               nearAngle(self.theta, pose.theta, angleEps)

    def diff(self, pose):
        """
        @param pose: an instance of C{util.Pose}
        @returns: a pose that is the difference between self and pose (in
        x, y, and theta)
        """
        return Pose(self.x-pose.x,
                    self.y-pose.y,
                    fixAnglePlusMinusPi(self.theta-pose.theta))

    def distance(self, pose):
        """
        @param pose: an instance of C{util.Pose}
        @returns: the distance between the x,y part of self and the x,y
        part of pose.
        """
        return self.point().distance(pose.point())

    def inverse(self):
        """
        Return a pose corresponding to the transformation matrix that
        is the inverse of the transform associated with this pose.  If this
        pose's transformation maps points from frame X to frame Y, the inverse
        maps points from frame Y to frame X.
        """
        return self.transform().inverse().pose()

    def xytTuple(self):
        """
        @returns: a representation of this pose as a tuple of x, y,
        theta values  
        """
        return (self.x, self.y, self.theta)
    
    def __repr__(self):
        return 'pose:'+ prettyString(self.xytTuple())

def valueListToPose(values):
    """
    @param values: a list or tuple of three values: x, y, theta
    @returns: a corresponding C{util.Pose}
    """
    return apply(Pose, values)

class Point:
    """
    Represent a point with its x, y values
    """
    x = 0.0
    y = 0.0
    def __init__(self, x, y):
        self.x = float(x)
        """x coordinate"""
        self.y = float(y)
        """y coordinate"""

    def near(self, point, distEps):
        """
        @param point: instance of C{util.Point}
        @param distEps: positive real number
        @returns: true if the distance between C{self} and C{util.Point} is less
        than distEps
        """
        return self.distance(point) < distEps

    # This is hear for backward compatibility
    isNear = near

    def distance(self, point):
        """
        @param point: instance of C{util.Point}
        @returns: Euclidean distance between C{self} and C{util.Point}
        """
        return math.sqrt((self.x - point.x)**2 + (self.y - point.y)**2)

    def magnitude(self):
        """
        @returns: Magnitude of this point, interpreted as a vector in
        2-space 
        """
        return math.sqrt(self.x**2 + self.y**2)

    def xyTuple(self):
        """
        @returns: pair of x, y values
        """
        return (self.x, self.y)

    def __repr__(self):
        return 'point:'+ prettyString(self.xyTuple())

    def angleTo(self, p):
        """
        @param p: instance of C{util.Point} or C{util.Pose}
        @returns: angle in radians of vector from self to p
        """
        dx = p.x - self.x
        dy = p.y - self.y
        return math.atan2(dy, dx)

    def add(self, point):
        """
        Vector addition
        """
        return Point(self.x + point.x, self.y + point.y)
    def __add__(self, point):
        return self.add(point)
    def sub(self, point):
        """
        Vector subtraction
        """
        return Point(self.x - point.x, self.y - point.y)
    def __sub__(self, point):
        return self.sub(point)
    def scale(self, s):
        """
        Vector scaling
        """
        return Point(self.x*s, self.y*s)
    def __rmul__(self, s):
        return self.scale(s)
    def dot(self, p):
        """
        Dot product
        """
        return self.x*p.x + self.y*p.y

class Transform:
    """
    Rotation and translation represented as 3 x 3 matrix
    """
    def __init__(self, matrix = None):
        if matrix == None:
            self.matrix = make2DArray(3, 3, 0)
            """matrix representation of transform"""
        else:
            self.matrix = matrix

    def inverse(self):
        """
        Returns transformation matrix that is the inverse of this one
        """
        ((c, ms, x),(s, c2, y), (z1, z2, o)) = self.matrix
        return Transform([[c, s, (-c*x)-(s*y)],
                          [-s, c, (s*x)-(c*y)],
                          [0, 0, 1]])

    def compose(self, trans):
        """
        Returns composition of self and trans
        """
        return Transform(mm(self.matrix, trans.matrix))

    def pose(self):
        """
        Convert to Pose
        """
        theta = math.atan2(self.matrix[1][0], self.matrix[0][0])
        return Pose(self.matrix[0][2], self.matrix[1][2], theta)

    def applyToPoint(self, point):
        """
        Transform a point into a new point.
        """
        # could convert the point to a vector and do multiply instead
        return self.pose().transformPoint(point)

    def applyToPose(self, pose):
        """
        Transform a pose into a new pose.
        """
        return self.compose(pose.transform()).pose()

    def __repr__(self):
        return 'transform:'+ prettyString(self.matrix)

class Line:
    """
    Line in 2D space
    """
    def __init__(self, p1, p2):
        """
        Initialize with two points that are on the line.  Actually
        store a normal and an offset from the origin
        """
        self.theta = p1.angleTo(p2)
        """normal angle"""
        self.nx = -math.sin(self.theta)
        """x component of normal vector"""
        self.ny = math.cos(self.theta)
        """y component of normal vector"""
        self.off = p1.x * self.nx + p1.y * self.ny
        """offset along normal"""

    def pointOnLine(self, p, eps):
        """
        Return true if p is within eps of the line
        """
        dist = abs(p.x*self.nx + p.y*self.ny - self.off)
        return dist < eps

    def __repr__(self):
        return 'line:'+ prettyString((self.nx, self.ny, self.off))

class LineSeg:
    """
    Line segment in 2D space
    """
    def __init__(self, p1, p2):
        """
        Initialize with two points that are on the line.  Store one of
        the points and the vector between them.
        """
        self.p1 = p1
        """One point"""
        self.p2 = p2
        """Other point"""
        self.M = p2 - p1
        """Vector from the stored point to the other point"""

    def closestPoint(self, p):
        """
        Return the point on the line that is closest to point p
        """
        t0 = self.M.dot(p - self.p1) / self.M.dot(self.M)
        if t0 <= 0:
            return self.p1
        elif t0 >= 1:
            return self.p1 + self.M
        else:
            return self.p1 + t0 * self.M

    def distToPoint(self, p):
        """
        Shortest distance between point p and this line
        """
        return p.distance(self.closestPoint(p))

    def intersection(self, other):
        """
        Return a C{Point} where C{self} intersects C{other}.  Returns C{False}
        if there is no intersection.
        @param other: a C{LineSeg}
        """
        def helper(l1, l2):
            (a, b, c, d) = (l1.p1, l1.p2, l2.p1, l2.p2)
            try:
                s = ((b.x-a.x)*(a.y-c.y)+(b.y-a.y)*(c.x-a.x))/\
                    ((b.x-a.x)*(d.y-c.y)-(b.y-a.y)*(d.x-c.x)) 
                t = ((c.x-a.x)+(d.x-c.x)*s)/(b.x-a.x)
                if s <= 1 and s >=0 and t <= 1 and t >= 0:
                    fromt = Point(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t)
                    froms = Point(c.x+(d.x-c.x)*s,c.y+(d.y-c.y)*s)
                    if fromt.near(froms, 0.001):
                        return fromt
                    else:
                        return False 
                else:
                    return False 
            except ZeroDivisionError:
                return False
        first = helper(self, other)
        if first:
            return first
        else:
            return helper(other, self)

    def __repr__(self):
        return 'lineSeg:'+ prettyString((self.p1, self.p2))

#####################

def localToGlobal(pose, point):
    """
    Same as pose.transformPoint(point)
    @param point: instance of C{util.Point}
    """
    return pose.transformPoint(point)

def localPoseToGlobalPose(pose1, pose2):
    """
    Applies the transform from pose1 to pose2
    @param pose1: instance of C{util.Pose}
    @param pose2: instance of C{util.Pose}
    """
    return pose1.transform().applyToPose(pose2)

def inversePose(pose):
    """
    Same as pose.inverse()
    @param pose: instance of C{util.Pose}
    """
    return pose.transform().inverse().pose()

# Given robot's pose in a global frame and a point in the global frame
# return coordinates of point in local frame
def globalToLocal(pose, point):
    """
    Applies inverse of pose to point.
    @param pose: instance of C{util.Pose}
    @param point: instance of C{util.Point}
    """
    return inversePose(pose).transformPoint(point)

def globalPoseToLocalPose(pose1, pose2):
    """
    Applies inverse of pose1 to pose2.
    @param pose1: instance of C{util.Pose}
    @param pose2: instance of C{util.Pose}
    """
    return inversePose(pose1).transform().applyToPose(pose2)

# Given robot's pose in a global frame an a point in the global frame
# return coordinates of point in local frame
def globalDeltaToLocal(pose, deltaPoint):
    """
    Applies inverse of pose to delta using transformDelta.
    @param pose: instance of C{util.Pose}
    @param deltaPoint: instance of C{util.Point}
    """
    return inversePose(pose).transformDelta(deltaPoint)

def sum(items):
    """
    Defined to work on items other than numbers, which is not true for
    the built-in sum.
    """
    if len(items) == 0:
        return 0
    else:
        result = items[0]
        for item in items[1:]:
            result += item
        return result

def within(v1, v2, eps):
    """
    @param v1: number
    @param v2: number
    @param eps: positive number
    @returns: C{True} if C{v1} is with C{eps} of C{v2} 
    """
    return abs(v1 - v2) < eps

def nearAngle(a1, a2, eps):
    """
    @param a1: number representing angle; no restriction on range
    @param a2: number representing angle; no restriction on range
    @param eps: positive number
    @returns: C{True} if C{a1} is within C{eps} of C{a2}.  Don't use
    within for this, because angles wrap around!
    """
    return abs(fixAnglePlusMinusPi(a1-a2)) < eps

def nearlyEqual(x,y):
    """
    Like within, but with the tolerance built in
    """
    return abs(x-y)<.0001

def mm(t1, t2):
    """
    Multiplies 3 x 3 matrices represented as lists of lists
    """
    result = make2DArray(3, 3, 0)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += t1[i][k]*t2[k][j]
    return result

def fixAnglePlusMinusPi(a):
    """
    A is an angle in radians;  return an equivalent angle between plus
    and minus pi
    """
    return ((a+math.pi)%(2*math.pi))-math.pi

def fixAngle02Pi(a):
    """
    @param a: angle in radians
    @returns: return an equivalent angle between 0 and 2 pi
    """
    return a%(2*math.pi)

def reverseCopy(items):
    """
    Return a list that is a reversed copy of items
    """
    itemCopy = items[:]
    itemCopy.reverse()
    return itemCopy


def dotProd(a, b):
    """
    Return the dot product of two lists of numbers
    """
    return sum([ai*bi for (ai,bi) in zip(a,b)])

def argmax(l, f):
    """
    @param l: C{List} of items
    @param f: C{Procedure} that maps an item into a numeric score
    @returns: the element of C{l} that has the highest score
    """
    vals = [f(x) for x in l]
    return l[vals.index(max(vals))]

def argmaxWithVal(l, f):
    """
    @param l: C{List} of items
    @param f: C{Procedure} that maps an item into a numeric score
    @returns: the element of C{l} that has the highest score and the score
    """
    best = l[0]; bestScore = f(best)
    for x in l:
        xScore = f(x)
        if xScore > bestScore:
            best, bestScore = x, xScore
    return (best, bestScore)

def argmaxIndex(l, f = lambda x: x):
    """
    @param l: C{List} of items
    @param f: C{Procedure} that maps an item into a numeric score
    @returns: the index of C{l} that has the highest score
    """
    best = 0; bestScore = f(l[best])
    for i in range(len(l)):
        xScore = f(l[i])
        if xScore > bestScore:
            best, bestScore = i, xScore
    return (best, bestScore)

def argmaxIndices3D(l, f = lambda x: x):
    best = (0,0,0); bestScore = f(l[0][0][0])
    for i in range(len(l)):
        for j in range(len(l[0])):
            for k in range(len(l[0][0])):
                xScore = f(l[i][j][k])
                if xScore > bestScore:
                    best, bestScore = (i, j, k), xScore
    return (best, bestScore)

def randomMultinomial(dist):
    """
    @param dist: List of positive numbers summing to 1 representing a
    multinomial distribution over integers from 0 to C{len(dist)-1}.
    @returns: random draw from that distribution
    """
    r = random.random()
    for i in range(len(dist)):
        r = r - dist[i]
        if r < 0.0:
            return i
    return "weird"

def clip(v, vMin, vMax):
    """
    @param v: number
    @param vMin: number (may be None, if no limit)
    @param vMax: number greater than C{vMin} (may be None, if no limit)
    @returns: If C{vMin <= v <= vMax}, then return C{v}; if C{v <
    vMin} return C{vMin}; else return C{vMax}
    """
    if vMin == None:
        if vMax == None:
            return v
        else:
            return min(v, vMax)
    else:
        if vMax == None:
            return max(v, vMin)
        else:
            return max(min(v, vMax), vMin)

def sign(x):
    """
    Return 1, 0, or -1 depending on the sign of x
    """
    if x > 0.0:
        return 1
    elif x == 0.0:
        return 0
    else:
        return -1

def make2DArray(dim1, dim2, initValue):
    """
    Return a list of lists representing a 2D array with dimensions
    dim1 and dim2, filled with initialValue
    """
    result = []
    for i in range(dim1):
        result = result + [makeVector(dim2, initValue)]
    return result

def make2DArrayFill(dim1, dim2, initFun):
    """
    Return a list of lists representing a 2D array with dimensions
    C{dim1} and C{dim2}, filled by calling C{initFun(ix, iy)} with
    C{ix} ranging from 0 to C{dim1 - 1} and C{iy} ranging from 0 to
    C{dim2-1}. 
    """
    result = []
    for i in range(dim1):
        result = result + [makeVectorFill(dim2, lambda j: initFun(i, j))]
    return result

def make3DArray(dim1, dim2, dim3, initValue):
    """
    Return a list of lists of lists representing a 3D array with dimensions
    dim1, dim2, and dim3 filled with initialValue
    """
    result = []
    for i in range(dim1):
        result = result + [make2DArray(dim2, dim3, initValue)]
    return result

def mapArray3D(array, f):
    """
    Map a function over the whole array.  Side effects the array.  No
    return value.
    """
    for i in range(len(array)):
        for j in range(len(array[0])):
            for k in range(len(array[0][0])):
                array[i][j][k] = f(array[i][j][k])

def makeVector(dim, initValue):
    """
    Return a list of dim copies of initValue
    """
    return [initValue]*dim

def makeVectorFill(dim, initFun):
    """
    Return a list resulting from applying initFun to values from 0 to
    dim-1
    """
    return [initFun(i) for i in range(dim)]

def prettyString(struct):
    """
    Make nicer looking strings for printing, mostly by truncating
    floats
    """
    if type(struct) == list:
        return '[' + ', '.join([prettyString(item) for item in struct]) + ']'
    elif type(struct) == tuple:
        return '(' + ', '.join([prettyString(item) for item in struct]) + ')'
    elif type(struct) == dict:
        return '{' + ', '.join([str(item) + ':' +  prettyString(struct[item]) \
                                             for item in struct]) + '}'
    elif type(struct) == float:
        return "%5.6f" % struct
    else:
        return str(struct)
  
def prettyPrint(struct):
    s = prettyString(struct)
    print s

class SymbolGenerator:
    """
    Generate new symbols guaranteed to be different from one another
    Optionally, supply a prefix for mnemonic purposes
    Call gensym("foo") to get a symbol like 'foo37'
    """
    def __init__(self):
        self.count = 0
    def gensym(self, prefix = 'i'):
        self.count += 1
        return prefix + '_' + str(self.count)
    
gensym = SymbolGenerator().gensym
"""Call this function to get a new symbol"""

def logGaussian(x, mu, sigma):
    """
    Log of the value of the gaussian distribution with mean mu and
    stdev sigma at value x
    """
    return -((x-mu)**2 / (2*sigma**2)) - math.log(sigma*math.sqrt(2*math.pi))

def gaussian(x, mu, sigma):
    """
    Value of the gaussian distribution with mean mu and
    stdev sigma at value x
    """
    return math.exp(-((x-mu)**2 / (2*sigma**2))) /(sigma*math.sqrt(2*math.pi))  

def lineIndices((i0, j0), (i1, j1)):
    """
    Takes two cells in the grid (each described by a pair of integer
    indices), and returns a list of the cells in the grid that are on the
    line segment between the cells.
    """
    assert type(i0) == int, 'Args to lineIndices must be pairs of integers'
    assert type(j0) == int, 'Args to lineIndices must be pairs of integers'
    assert type(i1) == int, 'Args to lineIndices must be pairs of integers'
    assert type(j1) == int, 'Args to lineIndices must be pairs of integers'
    
    ans = [(i0,j0)]
    di = i1 - i0
    dj = j1 - j0
    t = 0.5
    if abs(di) > abs(dj):               # slope < 1
        m = float(dj) / float(di)       # compute slope
        t += j0
        if di < 0: di = -1
        else: di = 1
        m *= di
        while (i0 != i1):
            i0 += di
            t += m
            ans.append((i0, int(t)))
    else:
        if dj != 0:                     # slope >= 1
            m = float(di) / float(dj)   # compute slope
            t += i0
            if dj < 0: dj = -1
            else: dj = 1
            m *= dj
            while j0 != j1:
                j0 += dj
                t += m
                ans.append((int(t), j0))
    return ans

def lineIndicesConservative((i0, j0), (i1, j1)):
    """
    Takes two cells in the grid (each described by a pair of integer
    indices), and returns a list of the cells in the grid that are on the
    line segment between the cells.  This is a conservative version.
    """
    assert type(i0) == int, 'Args to lineIndices must be pairs of integers'
    assert type(j0) == int, 'Args to lineIndices must be pairs of integers'
    assert type(i1) == int, 'Args to lineIndices must be pairs of integers'
    assert type(j1) == int, 'Args to lineIndices must be pairs of integers'
    
    ans = [(i0,j0)]
    di = i1 - i0
    dj = j1 - j0
    t = 0.5
    if abs(di) > abs(dj):               # slope < 1
        m = float(dj) / float(di)       # compute slope
        t += j0
        if di < 0: di = -1
        else: di = 1
        m *= di
        while (i0 != i1):
            i0 += di
            t1 = t + m
            if int(t1) == int(t):
                ans.append((i0, int(t1)))
            else:
                ans.append((i0-di, int(t1)))
                ans.append((i0, int(t)))
                ans.append((i0, int(t1)))
            t = t1
    else:
        if dj != 0:                     # slope >= 1
            m = float(di) / float(dj)   # compute slope
            t += i0
            if dj < 0: dj = -1
            else: dj = 1
            m *= dj
            while j0 != j1:
                j0 += dj
                t1 = t + m
                if int(t1) == int(t):
                    ans.append((int(t1), j0))
                else:
                    ans.append((int(t1), j0-dj))
                    ans.append((int(t), j0))
                    ans.append((int(t1), j0))
                t = t1
    return ans

import sys, os
def findFile(filename):
    """
    Takes a filename and returns a complete path to the first instance of the file found within the subdirectories of the brain directory.
    """
    libdir = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
    braindir = os.path.abspath(libdir+'/..')
    for (root, dirs, files) in os.walk(braindir):
        for f in files:
            if f == filename:
                return root+'/'+f
    print "Couldn't find file: ", filename
    return '.'
# This only works if the brain directory is in sys.path, which isn't 
# true unless we put it there, which is complicated
# def findFile(filename):
#     """
#     Takes a filename and returns the first directory in sys.path that contains
#     the file
#     """
#     for p in sys.path:
#         if os.path.exists(p+'/'+filename):
#             return os.path.abspath(p)+'/'+filename
#     print 'Could not find file: ', filename
#     return filename


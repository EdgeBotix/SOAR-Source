import search
import util
import sm
import ucSearch
reload(ucSearch)

import pdb

######################################################################
###
###  Map domain
###
######################################################################

def mapTest(map, start, goal, searchFn = search.breadthFirstDP):
    actions = range(max([len(map[s]) for s in map]))

    def succFn(s, a):
        if a < len(map[s]):
            return map[s][a]
        else:
            return s

    def goalFn(s):
        return s == goal

    return searchFn(start, goalFn, actions, succFn)

######################################################################
###
###  Map1 in notes
###
######################################################################

map1 = {'S' : ['A', 'B'],
        'A' : ['S', 'C', 'D'],
        'B' : ['S', 'D', 'E'],
        'C' : ['A', 'F'],
        'D' : ['A', 'B', 'F', 'H'],
        'E' : ['B', 'H'], 
        'F' : ['C', 'D', 'G'],
        'H' : ['D', 'E', 'G'],
        'G' : ['F', 'H']}

######################################################################
###
###  Map2 in notes
###
######################################################################

map2 = {'S' : ['A', 'B'],
        'A' : ['S', 'C', 'D'],
        'B' : ['S', 'E', 'F'],
        'C' : ['A', 'D'],
        'D' : ['A', 'C'],
        'E' : ['B'],
        'F' : ['B', 'G'],
        'G' : ['F']}

def mapTestAll(map, start, goal):
    print "BreadthFirst: ", mapTest(map, start, goal, search.breadthFirst)
    print "BreadthFirstDP: ", mapTest(map, start, goal, search.breadthFirstDP)
    print "DepthFirst: ", mapTest(map, start, goal, search.depthFirst)
    print "DepthFirstDP: ", mapTest(map, start, goal, search.depthFirstDP)

######################################################################
###
###  Map with distances
###
######################################################################

def mapDistTest(map, start, goal, searchFn = ucSearch.search,
                h = lambda x: 0):
    actions = range(max([len(map[s]) for s in map]))

    def succFn(s, a):
        if a < len(map[s]):
            return map[s][a]
        else:
            return (s, 100)

    def goalFn(s):
        return s == goal

    return searchFn(start, goalFn, actions, succFn, heuristic = h)

######################################################################
###
###  Map1 in notes
###
######################################################################

map1dist = {'S' : [('A', 2), ('B', 1)],
            'A' : [('S', 2), ('C', 3), ('D', 2)],
            'B' : [('S', 1), ('D', 2), ('E', 3)],
            'C' : [('A', 3), ('F', 1)],
            'D' : [('A', 2), ('B', 2), ('F', 4), ('H', 6)],
            'E' : [('B', 3), ('H', 2)], 
            'F' : [('C', 1), ('D', 4), ('G', 1)],
            'H' : [('D', 6), ('E', 2), ('G', 4)],
            'G' : [('F', 1), ('H', 4)]}

smallMapDist = {'S' : [('A', 2), ('B', 1)],
                'A' : [('S', 2), ('D', 2)],
                'B' : [('S', 1), ('D', 10)]}

######################################################################
###
###  Big distance map
###
######################################################################

bigMap = {'S': [('A', 20.7), ('D', 18.1), ('B', 35)],
          'A': [('S', 20.7), ('C', 14.2), ('D', 35.4)],
          'B': [('S', 35), ('D', 22.4), ('E', 15)],
          'C': [('A', 14.2), ('F', 20), ('I', 15)],
          'D': [('S', 18.1), ('A', 35.4), ('B', 22.4), ('F', 25.5), ('H', 18.1)],
          'E': [('B', 15), ('H', 31.7), ('V', 25.5), ('Y', 35)],
          'F': [('D', 25.5), ('C', 20), ('G', 20.7)],
          'G': [('I', 25.5), ('F', 20.7), ('H', 14.2)],
          'H': [('D', 18.1), ('E', 31.7), ('T', 15.9), ('G', 14.2)],
          'I': [('C', 15), ('G', 25.5), ('L', 25), ('J', 11.2)],
          'J': [('I', 11.2), ('K', 18.1), ('M', 15.9)],
          'K': [('J', 15.9), ('N', 11.2)],
          'L': [('I', 25), ('O', 18.1)],
          'M': [('J', 15.9), ('P', 15.9)],
          'N': [('K', 11.2), ('Q', 22.4)],
          'O': [('L', 18.1), ('W', 18.1), ('U', 27), ('Q', 39.1)],
          'P': [('M', 15.9), ('Q', 14.2)],
          'Q': [('P', 14.2), ('N', 22.4), ('O', 39.1)],
          'R': [('T', 14.2), ('V', 14.2)],
          'T': [('H', 15.9), ('R', 14.2)],
          'U': [('O', 27), ('X', 35.4)],
          'V': [('R', 14.2), ('E', 25.5), ('Y', 11.2)],
          'W': [('O', 18.1), ('Z', 25)],
          'X': [('U', 35.4), ('AA', 10)],
          'Y': [('E', 35), ('V', 11.2), ('Z', 15)],
          'Z': [('Y', 15), ('W', 25), ('AA', 11.2)],
          'AA': [('Z', 11.2), ('X', 10)]}

mapLocs = {'S': (40, 5),
         'A': (20, 10),
         'B': (75, 5),
         'C': (10, 20),
         'D': (55, 15),
         'E': (75, 20),
         'F': (30, 20),
         'G': (35, 40),
         'H': (45, 30),
         'I': (10, 35),
         'J': (5, 45),
         'K': (20, 55),
         'L': (30, 50),
         'M': (10, 60),
         'N': (25, 65),
         'O': (45, 60),
         'P': (5, 75),
         'Q': (15, 85),
         'R': (60, 35),
         'T': (50, 45),
         'U': (35, 85),
         'V': (70, 45),
         'W': (60, 50),
         'X': (70, 90),
         'Y': (75, 55),
         'Z': (75, 70),
         'AA': (70, 80)}

def mapD(s, g):
    (sx, sy) = mapLocs[s]
    (gx, gy) = mapLocs[g]
    return math.sqrt((sx - gx)**2 + (sy - gy)**2)

def bigTest(s, g):
    print mapDistTest(bigMap, s, g)
    print mapDistTest(bigMap, s, g, h = lambda x: mapD(x, g))

######################################################################
###
###  Number test domain, specified as a state machine
###
######################################################################

class NumberTestSM(sm.SM):
    startState = 1
    legalInputs = ['x*2', 'x+1', 'x-1', 'x**2', '-x']
    def __init__(self, goal):
        self.goal = goal
    def nextState(self, state, action):
        if action == 'x*2':
            return state*2
        elif action == 'x+1':
            return state+1
        elif action == 'x-1':
            return state-1
        elif action == 'x**2':
            return state**2
        elif action == '-x':
            return -state
    def getNextValues(self, state, action):
        nextState = self.nextState(state, action)
        return (nextState, nextState)
    def done(self, state):
        return state == self.goal

class NumberTestCostSM(sm.SM):
    startState = 1
    legalInputs = ['x*2', 'x+1', 'x-1', 'x**2', '-x']
    def __init__(self, goal):
        self.goal = goal
    def nextState(self, state, action):
        if action == 'x*2':
            return (state*2, 1)
        elif action == 'x+1':
            return (state+1, 1)
        elif action == 'x-1':
            return (state-1, 1)
        elif action == 'x**2':
            return (state**2, 1)
        elif action == '-x':
            return (-state, 1)
    def getNextValues(self, state, action):
        return self.nextState(state, action)
    def done(self, state):
        return state == self.goal



# Same as numberTest, but only considers states whose absolute value
# is less than some maximum.  
class NumberTestFiniteSM(NumberTestSM):
    def __init__(self, goal, maxVal):
        self.goal = goal
        self.maxVal = maxVal
    def getNextValues(self, state, action):
        nextState = self.nextState(state, action)
        if abs(nextState) < self.maxVal:
            return (nextState, nextState)
        else:
            return (state, state)
    
def searchTestSM(goal):
    print "BreadthFirstDP: ", search.smSearch(NumberTestFiniteSM(goal, goal+1), 1)
    print "BreadthFirst: ", search.smSearch(NumberTestFiniteSM(goal, goal+1), 1, DP=False)
    print "DepthFirstDP: ", search.smSearch(NumberTestFiniteSM(goal, goal+1), 1,
                                            depthFirst=True)
    print "DepthFirst: ", search.smSearch(NumberTestFiniteSM(goal, goal+1), 1,
                                          depthFirst=True, DP=False)

import math

def sign(x):
    if x > 0: return 1
    if x < 0: return -1
    else:
        return 0

# Hairy attempt to be admissible
def NH(s, g):
    if sign(g) != 0 and sign(s) != 0 and sign(g) != sign(s):
        return 1 + NH(abs(s), abs(g))
    if s == g:
        return 0
    if abs(s - g) == 1:
        return 1
    if s == 0:
        return 1 + NH(1, g)
    if abs(s) == 1:
        return 1 + NH(2, g)
    else:
        return math.log(math.log(abs(g), abs(s)), 2)

def HN1(s, g):
    return abs(abs(s) - abs(g))

def HN2(s, g):
    if abs(s) > abs(g) or s == 0 or g == 0:
        return HN1(s, g)
    else: 
        return abs(math.log(abs(g)) - math.log(abs(s)))

def foo(s, g):
    return abs(g - s)

def bar(s, g):
    return math.log(abs(g)+1, abs(s)+2)

def numberCostCompare(s, g, h):
    print numberCostTest(s, g, lambda x: 0)
    print numberCostTest(s, g, lambda x: h(x, g))

def numberCostTest(s, g, h):
    return ucSearch.smSearch(NumberTestCostSM(g), s, heuristic = h)


######################################################################
###
###  8 puzzle
###
######################################################################

class EightPuzzleSM(sm.SM):
    startState = (((2, 8, 3), (1, 6, 4), (7, None, 5)),
                  (2, 1))
    legalInputs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    def __init__(self, goal):
        self.goal = goal
    def nextState(self, state, action):
        (board, (x, y)) = state
        (dx, dy) = action
        newSpaceLoc = (util.clip(x + dx, 0, 2),
                       util.clip(y + dy, 0, 2))
        newBoard = swap(board, (x, y), newSpaceLoc)
        return (newBoard, newSpaceLoc)
    def getNextValues(self, state, action):
        nextState = self.nextState(state, action)
        return (nextState, 1)
    def done(self, state):
        return state == self.goal

def swap(board, (ox, oy), (nx, ny)):
    if (ox, oy) == (nx, ny):
        return board
    else:
        # ugly
        newBoard = [[v for v in row] for row in board]
        moved = board[nx][ny]
        newBoard[nx][ny] = board[ox][oy]
        newBoard[ox][oy] = board[nx][ny]
        return tuple([tuple(row) for row in newBoard])

g1 = (((1, 2, 3), (8, None, 4), (7, 6, 5)), (1, 1))
g2 = (((1, 2, 3), (4, 5, 6), (7, 8, None)), (2, 2))
g3 = (((1, 2, 3), (8, None, 4), (7, 6, 5)), (1, 1))
s2 = (((1, 2, 3), (4, 5, 6), (7, None, 8)), (2, 1))
s1 = (((2, 8, 3), (1, 6, 4), (7, None, 5)), (2, 1))
s3 = (((7, 3, 5), (1, 8, 4), (2, None, 6)), (2, 1))

# s3, g3, h1 very slow; h2 good
# s2, g2, very easy
# s1, g1, easy

def eightTest(s, g, h):
    return ucSearch.smSearch(EightPuzzleSM(g), s, maxNodes = 200000,
                             heuristic = lambda s: h(s, g))

def big8():
    for g in [g1, g2, g3]:
        for s in [s1, s2, s3]:
            for h in [h0, h1, h2]:
                print g, s, h
                print eightTest(s, g, h)

def h0(s, g): return 0

def h1(s, g):
    sb = s[0]
    gb = g[0]
    c = 0
    for i in range(3):
        for j in range(3):
            if sb[i][j] != gb[i][j]:
                c += 1
    return c

def h2(s, g):
    sb = s[0]
    gb = g[0]
    def distInBoards(i):
        (xs, ys) = loc(i, sb)
        (xg, yg) = loc(i, gb)
        return abs(xs - xg) + abs(ys - yg)
    
    def loc(v, b):
        for i in range(3):
            for j in range(3):
                if b[i][j] == v:
                    return (i, j)
        print 'failed to find', v, b
    
    return sum([distInBoards(i) for i in range(1, 9)])















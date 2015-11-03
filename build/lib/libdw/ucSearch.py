"""
Procedures and classes for doing uniform cost search, always with
dynamic programming.  Becomes A* if a heuristic is specified. 
"""

import util

somewhatVerbose = False
"""If C{True}, prints a trace of the search"""
verbose = False
"""If C{True}, prints a verbose trace of the search"""

class SearchNode:
    """A node in a search tree"""
    def __init__(self, action, state, parent, actionCost):
        self.state = state
        self.action = action
        """Action that moves from C{parent} to C{state}"""
        self.parent = parent
        if self.parent:
            self.cost = self.parent.cost + actionCost
            """The cost of the path from the root to C{self.state}"""
        else:
            self.cost = actionCost
        
    def path(self):
        """@returns: list of C{(action, state)} pairs from root to this node"""
        if self.parent == None:
            return [(self.action, self.state)]
        else:
            return self.parent.path() + [(self.action, self.state)]

    def inPath(self, s):
        """@returns: C{True} if state C{s} is in the path from here to
        the root"""
        if s == self.state:
            return True
        elif self.parent == None:
            return False
        else:
            return self.parent.inPath(s)

    def __repr__(self):
        if self.parent == None:
            return str(self.state)
        else:
            return repr(self.parent) + \
                   "-"+str(self.action)+"->"+str(self.state)

    __str__ = __repr__

class PQ:
    """
    Slow implementation of a priority queue that just finds the
    minimum element for each extraction.
    """
    def __init__(self):
        """Create a new empty priority queue."""
        self.data = []
    def push(self, item, cost):
        """Push an item onto the priority queue.
           Assumes items are instances with an attribute C{cost}."""
        self.data.append((cost, item))
    def pop(self):
        """Returns and removes the least cost item.
           Assumes items are instances with an attribute C{cost}."""
        (index, cost) = util.argmaxIndex(self.data, lambda (c, x): -c)
        return self.data.pop(index)[1] # just the data item
    def isEmpty(self):
        """Returns C{True} if the PQ is empty and C{False} otherwise."""
        return len(self.data) == 0
    def __str__(self):
        return 'PQ('+str(self.data)+')'
        

def search(initialState, goalTest, actions, successor,
           heuristic = lambda s: 0, maxNodes = 10000):
    """
    @param initialState: root of the search
    @param goalTest: function from state to Boolean
    @param actions: a list of possible actions
    @param successor: function from state and action to next state and cost
    @param heuristic: function from state to estimated cost to reach a goal;
        defaults to a heuristic of 0, making this uniform cost search
    @param maxNodes: kill the search after it expands this many nodes
    @returns: path from initial state to a goal state as a list of
           (action, state) tuples
    """
    startNode = SearchNode(None, initialState, None, 0)
    if goalTest(initialState):
        return startNode.path()
    agenda = PQ()
    agenda.push(startNode, 0)
    expanded = {}
    count = 1
    while (not agenda.isEmpty()) and maxNodes > count:
        if verbose: print "agenda: ", agenda
        n = agenda.pop()
        if not expanded.has_key(n.state):
            expanded[n.state] = True
            if goalTest(n.state):
                # We're done!
                print count, 'nodes visited;', len(expanded), 'states expanded;', 'solution cost:', n.cost
                return n.path()
            if somewhatVerbose or verbose:
                print "   ", n.cost, ":   expanding: ",  n
            for a in actions:
                (newS, cost) = successor(n.state, a)
                if not expanded.has_key(newS):
                    # We don't know the best path to this state yet
                    count += 1
                    newN = SearchNode(a, newS, n, cost)
                    agenda.push(newN, newN.cost + heuristic(newS))
    print "Search failed after visiting ", count, " states."
    return None

def smSearch(smToSearch, initialState = None, goalTest = None,
               heuristic = lambda x: 0, maxNodes = 10000):
   """
   @param smToSearch: instance of C{sm.SM} defining a search domain;
             C{getNextValues} is used to determine the successor of a
             state given an action; the output field of getNextValues is
             interpreted as a cost.
   @param initialState: initial state for the search;  if not
             provided, will use C{smToSearch.startState}
   @param goalTest: function that takes a state as an argument and
             returns C{True} if it is a goal state, and C{False} otherwise
    @param heuristic: function from state to estimated cost to reach a goal;
        defaults to a heuristic of 0, making this uniform cost search
   @param maxNodes: maximum number of nodes to be searched;  prevents
             runaway searches
   @returns: a list of the form C{[(a0, s0), (a1, s1), (a2, s2), ...]}
    where the a's  are legal actions of c{smToSearch} and s's are
    states of that  machine.  C{s0} is the start state;  the last
    state is a state that satisfies the goal test.  If the
    goal is unreachable (within the search limit), it returns C{None}. 
   """
   if initialState == None:
       initialState = smToSearch.getStartState()
   if goalTest == None:
       goalTest = smToSearch.done
   return search(initialState, goalTest,
                 smToSearch.legalInputs,
                 smToSearch.getNextValues,
                 heuristic = heuristic,
                 maxNodes = maxNodes)

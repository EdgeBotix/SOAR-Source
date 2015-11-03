"""
Describe a circuit in terms of its components; generates equations and
solves them.
"""

import le
reload(le)
import util
#!

class Circuit:
    def __init__(self, components):
        """
        @param components: list of instances of C{Component} that make
           up this circuit
        """
        self.components = components

    def solve(self, gnd):
        """
        @param gnd: Name of the node to set to ground (string)
        @returns: instance of C{le.Solution}, mapping node names to values
        """
        es = le.EquationSet()
        n2c = NodeToCurrents()
        
        # Add constituent constraints, and the node/current
        # information induced by each component.
        for c in self.components:
            es.addEquation(c.getEquation())
            n2c.addCurrents(c.getCurrents())
        
        # Add KCL constraints
        es.addEquations(n2c.getKCLEquations(gnd))

        print 'Solving equations'
        print '*****************'
        for e in es.equations: print e
        print '*****************'

        # Solve
        return es.solve()
#!
    def addComponent(self, component):
        self.components.append(component)

    def voc(self, nPlus, nMinus):
        """
        Find the open-circuit voltage by setting nMinus to ground and
        finding the voltage at nPlus
        """
        return self.solve(nMinus).translate(nPlus)

    def isc(self, nPlus, nMinus):
        """
        Find the short-circuit current:  Add a wire across the
        positive and negative terminals and measure the current there
        """
        w = Wire(nMinus, nPlus)
        return Circuit(self.components + [w]).solve(nMinus).translate(w.current)
    
    def theveninEquivalent(self, nPlus, nMinus):
        vTh = self.voc(nPlus, nMinus)
        isc = self.isc(nPlus, nMinus)
        rTh = -(vTh / isc)
        return (vTh, rTh)

    def __str__(self):
        return 'Circuit: '+util.prettyString(self.components)
#!
class NodeToCurrents:
    """
    Keep track of which currents are flowing in and out of which
    nodes in a circuit.
    """
    def __init__(self):
#!!
        self.d = {}
        """
        Dictionary, mapping a node name to a list of current
        descriptions.  Each current description is a list of a current
        name and a sign (+1 or -1), indicating whether the current is
        flowing into or out of that node.
        """
#!!
    def addCurrent(self, current, node, sign):
#!!
        """
        @param current: name of a current variable (string)
        @param node: name of a node (string)
        @param sign: +1 or -1, indicating whether the current is
        flowing into or out of the node

        Adds the new current, with approrpiate sign to C{node}.  
        Adds an entry for C{node}, if doesn't already exist in the
        dictionary.
        """
        if not self.d.has_key(node):
            self.d[node] = []
        self.d[node].append([current, sign])
#!!
    def addCurrents(self, currents):
#!!
        """
        @param currents: list of tuples C{(currentName, nodeName,
        sign)}, with the same meaning as for C{addCurrent}.
        Add several currents at once.
        """
        for (c, n, s) in currents:
            self.addCurrent(c, n, s)
#!!
    def getKCLEquations(self, gnd):
#!!
        """
        @param gnd: name of a node that will have its voltage assigned
        to 0 (string)
        @returns: a list of equations, one for each node.  For
        the ground node, it just asserts that its voltage is 0.  For
        the other nodes, the equation asserts that the sum of the
        currents going into the node minus the sum of currents going
        out of the node is equal to zero.
        """
        result = []
        for node in self.d.keys():
           if not node == gnd:
               (currents, signs) = apply(zip, self.d[node])
               result.append(le.Equation(signs, currents, 0.0))
        result.append(le.Equation([1], [gnd], 0))
        return result
#!!

class Component:
    """
    Generic superclass.  Every component type has to provide
      - C{getCurrents(self)}: Returns a list of tuples C{(i, node, sign)},
        where C{i} is the name of a current variable, C{node} is the name
        of a node,  and C{sign} is the sign of that current at that node.
      - C{getEquation(self)}: Returns an instance of
        C{le.Equation}, representing the constituent equation for this
        component.  
    """
    
    def getCurrents(self):
        """
        Default method that works for components with two leads,
        assuming they define attributes C{current}, C{n1}, and C{n2}. 
        """
        return [[self.current, self.n1, +1],
                [self.current, self.n2, -1]]

class VSrc(Component):
    def __init__(self, v, n1, n2):
        """
        @param v: voltage in Volts (number);  equal to voltage at C{n1} minus voltage at C{n2} 
        @param n1: name of node at one end of the voltage source (string)
        @param n2: name of node at the other end of the voltage source (string)
        """
        self.current = util.gensym('i_'+n1+'->'+n2)
        """
        Name of the current variable for this component
        """
        self.n1 = n1
        self.n2 = n2
        self.v = v
        
    def getEquation(self):
        return le.Equation([1.0, -1.0],
                           [self.n1, self.n2],
                           self.v)

    def __str__(self):
        return 'VSrc('+str(self.v)+', '+self.n1+', '+self.n2+')'

class ISrc(Component):
    def __init__(self, i, n1, n2):
        """
        @param i: current, in Amperes (number), flowing from C{n1} to C{n2}
        @param n1: name of node at one end of the current source (string)
        @param n2: name of node at the other end of the current source (string)
        """
        self.current = util.gensym('i_'+n1+'->'+n2)
        """
        Name of the current variable for this component
        """
        self.n1 = n1
        self.n2 = n2
        self.i = i
        
    def getEquation(self):
        return le.Equation([1.0],
                           [self.current],
                           self.i)
    def __str__(self):
        return 'ISrc('+str(self.i)+', '+self.n1+', '+self.n2+')'

class Wire(Component):
    """
    Just describes a wire between nodes C{n1} and C{n2}; nodes are
    specified by their names (strings)
    """
    def __init__(self, n1, n2):
        self.current = util.gensym('i_'+n1+'->'+n2)
        """
        Name of the current variable for this component
        """
        self.n1 = n1
        self.n2 = n2

    def getEquation(self):
        return le.Equation([1.0, -1.0],
                           [self.n1, self.n2],
                           0)
    def __str__(self):
        return 'Wire('+self.n1+', '+self.n2+')'

class Resistor(Component):
    def __init__(self, r, n1, n2):
        """
        @param r: resistance in Ohms (number)
        @param n1: name of node at one end of the resistor (string)
        @param n2: name of node at the other end of the resistor (string)
        """
        self.current = util.gensym('i_'+n1+'->'+n2)
        """
        Name of the current variable for this component
        """
        self.n1 = n1
        self.n2 = n2
        self.r = r

    def getEquation(self):
#!!
        return le.Equation([1.0, -1.0, -self.r],
                           [self.n1, self.n2, self.current],
                           0)

    def __str__(self):
        return 'Resistor('+str(self.r)+', '+self.n1+', '+self.n2+')'
#!!
class OpAmp(Component):
#!
    """
    Asserts that  nOut = K(nPlus - nMinus).
    """
#!
    def __init__(self, nPlus, nMinus, nOut, K=10000):
        """
        @param nPlus: name of positive input node (string)
        @param nMinus: name of negative input node (string)
        @param nOut: name of positive output node (string)
        @param K: constant in op-amp model (number)
        """
        self.K = K
        self.nPlus = nPlus
        self.nMinus = nMinus
        self.nOut = nOut
        self.current = util.gensym('i->'+nOut)
        """
        Name of the current variable for this component
        """

    def getCurrents(self):
        return [[self.current, self.nOut, +1]]

    def getEquation(self):
#!!
        return le.Equation([1.0, -self.K, self.K],
                           [self.nOut, self.nPlus, self.nMinus],
                           0.0)
#!!
#!
    def __str__(self):
        return 'OpAmp('+self.nPlus+', '+self.nMinus+', '+self.nOut+')'
#!
#!        
class Thevenin(Component):
    """
    An abstract component consisting of a resistor and a voltage
    source in series.
    """
    def __init__(self, v, r, n1, n2):
        """
        @param v: voltage in Volts (number)
        @param r: resistance in Ohms (number)
        @param n1: name of node at one end of the resistor (string)
        @param n2: name of node at the other end of the resistor (string)
        Makes a component that is, effectively, a resistor and a
        voltage source in series.
        """
        self.current = util.gensym('i_'+n1+'->'+n2)
        """
        Name of the current variable for this component
        """
        self.n1 = n1
        self.n2 = n2
        self.v = v
        self.r = r

    def getEquation(self):
        return le.Equation([1.0, -1.0, -self.r],
                           [self.n1, self.n2, self.current],
                           self.v)

    def __str__(self):
        return 'Resistor('+str(self.r)+', '+self.n1+', '+self.n2+')'
#!

# Remove quotes to test the Resistor components
'''
div = Circuit([
    VSrc(10, '10v', 'gnd'),
    Resistor(1000, '10v', 'vo'),
    Resistor(1000, 'vo', 'gnd'),
    Resistor(10, 'vo', 'gnd')
    ])
print div.solve('gnd')
'''

# Remove quotes to test the Resistor and OpAmp components
'''    
buf = Circuit([
    VSrc(10, '10v', 'gnd'),
    Resistor(1000, '10v', 'vo'),
    Resistor(1000, 'vo', 'gnd'),
    OpAmp('vo', 'v-', 'vb'),
    Wire('vb', 'v-'),
    Resistor(10, 'vb', 'gnd')
    ])
print buf.solve('gnd')
'''

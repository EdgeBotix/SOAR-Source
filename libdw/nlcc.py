import math
from nleNumpy import *

print 'Loading', __name__

class Circuit:
    def __init__(self, components):
        self.components = components
        self.nodeNames = reduce(set.union,
                                ([set(c.nodeNames) for c in components]))
        
    def makeConstraintSet(self, groundNode):
        # Build a dictionary to map node names into Node instances
        self.nodeDict = {}
        for name in self.nodeNames:
            self.nodeDict[name] = CircuitNode()
        ckt = ConstraintSet()
        self.addConstituentConstraints(ckt)
        self.addKCLConstraints(ckt, groundNode)
        ckt.addConstraint(setGround, [groundNode])
        return ckt

    def makeEquationSet(self, groundNode):
        return self.makeConstraintSet(groundNode)

    def addConstituentConstraints(self, constraintSet):
        for c in self.components:
            constraintSet.addConstraint(c.constraintFn(), c.vars)

    def addKCLConstraints(self, constraintSet, groundNode):
        for c in self.components:
            c.addKCLToNodes(self.nodeDict)
        for name in self.nodeDict.keys():
            if name != groundNode:
                c = self.nodeDict[name]
                constraintSet.addConstraint(kcl(c.signs), c.currents)

    def displaySolution(self, groundNode = 'gnd'):
        # default name of the ground node is 'gnd'
        ckt = self.makeConstraintSet(groundNode)
        solution = resolveConstraints(ckt.getConstraintEvaluationFunction())
        ckt.display(solution)
        
## Note that this is already the constraint function, it returns a value *not* a
## function like kcl.
def setGround(x):
    # Enforces a constaint that a variable should be zero.
    return x[0]

def kcl(signs):
    def kclsum(x):
        # Set up a sum of signed currents = 0 equation
        return sum([si*xi for (si,xi) in zip(signs,x)])
    return kclsum

class CircuitNode:
    def __init__(self):
        self.signs = []
        self.currents = []

    def addConnection(self, sign, currentName):
        self.signs.append(sign)
        self.currents.append(currentName)

class Component2Leads:
    def __init__(self, n1, n2):
        self.nodeNames = [n1, n2]
        self.v1Name = n1
        self.v2Name = n2
        self.currentName = gensym('i_' + n1 +'_' + n2 + '_')
        self.vars = [n1, n2, self.currentName]        

    def addKCLToNodes(self, nodeDict):
        node1 = nodeDict[self.nodeNames[0]]
        node2 = nodeDict[self.nodeNames[1]]
        node1.addConnection(-1, self.currentName)
        node2.addConnection(1, self.currentName)

class Resistor(Component2Leads):
    def __init__(self, resistance, n1, n2):
        self.R = resistance
        Component2Leads.__init__(self, n1, n2)
    def constraintFn(self):
        def ohmsLaw(x):
            # assumes a list or tuple x = [vn1, vn2, iR]
            [vn1, vn2, iR] = x
            return vn1 - vn2 - float(self.R)*iR
        return ohmsLaw

class VSrc(Component2Leads):
    def __init__(self, voltage, n1, n2):
        self.Vs = voltage
        Component2Leads.__init__(self, n1, n2)
    def constraintFn(self):
        def source(x):
            # assumes a list or tuple x = [vn1, vn2, iR]
            [vn1, vn2, iR] = x
            return vn1 - vn2 - self.Vs
        return source

class Wire(Component2Leads):
    def __init__(self, n1, n2):
        Component2Leads.__init__(self, n1, n2)
    def constraintFn(self):
        def noVoltageDrop(x):
            # assumes a list or tuple x = [vn1, vn2]
            [vn1, vn2, iR] = x
            return vn1 - vn2
        return noVoltageDrop

class OpAmp():
    # Assumes a 10V power supply
    def __init__(self, n1, n2, n3, K=1000, Vcc = 10, Vss = 0):
        # n1 is V+, n2 is V-, n3 is Vout
        self.K = K
        if (Vcc or Vss) and not(Vcc == -Vss or Vss == 0):
            print 'Error: Vss must be -Vcc or 0'
        self.Vcc = Vcc
        self.Vss = Vss
        self.nodeNames = [n1, n2, n3]
        self.voutName = n3
        self.currentName = gensym('i_' + n3 +'_' + '_')
        self.vars = [n1, n2, n3, self.currentName]        

    def addKCLToNodes(self, nodeDict):
        # The current flows from Vout (n3) to ground
        node3 = nodeDict[self.nodeNames[2]]
        node3.addConnection(-1, self.currentName)

    def constraintFn(self):
        def vcvs(x):
            # assumes a list or tuple x = [vinP, vinM, voutP, iout]
            [vinP, vinM, voutP, iout] = x
            vin = vinP - vinM
            # limit the output to be in the [Vss, Vcc] range
            e = self.K*(vinP - vinM)
            if not (self.Vcc is None or self.Vss is None):
                Vrange = (self.Vcc - self.Vss)
                out = Vrange/math.pi*math.atan(math.pi*e/Vrange)
                if self.Vss == 0:
                    out += self.Vcc/2.0
            else:
                out = e
            # print voutP, out, voutP-out
            return voutP - out
        return vcvs

##  Generate new symbols guaranteed to be different from one another
##  Optionally, supply a prefix for mnemonic purposes
##  Call gensym("foo") to get a symbol like 'foo37'        

class SymbolGenerator:
    def __init__(self):
        self.count = 0
    def gensym(self, prefix = 'i'):
        self.count += 1
        return prefix + str(self.count)
gensym = SymbolGenerator().gensym
    

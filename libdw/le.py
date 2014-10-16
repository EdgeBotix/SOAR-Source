"""
Specify and solve systems of linear equations.
"""

import util
import gauss

class NameToIndex:
    """
    Construct a unique mapping of names to indices.  Every time a new
    name is inserted, it is assigned a new index.  Indices start at 0
    and increment by 1.
    For example::
        >>> n2n = nameToIndex()
        >>> n2n.insert('n1')
        >>> n2n.insert('n2')
        >>> n2n.insert('n1')   # has no effect since it is a duplicate
        >>> n2n.lookup('n1')
        0
        >>> n2n.names()
        ['n1', 'n2']
    """
    def __init__(self):
        self.nextIndex = 0
        """The next index to be allocated."""
        self.namesToNums = {}
        """Dictionary mapping names to their assigned indices"""
        self.namesList = []
        """List of names in order of insertion"""
        
    def insert(self, name):
        """
        If C{name} has been inserted before, do nothing.  Otherwise,
        assign it the next index.
        """
        if not self.namesToNums.has_key(name):
            self.namesToNums[name] = self.nextIndex
            self.namesList.append(name)
            self.nextIndex = self.nextIndex + 1
            
    def lookup(self, name):
        """
        Returns the index associated with C{name}.  Generates an error
        if it C{name} has not previously been inserted.
        """
        return self.namesToNums[name]
    
    def names(self):
        """
        Returns list of names that have been inserted so far, in the
        order they were inserted.
        """
        return self.namesList
        

class Equation:
    """
    Represent a single linear equation as a list of variable names, a
    list of coefficients, and a constant.  Assume the coeff * var
    terms are on the left of the equality and the constant is on the
    right.
    """
    def __init__(self, coeffs, variableNames, constant):
        if len(variableNames) != len(coeffs):
            raise Exception, "Number of coefficients %s and names %s do not match"%(str(coeffs),str(variableNames))
        self.variableNames = variableNames
        """List of variable names"""
        self.coeffs = coeffs
        """List of coefficients in the same order as the variable names"""
        self.constant = constant
        """Constant (right hand side)"""
        
    def __str__(self):
        def equationTerm(coeff, varname):
            # don't print 1.0*n1, just n1
            if coeff == 1: return '+'+varname
            if coeff == -1: return '-'+varname
            elif coeff == 0: return ''
            # use the right sign
            elif coeff > 0: return ' + '+str(coeff)+'*'+varname
            else: return str(coeff)+'*'+varname
        return reduce(lambda a,b:a+b,
                      [equationTerm(coeff,name) \
                       for (coeff,name) \
                       in zip(self.coeffs,self.variableNames)])\
                       +' = '+str(self.constant)
    __repr__ = __str__


class EquationSet:
    """
    Represent a set of linear equations
    """
    def __init__(self):
        self.equations = []
        """List of instances of C{Equation}."""

    def addEquation(self, eqn):
        """
        @param eqn: instance of C{Equation}
        Adds it to the set
        """
        self.equations.append(eqn)

    def addEquations(self, eqns):
        """
        @param eqns: list of instances of C{Equation}
        Adds them to the set
        """
        self.equations += eqns

    def solve(self):
        """
        @returns: an instance of C{Solution}
        """
        # Get a unique assignment of names to indices
        n2i = NameToIndex()
        for eq in self.equations:
            for name in eq.variableNames:
                n2i.insert(name)

        # Be sure we have the same number of variables and equations
        numVars = len(n2i.names())
        numEqs = len(self.equations)
        assert numVars == numEqs, 'Number of variables, '\
               +str(numVars)+' does not match number of equations, '+str(numEqs)

        # Write the coefficients into the A matrix and the constants
        # in the c vector.  Return a vector of values.
        c = util.makeVector(numEqs, 0.0)
        A = util.make2DArray(numEqs, numVars, 0.0)
        for i in range(len(self.equations)):
            equation = self.equations[i]
            for (n, var) in zip(equation.coeffs, equation.variableNames):
                A[i][n2i.lookup(var)] = n
            c[i] = equation.constant
        return Solution(n2i, gauss.gaussSolve(A,c))

    def __str__(self):
        return str([str(e) for e in self.equations])    
    __repr__ = __str__


class Solution:
    """Solution to a set of linear equations"""
    def __init__(self, n2i, values):
        self.n2i = n2i
        """Mapping from variable names to indices, an instance of the NameToIndex class"""
        self.values = values
        """List of values of the variables, in order of their indices"""

    def translate(self, name):
        """
        @returns: the value of variable C{name} in the solution
        """
        return self.values[self.n2i.lookup(name)]

    def __str__(self):
        varlist = self.n2i.names()
        varlist.sort()                  # alphabetical order
        result = ""
        for var in varlist:
            line = var + ' = ' + str(self.translate(var)) + '\n'
            result = result + line
        return result
    
    __repr__ = __str__





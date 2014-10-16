"""
Polynomials, with addition, multiplication, and roots.
"""

import operator
import math

class Polynomial:
    """
    Represent polynomials, and supports addition, subtraction, and
    root finding.
    """
    def __init__(self, coeffs):
        """
        @param coeffs: a list of numbers, starting with highest
        order coefficient.  
        """
        self.coeffs = [fixType(c) for c in coeffs]
        """List of coefficients of the polynomial, highest order first"""
        
        self.order = len(coeffs)-1
        """Order of the polynomial;  one less than the number of coeffs"""

    def coeff(self, i):
        if i < 0 or i > self.order:
            return 0.0
        else:
            return self.coeffs[self.order - i]

    def add(p1, p2):
        """
        @param p1, p2: polynomials
        @return: a new polynomial, which is their sum.
        Does not affect either input.
        """
        def extend(coeffs, length):
            """@return: list of coeffs, extended to length by adding zeros
            to the front."""
            return  [0.0]*(length - len(coeffs)) + coeffs
        resultLength = max(p1.order, p2.order) + 1
        return Polynomial(vectorAdd(extend(p1.coeffs, resultLength),
                                    extend(p2.coeffs, resultLength)))
    def __add__(p1, p2):
        return p1.add(p2)

    def __sub__(p1, p2):
        return p1.add(p2.scalarMult(-1))

    def scalarMult(self, s):
        """
        @param s: a scalar
        @return: a new polynomial with all coefficients of self, multiplied by s
        """
        return Polynomial([c*s for c in self.coeffs])

    def mul(p1, p2):
        """
        @param p1, p2: polynomials
        @return: a new polynomial, which is their product.
        
        Does not affect either input.
        """
        result = Polynomial([])
        for i in range(len(p2.coeffs)):
            result = result + p1.shift(p2.order-i).scalarMult(p2.coeffs[i])
        return result

    def shift(p, a):
        """
        @param a: integer
        @return: a new polynomial, multiplied by x**a.

        Just adds zeros for new low-order coefficients.
        """
        return Polynomial(p.coeffs + [0.0]*a)
    
    def __mul__(p1, p2):
        return p1.mul(p2)

    def __str__( self, var = 'z' ):
        if len(self.coeffs) == 0:
            return '0.0'
        else:
            # The last [3:] gets rid of the initial ' + ' characters.
            return reduce(operator.add,
                          [" + " + prettyTerm(c, self.order - p, var) \
                           for (c,p) in zip(self.coeffs, range(self.order+1)) \
                           if not c == 0.0],
                      "")[3:]
    __repr__ = __str__

    def val(self, x):
        """
        @param x: number
        @return: the value of the polynomial with the variable assigned to x. 
        """
        # This implementation uses Horner's rule
        v = self.coeffs[0]
        for c in self.coeffs[1:]:
            v = x * v + c
        return v

    def __call__(self, x):
        return self.val(x)

    def roots(self):
        """
        @return: list of the roots, found by numpy
        """
        import numpy
        # Make a copy of the numpy array into a list
        return [x for x in numpy.roots(self.coeffs)]


######################################################################
###                 Helper functions
######################################################################

def fixType(n):
    """
    If n is an integer, convert to a float, but leave complex as
    complex.
    """
    if type(n) == int:
        return float(n)
    else:
        return n

def assertSameLength(a,b):
    """
    Generate an error if the arguments do not have the same length
    """
    assert len(a) == len(b), \
           "Error: lists must have same length" + str(a) + str(b)

def vectorAdd(a, b):
    """
    @param a, b: lists of numbers of the same length
    @return: (a[1]+b[1], ..., a[n]+b[n])
    """
    assertSameLength(a,b)
    return [ai+bi for (ai,bi) in zip(a,b)]
        
def prettyTerm(coefficient, power, var="z"):
    if power == 0:
        return prettyNum(coefficient)
    elif power == 1:
        return prettyNum(coefficient) + " " + var 
    else:
        return prettyNum(coefficient) + " " + var + "**" + prettyNum(power)

def prettyNum(value):
    if isinstance(value, float):
        return "%.3f" % value
    else:
        return str(value)

    


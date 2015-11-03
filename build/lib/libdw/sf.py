"""
Class and some supporting functions for representing and manipulating system functions. 
"""

import math
import poly
reload(poly)
import util
reload(util)
import ltism
reload(ltism)

class SystemFunction:
    """
    Represent a system function as a ratio of polynomials in R
    """
#!
    def __init__(self, numeratorPoly, denominatorPoly):
        """
        @param numeratorPoly: C{Polynomial}
        @param denominatorPoly: C{Polynomial}
        """
        self.numerator = numeratorPoly
        """Polynomial in R representing the numerator"""
        self.denominator = denominatorPoly
        """Polynomial in R representing the denominator"""

    def poles(self):
        """
        @returns: a list of the poles of the system
        """
        # The poles of a system are the roots of the denominator
        # polynomial in z, which is 1/R.  To get that polynomial,
        # reverse the coefficients of our polynomial (which is in R).

        # make polynomials of z
        num = util.reverseCopy(self.numerator.coeffs)
        den = util.reverseCopy(self.denominator.coeffs)
        # kill off zero-valued leading coeffs (although they don't
        # seem to bother numpy)
        while len(num) > 1 and num[0] == 0:
            num = num[1:]
        while len(den) > 1 and den[0] == 0:
            den = den[1:]
        # cancel poles at zero with zeros at zero
        while len(num) > 0 and len(den) > 0 and num[-1]==den[-1]==0:
            num = num[:-1]
            den = den[:-1]
        return poly.Polynomial(den).roots()

    def poleMagnitudes(self):
        """
        @returns: a list of the magnitudes of the poles of the system
        """
        return [abs(r) for r in self.poles()]

    def dominantPole(self):
        """
        @returns: the pole with the largest magnitude
        """
        return util.argmax(self.poles(), abs)

    def differenceEquation(self):
        """
        @returns: a C{DifferenceEquation} representation of this same system
        """
        # Orders of the output and input parts
        k = self.denominator.order
        j = self.numerator.order

        # Generate an error if the coefficient of y[n] is 0
        a0 = float(self.denominator.coeffs[-1])
        assert not a0 == 0, "Coefficient of y[n] must be non-zero"

        # Now derive coefficient lists c and d of this form
        # y[n] = c_0 y[n-1] + c_{k-1} y[n-k] +
        #        d_0 x[n] + d_1 x[n-1] + ... + d_j x[n-j]
        # Coefficients for newest state and input are at the front;
        # these are the least delayed, so we have to reverse the
        # coeffs in the polynomials
        cCoeffs = [-a/a0 for a in \
                        util.reverseCopy(self.denominator.coeffs[:-1])]
        dCoeffs = [b/a0 for b in \
                        util.reverseCopy(self.numerator.coeffs)]

        return DifferenceEquation(dCoeffs, cCoeffs)

    def __add__(self, other):
        return Sum(self, other)
#!

    def __str__(self):
        return 'SF(' + self.numerator.__str__('R') + \
               '/' + self.denominator.__str__('R') + ')'

    __repr__ = __str__

#!
######################################################################
# A symmetric syntax for combining SystemFunctions
######################################################################
#!
def Cascade(sf1, sf2):
#!    pass
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the cascade of C{sf1} and C{sf2}
    """
    return SystemFunction(sf1.numerator * sf2.numerator,
                          sf1.denominator * sf2.denominator)
#!
#!
def FeedforwardAdd(sf1, sf2):
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the sum of C{sf1} and
    C{sf2}; this models the situation when the two component systems
    have the same input and the output of the whole system is the sum
    of the outputs of the components.
    """
    return SystemFunction(sf1.numerator*sf2.denominator + \
                          sf2.numerator*sf1.denominator,
                          sf1.denominator * sf2.denominator)
def FeedforwardSubtract(sf1, sf2):
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the difference of C{sf1} and
    C{sf2}; this models the situation when the two component systems
    have the same input and the output of the whole system is the
    output of the first component minus the output of the second component.
    """
    return SystemFunction(sf1.numerator*sf2.denominator - \
                          sf2.numerator*sf1.denominator,
                          sf1.denominator * sf2.denominator)
    
# sf maps (X - Y) into Y
# return the sf for a machine that maps X into Y
# Use Black's formula.  SF_new = sf / (1 + sf)
# (n/d) / (1 + (n/d)) = (n/d) / ((d+n)/d) = n / (d+n)
# def feedbackSF(self):
#    return SystemFunction(self.numerator, self.denominator + self.numerator)

# More general version, with sf1 taking the input and sf2 on the
# feedback path
# Y = H1 E
# E = X - W
# W = H2 Y
### so
# E = X - H2 Y
# Y = H1 (X - H2 Y)
# Y + H1 H2 Y = H1 X
# Y (1 + H1 H2) = H1 X
# Y = X H1 / (1 + H1 H2)
# Now, in terms of numerator and denominator
# (n1 / d1) ((d1 d2 + n1 n2) / (d1 d2))
# n1 d1 d2 / d1 (d1 d2 + n1 n2)
# n1 d2 / (d1 d2 + n1 n2)
#!
def FeedbackSubtract(sf1, sf2=None):
#!    pass
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the result of feeding the
    output of C{sf1} back, with (optionally)
    C{sf2} on the feedback path, subtracting it from the input, and
    feeding the resulting signal into C{sf1}.  This situation can be
    characterized with Black's formula. 
    """
    if sf2 == None:
        sf2 = SystemFunction(poly.Polynomial([1]),
                             poly.Polynomial([1]))
    (n1, d1) = (sf1.numerator, sf1.denominator)
    (n2, d2) = (sf2.numerator, sf2.denominator)
    return SystemFunction(n1 * d2, d1 * d2 + n1 * n2)
#!
#!
def FeedbackAdd(sf1, sf2=None):
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the result of feeding the
    output of C{sf1} back, with (optionally)
    C{sf2} on the feedback path, adding it to the input, and
    feeding the resulting signal into C{sf1}.
    """
    if sf2 == None:
        sf2 = SystemFunction(poly.Polynomial([1]),
                             poly.Polynomial([1]))
    (n1, d1) = (sf1.numerator, sf1.denominator)
    (n2, d2) = (sf2.numerator, sf2.denominator)
    return SystemFunction(n1 * d2, d1 * d2 - n1 * n2)

def Sum(sf1, sf2):
    """
    @param sf1: C{SystemFunction}
    @param sf2: C{SystemFunction}
    @returns: C{SystemFunction} representing the system that sums the outputs of the two systems
    """
    (n1, d1) = (sf1.numerator, sf1.denominator)
    (n2, d2) = (sf2.numerator, sf2.denominator)
    return SystemFunction(n1 * d2 + n2 * d1, d1 * d2)

######################################################################
##    Primitive SF's
######################################################################

def Gain(k):
    """
    @param k: gain parameter
    @returns: C{SystemFunction} representing a system that multiplies
    the input signal by C{k}.
    """
    return SystemFunction(poly.Polynomial([k]),poly.Polynomial([1]))

def R():
    """
    @returns: C{SystemFunction} representing a system that delays
    the input signal by one step.
    """
    return SystemFunction(poly.Polynomial([1, 0]),poly.Polynomial([1]))

######################################################################
##    Difference Equations
######################################################################

class DifferenceEquation:
    """
    Represent a difference equation in a form that makes it easy to
    simulate.
    """
    def __init__(self, dCoeffs, cCoeffs):
        """
        Expects coefficients in the form
        M{y[n] = c_0 y[n-1] + c_(k-1) y[n-k] + d_0 x[n] + d_1 x[n-1] + ... + d_j x[n-j]}
        Coefficients for newest state and input are at the front
        """
        self.cCoeffs = cCoeffs
        """Output coefficients"""
        self.dCoeffs = dCoeffs
        """Input coefficients"""

    def systemFunction(self):
        """
        @returns: A C{SystemFunction} equivalent to this difference
        equation
        """
        return SystemFunction(
                poly.Polynomial(util.reverseCopy(self.dCoeffs)),
                poly.Polynomial([-c for c in util.reverseCopy(self.cCoeffs)] \
                                + [1]))

    def stateMachine(self, previousInputs = None, previousOutputs = None):
        """
        @param previousInputs: list of historical inputs running from
        M{x[-1]} (at the beginning of the list) to M{x[-j]} at the end of
        the list, where M{j} is C{len(self.dCoeffs)-1}.  Defaults to
        the appropriate number of zeros.
        @param previousOutputs: list of historical outputs running
        from M{y[-1]} (at the beginning of the list) to M{y[-k]} (at the end
        of the list), where M{k} is C{len(self.cCoeffs)}.  Defaults to
        the appropriate number of zeros.
        @returns: A state machine that uses this difference equation
        to transduce the sequence of
        inputs X to the sequences of outputs Y, starting from a state
        determined by C{previousInputs} and C{previousOutputs}
        """
        return ltism.LTISM(self.dCoeffs, self.cCoeffs,
                           previousInputs, previousOutputs)

    def __str__(self):
        result = 'DE: y[n] = '
        for i in range(len(self.cCoeffs)):
            result += util.prettyString(self.cCoeffs[i])+'y[n-'+str(i+1)+'] + '
        for i in range(len(self.dCoeffs)):
            if i == 0:
                result += util.prettyString(self.dCoeffs[i])+'x[n] + '
            else:
                result +=util.prettyString(self.dCoeffs[i])+'x[n-'+str(i)+'] + '
        return result[:-2]
    __repr__ = __str__

######################################################################
##   Utilities
######################################################################

def periodOfPole(p):
    """
    @param p: int, float, or complex number
    @returns: period = 2 pi / phase of pole  or None (if phase is 0)
    """
    (r, phase) = complexPolar(p)
    if phase == 0:
        print "Pole", p, "does not generate periodic behavior."
        return None    
    else:
        return 2*math.pi / phase

def complexPolar(p):
    """
    @param p: int, float, or complex number
    @returns: polar representation as a pair of r, theta
    """
    if isinstance(p, complex):
        return (abs(p), math.atan2(p.imag, p.real))
    elif p >= 0:
        return (p, 0.0)
    else:
        return (abs(p), math.pi)

#!

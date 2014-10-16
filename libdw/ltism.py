"""
State machines that are representable as LTI systems.
"""

import poly
reload(poly)

import sm
reload(sm)

import util
reload(util)

class LTISM (sm.SM):
    """
    Class of state machines describable as LTI systems
    """
    
    def __init__(self, dCoeffs, cCoeffs,
                 previousInputs = None, previousOutputs = None):
        """
        Expects coefficients in the form
        M{y[n] = c_0 y[n-1] + c_(k-1) y[n-k] + d_0 x[n] + d_1 x[n-1] + ... + d_j x[n-j]}
        Coefficients for newest state and input are at the front

        @param previousInputs: list of historical inputs running from
        M{x[-1]} (at the beginning of the list) to M{x[-j]} at the end of
        the list, where M{j} is C{len(self.dCoeffs)-1}.  If omitted,
        will default to a list of the appropriate number of zeroes,
        corresponding to the system being 'at rest'.
        @param previousOutputs: list of historical outputs running
        from M{y[-1]} (at the beginning of the list) to M{y[-k]} (at the end
        of the list), where M{k} is C{len(self.cCoeffs)}.  If omitted,
        will default to a list of the appropriate number of zeroes,
        corresponding to the system being 'at rest'.
        @returns: A state machine that uses this difference equation
        to transduce the sequence of
        inputs X to the sequences of outputs Y, starting from a state
        determined by C{previousInputs} and C{previousOutputs}
        """

        j = len(dCoeffs) - 1
        k = len(cCoeffs)

        if previousInputs == None:
            previousInputs = [0.0]*j
        if previousOutputs == None:
            previousOutputs = [0.0]*k

        # Generate error if wrong number of initial values
        assert (j == -1 or len(previousInputs) == j), \
               "Wrong number of initial inputs. Expected " + \
               str(j) + ", got " + str(len(previousInputs))
        assert len(previousOutputs) == k, \
               "Wrong number of initial outputs. Expected " + \
                  str(k) + ", got " + str(len(previousOutputs))
        
        self.cCoeffs = cCoeffs
        """Output coefficients"""
        self.dCoeffs = dCoeffs
        """Input coefficients"""
        self.startState = (previousInputs, previousOutputs)
        """State is last j input values and last k output values"""

    def getNextValues(self, state, input):
        (inputs, outputs) = state

        # Push the new input onto the front of the inputs
        if not input == None and not self.dCoeffs == []:
            inputs = [input] + inputs

        currentOutput = util.dotProd(outputs, self.cCoeffs) + \
                        util.dotProd(inputs, self.dCoeffs)

        # Remember the most recent output
        # Forget the oldest input and the oldest output
        return ((inputs[:-1], ([currentOutput] + outputs)[:-1]),
                currentOutput)



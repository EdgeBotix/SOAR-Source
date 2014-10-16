"""
A class of signals that is created by putting another signal through a transducer (state machine).
"""

import sig
reload(sig)

class TransducedSignalSlow(sig.Signal):
    """
    Given a state a signal s and a state machine m, generate a new signal
    that has value 0 for any k < 0, and otherwise has the output of
    m, with s as its input, as its value
    """
    def __init__(self, s, m):
        self.s = s
        self.m = m

    def sample(self, k):
        """
        Generate sample k of this signal.  Wildly inefficient.
        """
        if k < 0:
            return 0
        else:
            self.m.start()
            for i in range(k+1):
                o = self.m.step(self.s.sample(i))
            return o

######################################################################
# With a cache

class TransducedSignal(sig.Signal):
    """
    Given a signal s, and a state machine m, generate a new signal
    that has value 0 for any k < 0, and otherwise has the output of
    m, with s as its input, as its value
    """
    def __init__(self, s, m):
        self.s = s
        self.m = m
        self.outputCache = {}
        self.lastCalculatedState = None
        self.maxCalcValueSoFar = -1

    def sample(self, k):
        if k < 0:
            return 0
        elif k <= self.maxCalcValueSoFar:
            return self.outputCache[k]
        else:
            if self.lastCalculatedState == None:
                self.m.state = self.m.getStartState()
            else:
                self.m.state = self.lastCalculatedState
            for i in range(self.maxCalcValueSoFar+1, k+1):
                o = self.m.step(self.s.sample(i))
                self.outputCache[i] = o
            self.lastCalculatedState = self.m.state
            self.maxCalcValueSoFar = k
            return o        

# ts1c = TransducedSignalC(sig.us, ltismTest.withInterest)
# ts2c = TransducedSignalC(sig.us, ltismTest.withFee)
# ts3c = TransducedSignalC(sig.us, ltismTest.delay)

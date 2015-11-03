"""State estimator that calls procedures for visualization or debugging"""

import seFast
reload(seFast)

observationHook = None
"""Procedure that takes two arguments, an observation and an
observation model, and does some useful display.  If C{None}, then
no display is done."""

beliefHook = None
"""Procedure that takes one argument, a belief distribution, and
does some useful display.  If C{None}, then no display is done.""" 

class StateEstimator(seFast.StateEstimator):
    """By default, this is the same as C{seFast.StateEstimator}.  If
    the attributes C{observationHook} or C{beliefHook} are defined,
    then as well as doing C{getNextValues} from
    C{seFast.StateEstimator}, it calls the hooks.
    """
    def getNextValues(self, state, inp):
        if observationHook and inp:
            observationHook(inp[0], self.model.observationDistribution)
            
        result = seFast.StateEstimator.getNextValues(self, state, inp)
        
        if beliefHook:
            beliefHook(result[0])
            
        return result

"""Just like se, but a more efficient implementation"""

import sm
import ssm

import dist
import util

class StateEstimator(sm.SM):
    """
    A state machine that performs state estimation, based on an input
    stream of (input, output pairs) and a stochastic state-machine
    model.  The output at time t is a C{dist.DDist} object, representing
    the 'belief' distribution P(s | i_0, ... i_t, o_0, ..., o_t)
    """

    def __init__(self, model):
        """
        @param model: a C{ssm.StochasticStateMachine} object,
        specifying the transition and observation models
        """
        self.model = model
        self.startState = model.startDistribution
        """
        The state of this machine is the same as its output:  the
        distribution over states of the subject machine given
        the input sequence so far;  the start state of this  machine
        is the starting distribution of the subject machine.
        """

    def getNextValues(self, state, inp):
        """
        @param state: Distribution over states of the subject machine,
        represented as a C{dist.Dist} object
        @param inp: A pair C{(o, a)} of the input and output of the
        subject machine on this time step.  If this parameter is
        C{None}, then no update occurs and the state is returned,
        unchanged. 
        """
        if inp == None:
            return (state, state)

        (o, i) = inp

        total = 0
        afterObs = state.d.copy()
        for s in state.support():
            afterObs[s] *= self.model.observationDistribution(s).prob(o)
            total += afterObs[s]

        if total == 0:
            raise Exception('Observation '+str(o)+\
                            ' has 0 probability in all possible states.')

        # Note: afterObs is not normalized at this point; dividing
        # through by toal during the transition update

        new = {}
        tDist = self.model.transitionDistribution(i)
        for s in state.support():
            tDistS = tDist(s)
            oldP = afterObs[s] /total
            for sPrime in tDistS.support():
                dist.incrDictEntry(new, sPrime, tDistS.prob(sPrime) * oldP)
        dSPrime = dist.DDist(new)
            
        return (dSPrime, dSPrime)


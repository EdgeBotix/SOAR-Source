"""
State machine that acts as a state estimator, given a world model
expressed as a c{ssm.StochasticSM}.
"""

import sm
import ssm
import dist
import util

class StateEstimator(sm.SM):
    """
    A state machine that performs state estimation, based on an input
    stream of (observation, input) pairs)and a stochastic state-machine
    model.  The output at time t is a C{dist.DDist} object, representing
    the 'belief' distribution P(s | i_0, ... i_t, o_0, ..., o_t)
    """

    def __init__(self, model, verbose = False):
        """
        @param model: a C{ssm.StochasticStateMachine} object
        @param verbose: if C{True}, prints out intermediate values
        """
        self.model = model
        self.verbose = verbose
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
        @param inp: A pair C{(o, i)} of the observation (output) and input 
        of the subject machine on this time step.
        """
        (o, i) = inp
        if self.model.sensorDisplayFun:
            self.model.sensorDisplayFun(o)

        sGo = dist.bayesEvidence(state, self.model.observationDistribution, o)

        if self.verbose: 
            print 'after obs', o, sGo

        dSPrime = dist.totalProbability(sGo, 
                                        self.model.transitionDistribution(i))
        if self.verbose:
            print 'after trans', i, dSPrime
        if self.model.beliefDisplayFun:
            self.model.beliefDisplayFun(dSPrime)
            
        return (dSPrime, dSPrime)

class StateEstimatorTriggered(StateEstimator):
    """
    Like C{StateEstimator}, but the inputs are C{(observation, action,
    trigger)}.   If C{trigger} is C{True} then do the state update,
    otherwise, just pass the state through.  Output is belief state,
    and a boolean indicating whether an update was just done.
    """
    def getNextValues(self, state, inp):
        (o, i, trigger) = inp
        if trigger:
            sO = StateEstimator.getNextValues(self, state, (o, i))
            return (sO[0], (sO[1], True))
        else:
            return (state, (state, False))

def makeStateEstimationSimulation(worldSM, verbose = False):
    """
    Make a machine that simulates the state estimation process.  It
    takes a state machine representing the world, at construction
    time.  Let i be an input to the world machine.  The input is fed
    into the world machine, generating (stochastically) an output, o.
    The (o, i) pair is fed into a state-estimator using worldSM as its
    model.  The output of the state estimator is a belief state, b.
    The output of this entire composite machine is (b, (o, i)).

    @param worldSM: an instance of C{ssm.StochasticSM}
    @returns: a state machine that simulates the world and executes
    the state estimation process.
    """
    return sm.Cascade(sm.Parallel(worldSM, sm.Wire()),
                      sm.Parallel(StateEstimator(worldSM, verbose = verbose),
                                  sm.Wire()))

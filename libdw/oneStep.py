import sig
import simulate

def testSignal(simTime = 1.0):
    nsteps = int(simTime/simulate.Tsim)
    print __name__, 'nsteps ', nsteps
    ninter = nsteps/2
    return (nsteps,
	    sig.ListSignal(ninter*[{'pot1':0.0}]+\
                           ninter*[{'pot1':0.1}]))

(nsteps, sigIn) = testSignal()
def runTest(lines, parent = None, nsteps = nsteps):
    simulate.runCircuit(lines, sigIn, parent, nsteps)


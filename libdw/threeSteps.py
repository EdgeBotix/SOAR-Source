import sig
import simulate

def testSignal(simTime = 2.5):
    nsteps = int(simTime/simulate.Tsim)
    print __name__, 'nsteps ', nsteps
    ninter = nsteps/3
    return (nsteps,
	    sig.ListSignal(ninter*[{'pot1':.25}]+\
                           ninter*[{'pot1':.5}]+\
                           ninter*[{'pot1':.75}]))

(nsteps, sigIn) = testSignal()
def runTest(lines, parent = None, nsteps = nsteps):
    simulate.runCircuit(lines, sigIn, parent, nsteps)


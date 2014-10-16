import sig

class IntDistSignal(sig.Signal):
    def __init__(self, d):
        self.dist = d
        elts = d.support()
        self.minV = min(elts)
        self.maxV = max(elts)
    def sample(self, n):
        return self.dist.prob(n)
    def plotDist(self):
        self.plot(start = self.minV, end = self.maxV+1, yOrigin = 0)

def plot(d):
    IntDistSignal(d).plotDist()

from numpy import *

class name2num:
    #creates an updateable mapping between string names and node nums
    def __init__(self, variable_list = []):
        self.next_int = 0
        self.names2nums = {}
        for x in variable_list:
            self(x)
        
    def __call__(self, x):
        if type(x) == type([]):
            return map(self,x)
        else:  
            if not self.names2nums.has_key(x):
                self.names2nums[x] = self.next_int
                self.next_int = self.next_int + 1
            return self.names2nums[x]
    def names(self):
        return self.names2nums.keys()
    def max_num(self):
        return max(self.names2nums.values())

def compute_fdf(f,vals):
    #compute the nominal value of f and derivs wrt vals
    #Uses finite differences to compute derivatives.
    df = [0.0] * (len(vals))
    fnom = f(vals)
    for i in range(len(vals)):
        # rel plus abs, not robust
        delta = 1.0e-6*vals[i] + 1.0e-12 
        saveval = vals[i]
        vals[i] = saveval+delta
        fup = f(vals)
        vals[i] = saveval-delta
        fdown = f(vals)
        df[i] = (fup - fdown)/(2.0*delta)
        vals[i] = saveval
    return (fnom,df)

# Returns an array of values
def resolveConstraints(fdf, maxiters = 100):
    # Uses Newton's method to find an x s.t. F(x) = 0
    # The program expects that fdf(x,f,Jf) takes two arrays
    # and a matrix, and modifies f and Jf so that f = F(x)
    # and Jf = derivative of f wrt x.  Finally, fdf should return
    # num of equations and num variables when call with null arrays.

    # Find out size of arrays and initialize
    vars,fs = fdf([],[], [])
    if not(vars == fs):
        print 'Number of variables = ', vars
        print 'Does not match number of eqns = ', fs
        print 'Did you forget a conservation law or to set a ground?'
    assert vars == fs, 'equation/variable mismatch error'
    
    x = array([0.0]*vars)
    f = array([0.0]*fs)
    Jf = array([[0.0 for col in range(vars)] for row in range(fs)])

    # Iterate until f(x) is small enough.
    for i in range(maxiters):
        fdf(x,f,Jf)
        dx = linalg.solve(Jf,f)
        x = x - dx
        err = sum(abs(dx))
        if err < 1.0e-10 :
            break
    if err > 1.0e-10 :
        print 'error exceeds ', err, ' in ', maxiters, ' iterations'
    return x
        
class ConstraintSet:
    def __init__(self):
        self.constraints = []
        self.n2n = name2num([])
        
    def addConstraint(self, f, variables):
        # Adds a constraint where f(variables) = 0, variables is list of strgs
        self.constraints.append([f,variables])
        [self.n2n(var) for var in variables]
        
    def listVariables(self): #list of variables without duplicates
        return self.n2n.names()

    def FdF(self,x,F,JF):
        # Calling routine does not know the sizes, return sizes and leave
        if F == []:
            return len(self.listVariables()), len(self.constraints)
        
        # Use zero as the default values for x
        if x == []:
            x = [0] * len(self.listVariables())
                          
        # Iterate through constraint container
        j = 0 
        for f_v in self.constraints: 

            # Indices of elments of x associated with constraint's variables
            index_list =  map(self.n2n, f_v[1])

            # Compute the constraint function and derivatives for given values
            f,df = compute_fdf(f_v[0], [x[i] for i in index_list])
            F[j] = f
            if not(JF == []):
                for i in index_list:
                    JF[j][i] = df.pop(0)
            j = j+1

        return x,F

    # solution is an array of values
    def translate(self, variable, solution):
        return solution[self.n2n(variable)]

    # solution is an array of values
    def display(self, solution):
        varlist = self.listVariables()
        varlist.sort()
        for var in varlist:
            print var, ' = ', self.translate(var, solution)

    def __call__(self):  # Returns constraint evaluation function for the list
        return self.FdF

    def getConstraintEvaluationFunction(self):
        return self.FdF

    def solve(self):
        sol = resolveConstraints(self.FdF)
        return Solution(self.n2n, [x for x in sol])

class Solution:
    def __init__(self, n2i, values):
        self.n2i = n2i
        """Mapping from variable names to indices"""
        self.values = values
        """List of values of the variables, in order of their indices"""

    def translate(self, name):
        """
        @returns: the value of variable C{name} in the solution
        """
        return self.values[self.n2i(name)]




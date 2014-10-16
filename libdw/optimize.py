"""
Procedures for finding values of a function to optimize its output.
"""

import operator

def floatRange(lo, hi, stepsize):
    """
    @returns: a list of numbers, starting with C{lo}, and increasing
    by C{stepsize} each time, until C{hi} is equaled or exceeded.

    C{lo} must be less than C{hi}; C{stepsize} must be greater than 0.
    """
    result = []
    if stepsize == 0:
       print 'Stepsize is 0 in floatRange'
       return result
    v = lo
    while v < hi:
        result.append(v)
        v += stepsize
    return result

def argopt(f, stuff, comp):
    """
    @param f: a function that takes a single argument of some type
    C{x} and returns a value of some type C{y}
    @param stuff: a list of elements of type C{x}
    @param comp: a function that takes two arguments of type C{y} and
    returns a Boolean;  it is intended to return C{True} if the first
    argument is 'better' than the second.
    @returns: a pair C{(bestVal, bestArg)}, where C{bestArg} is the
    element of C{stuff} such that C{f(bestArg)} is better, according
    to C{comp} than C{f} applied to any other element of C{stuff}, and
    C{bestVal} is C{f(bestArg)}.
    
    The types C{x} and C{y} are not actual types;  they're just
    intended to show that the types of the functions have to match up
    in the right way.
    
    For example, get the team with the highest score, you might do
    something like

    C{argopt(seasonScore, ['ravens', 'crows', 'buzzards'], operator.gt)}

    where C{seasonScore} is a function that takes the name of a team
    and returns a numerical score.
    """
    bestValSoFar = None
    bestArgSoFar = None
    for x in stuff:
        v = f(x)
        if bestValSoFar == None or comp(v, bestValSoFar):
            bestValSoFar = v
            bestArgSoFar = x
    return (bestValSoFar, bestArgSoFar)

def optOverLine(objective, xmin, xmax, numXsteps, 
               compare = operator.lt):
    """
    @param objective: a function that takes a single number as an
               argument and returns a value
    @param compare: a function from two values (of the type returned
               by C{objective}) to a Boolean;  should return C{True}
               if we like the first argument better.
    @returns: a pair, C{(objective(x), x)}.  C{x} one of the numeric
               values achieved by starting at C{xmin} and taking
               C{numXsteps} equal-sized steps up to C{xmax};  the
               particular value of C{x} returned is the one for which
               C{objective(x)} is best, according to the C{compare}
               operator. 
    """
    if type(numXsteps) != int:
        raise Exception, 'numXsteps should be an integer number of steps'
    return argopt(objective, floatRange(xmin, xmax, 
                                        (xmax - xmin) / float(numXsteps)),
                  compare)

def optOverGrid(objective, 
               xmin, xmax, numXsteps, 
               ymin, ymax, numYsteps, 
               compare = operator.lt):
    """
    Like C{optOverLine}, but C{objective} is now a function from two
    numerical values, one chosen from the C{x} range and one chosen
    from the C{y} range.  It returns C{(objective(x, y), (x, y))} for
    the optimizing pair C{(x,y)}.
    """
    ((score, y), x) = \
             optOverLine(lambda x: optOverLine(lambda y: objective(x, y),
                                               ymin, ymax, numYsteps,
                                               compare),
                         xmin, xmax, numXsteps,
                         lambda (s1,v1),(s2,v2):compare(s1, s2))
    return (score, (x, y))

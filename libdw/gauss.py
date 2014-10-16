
## Gauss Jordan as implemented by Numerical Recipes in C
## Ported to Python by TLP

def swap1(b,i1,i2):
    temp = b[i1]
    b[i1] = b[i2]
    b[i2] = temp

def swap2(a, i1, j1, i2, j2):
    temp = a[i1][j1]
    a[i1][j1] = a[i2][j2]
    a[i2][j2] = temp

## A is a matrix (as a list of lists)
## b is a vector (as a list)

def gaussSolve(Ain, bin):
    n = len(bin)+1
    ## pad out the input, so indices begin at 1, also copy
    A = [n*[0]]+[[0]+Ai[:] for Ai in Ain]
    b = [0]+bin[:]
    # print 'A=', A
    # print 'b=', b
    # initialize temps
    indexc = n*[0]
    indexr = n*[0]
    ipiv = n*[0]
    for i in range(1,n):
        big = 0.0
        for j in range(1, n):
            if ipiv[j] != 1:
                for k in range(1, n):
                    if ipiv[k] == 0:
                        if abs(A[j][k]) >= big:
                            big = abs(A[j][k])
                            irow = j;
                            icol = k;
                    elif ipiv[k] > 1:
                        raise Exception, "Error: Singular Matrix"
        ipiv[icol] += 1
        if irow != icol:
            for l in range(1, n): swap2(A, irow, l, icol, l)
            swap1(b, irow, icol)
        indexr[i] = irow
        indexc[i] = icol
        if A[icol][icol] == 0.0:
            raise Exception, "Error: Singular Matrix"
        pivinv = 1.0/A[icol][icol]
        A[icol][icol] = 1.0
        for l in range(1,n): A[icol][l] *= pivinv
        b[icol] *= pivinv
        for ll in range(1, n):
            if ll != icol:
                dum = A[ll][icol]
                A[ll][icol] = 0.0
                for l in range(1, n): A[ll][l] -= A[icol][l]*dum
                b[ll] -= b[icol]*dum
    for l in range(n-1, 0, -1):
        if indexr[l] != indexc[l]:
            for k in range(1, n):
                swap2(A, k, indexr[l], k, indexc[l])
    return b[1:]

# Test cases
A1 = [[1.0, 0.0, 0.0],
      [0.0, 2.0, 0.0],
      [0.0, 0.0, 3.0]]
b1a = [1.0, 0.0, 0.0]
b1b = [1.0, 1.0, 1.0]

A2 = [[1.0, 2.0, 3.0],
      [2.0, 2.0, 3.0],
      [3.0, 3.0, 3.0]]
b2a = [1.0, 1.0, 1.0]
b2b = [1.0, 2.0, 3.0]

A3 = [[1.0, 2.0, 3.0, 4.0, 5.0],
      [2.0, 3.0, 4.0, 5.0, 1.0],
      [3.0, 4.0, 5.0, 1.0, 2.0],
      [4.0, 5.0, 1.0, 2.0, 3.0],
      [5.0, 1.0, 2.0, 3.0, 4.0]]
b3a = [1.0, 1.0, 1.0, 1.0, 1.0]
b3b = [1.0, 2.0, 3.0, 4.0, 5.0]

A4 = [[1.4, 2.1, 2.1, 7.4, 9.6],
      [1.6, 1.5, 1.1, 0.7, 5.0],
      [3.8, 8.0, 9.6, 5.4, 8.8],
      [4.6, 8.2, 8.4, 0.4, 8.0],
      [2.6, 2.9, 0.1, 9.6, 7.7]]
b4a = [1.1, 1.6, 4.7, 9.1, 0.1]
b4b = [4.0, 9.3, 8.4, 0.4, 4.1]


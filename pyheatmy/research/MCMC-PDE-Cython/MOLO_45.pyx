import numpy as np
from libc.stdlib cimport malloc, free
from libc.stdlib cimport rand, srand, RAND_MAX
from libc.math cimport log, sqrt, exp
from libc.time cimport time

##Matrix objects and operations

#creates a malloc array from a memoryview
cdef double* numpy_to_C(double[:] X):
    cdef int size = X.shape[0]
    cdef double* Xr = <double*> malloc(size * sizeof(double))
    cdef int i
    for i in range(size):
        Xr[i] = X[i]
    return Xr

#creates a memoryview from a malloc array
cdef double[:] C_to_numpy(double* X, int size):
    cdef double[:] Xr = np.empty(size,dtype=np.double)
    cdef int i
    for i in range(size):
        Xr[i] = X[i]
    return Xr

#returns coefficient (i,j) of a triadiagonal matrix stored as a malloc array
cdef double tridget(double* coefs, int size, int i, int j):
    cdef int select = i-j
    #coef from the subdiagonal
    if select>0:
        return coefs[i-1]
    #coef from the diagonal
    elif select<0:
        return coefs[2*size-1+i]
    #coef from the superdiagonal
    else:
        return coefs[size-1+i]

#to build an ordinary (n,m) real matrix
cdef class Matrix:
    
    #matrix stored in a malloc array
    cdef double* mat
    #number of lines
    cdef int n
    #number of columns
    cdef int m
    
    cdef void init(self,int n, int m):
        self.n = n
        self.m = m
        self.mat = <double*> malloc((n*m) * sizeof(double))
    
    cdef void set(self, int i, int j, double val):
        self.mat[i*self.m+j] = val
    
    cdef double get(self, int i, int j):
        return self.mat[i*self.m+j]
    
    #assigns values of a contiguous row slice
    cdef void slicerowset(self,int i, int j1, int j2, double* row):
        cdef int j
        for j in range(j1,j2):
            self.set(i,j,row[j-j1])       
    
    def convert_to_numpy(self):
        A = np.empty((self.n,self.m),dtype=np.double)
        cdef double[:, ::1] A_view = A
        cdef int i
        for i in range(self.n):
            for j in range(self.m):
                A_view[i,j] = self.get(i,j)
        return np.asarray(A)
    
    def extract_from_numpy(self, double[:, ::1] A):
        cdef int i
        for i in range(self.n):
            for j in range(self.m):
                self.set(i,j, A[i,j])
                
    cdef void free(self):        
        free(self.mat)

#to build a tridiagonal (n,n) real matrix        
cdef class Tridiag:
    
    #matrix stored in a malloc array
    cdef double* mat
    #number of lines or rows
    cdef int size
    
    cdef void init(self,int size):
        self.size = size
        self.mat = <double*> malloc((3*size-2) * sizeof(double))
        
    cdef void set(self,int i, int j, double val):
        cdef int select = i-j
        #subdiagonal
        if select>0:
            self.mat[i-1] = val
        #diagonal
        elif select<0:
            self.mat[2*self.size-1+i] = val
        #superdiagonal
        else:
            self.mat[self.size-1+i] = val
    
    #assigns identity matrix coef values
    cdef void identity(self):
        
        #first row
        self.set(0,0,1)
        self.set(0,1,0)
        
        cdef int i
        for i in range(1,self.size-1):
            self.set(i,i-1,0)
            self.set(i,i,1)
            self.set(i,i+1,0)
        
        #last row
        self.set(self.size-1,self.size-2,0)
        self.set(self.size-1,self.size-1,1)        
    
    #assigns three given diagonals
    cdef void diagset(self,double* sub_diag, double* diag, double* sup_diag):
        
        #first row
        self.set(0,0,diag[0])
        self.set(0,1,sup_diag[0])
        
        cdef int i
        for i in range(1,self.size-1):
            self.set(i,i-1,sub_diag[i-1])
            self.set(i,i,diag[i])
            self.set(i,i+1,sup_diag[i])
        
        #last row    
        self.set(self.size-1,self.size-2,sub_diag[self.size-2])
        self.set(self.size-1,self.size-1,diag[self.size-1])
        
    cdef double get(self,int i, int j):
        cdef int select = i-j
        #subdiagonal
        if select>0:
            return self.mat[i-1]
        #diagonal
        elif select<0:
            return self.mat[2*self.size-1+i]
        #superdiagonal
        else:
            return self.mat[self.size-1+i]
    
    #multiplies the matrix with a scalar    
    cdef void scalarmul(self,double a):
        
        #first row
        self.set(0,0,a*self.get(0,0))
        self.set(0,1,a*self.get(0,1))
        
        cdef int i
        for i in range(1,self.size-1):
            self.set(i,i-1,a*self.get(i,i-1))
            self.set(i,i,a*self.get(i,i))
            self.set(i,i+1,a*self.get(i,i+1))
        
        #last row
        self.set(self.size-1,self.size-2,a*self.get(self.size-1,self.size-2))
        self.set(self.size-1,self.size-1,a*self.get(self.size-1,self.size-1)) 
    
    #returns the image of a vector
    #WARNING: it returns a new malloc array
    cdef double* dot(self,double* X):
        
        cdef double* Xr = <double*> malloc(self.size * sizeof(double))
        
        #first coef
        Xr[0] = self.get(0,0)*X[0] + self.get(0,1)*X[1]
        
        cdef int i
        for i in range(1,self.size-1):
            Xr[i] = self.get(i,i-1)*X[i-1] + self.get(i,i)*X[i] + self.get(i,i+1)*X[i+1]
        
        #last coef
        Xr[self.size-1] = self.get(self.size-1,self.size-2)*X[self.size-2] + self.get(self.size-1,self.size-1)*X[self.size-1]
        
        return Xr
    
    #copies the tridiagonal matrix coef values given as an array
    cdef void copy(self,double* A):
        
        #first row
        self.set(0,0, tridget(A,self.size,0,0))
        self.set(0,1, tridget(A,self.size,0,1))
        
        cdef int i
        for i in range(1,self.size-1):
            self.set(i,i-1,tridget(A,self.size,i,i-1))
            self.set(i,i,tridget(A,self.size,i,i))
            self.set(i,i+1,tridget(A,self.size,i,i+1))
         
        #last row
        self.set(self.size-1,self.size-2,tridget(A,self.size,self.size-1,self.size-2))
        self.set(self.size-1,self.size-1,tridget(A,self.size,self.size-1,self.size-1))
    
    #assigns the sum of two tridiagonal matrices given as arrays 
    cdef void add(self,double* A, double* B):
        
        #first row
        self.set(0,0, tridget(A,self.size,0,0) + tridget(B,self.size,0,0))
        self.set(0,1, tridget(A,self.size,0,1) + tridget(B,self.size,0,1))
        
        cdef int i
        for i in range(1,self.size-1):
            self.set(i,i-1,tridget(A,self.size,i,i-1) + tridget(B,self.size,i,i-1))
            self.set(i,i,tridget(A,self.size,i,i) + tridget(B,self.size,i,i))
            self.set(i,i+1,tridget(A,self.size,i,i+1) + tridget(B,self.size,i,i+1))
        
        #last row    
        self.set(self.size-1,self.size-2,tridget(A,self.size,self.size-1,self.size-2) + tridget(B,self.size,self.size-1,self.size-2))
        self.set(self.size-1,self.size-1,tridget(A,self.size,self.size-1,self.size-1) + tridget(B,self.size,self.size-1,self.size-1))
    
    #solves the linear system A*x = d
    #uses Thomas algorithm 
    #WARNING: the solution is returned as a new malloc array
    cdef double* solve(self,double* d):

        cdef double* cp = <double*> malloc((self.size-1) * sizeof(double))
        cdef double* dp = <double*> malloc(self.size * sizeof(double))
        cdef double* s = <double*> malloc(self.size * sizeof(double))
        cdef int i 

        cp[0] = self.get(0,1)*self.get(0,0)**(-1)
        for i in range(1,self.size-1):
            cp[i] = self.get(i,i+1)*(self.get(i,i)-self.get(i+1,i)*cp[i-1])**(-1)

        dp[0] = d[0]*self.get(0,0)**(-1)
        for i in range(1,self.size):
            dp[i] = (d[i]-self.get(i,i-1)*dp[i-1])*(self.get(i,i)-self.get(i,i-1)*cp[i-1])**(-1)

        s[self.size-1] = dp[self.size-1]
        for i in range(1,self.size):
            s[self.size-1-i] = dp[self.size-1-i] - cp[self.size-1-i]*s[self.size-i]
        
        free(cp)
        free(dp)
        
        return s
    
    cdef void free(self):        
        free(self.mat)
    
    def convert_to_numpy(self):
        A = np.zeros((self.size,self.size),dtype=np.double)
        cdef double[:, ::1] A_view = A
        cdef int i
        A_view[0,0] = self.get(0,0)
        A_view[0,1] = self.get(0,1)
        for i in range(1,self.size-1):
            A_view[i,i-1] = self.get(i,i-1)
            A_view[i,i] = self.get(i,i)
            A_view[i,i+1] = self.get(i,i+1)
        A_view[self.size-1,self.size-2] = self.get(self.size-1,self.size-2)
        A_view[self.size-1,self.size-1] = self.get(self.size-1,self.size-1)
        return np.asarray(A)

##MOLONARI objects

###Physical model

#to build the discretized spatial structure of the studied ground layer    
cdef class Geometry:
    #number of ground cells (or sublayers)
    cdef int N
    #height of the studied ground layer [m]
    cdef double h
    #cells widths [m]
    cdef double* width
    #spacings between consecutive cells [m]
    cdef double* spacing
    #cells interfaces depths [m]
    cdef double* depth_i
    #cells depths [m]
    cdef double* depth_c
    
    cdef void init(self,int N):
        self.N = N
        self.width = <double*> malloc((N+2) * sizeof(double))
        self.spacing = <double*> malloc((N+1) * sizeof(double))
        self.depth_c = <double*> malloc(N * sizeof(double))
        self.depth_i = <double*> malloc((N+1) * sizeof(double))
    
    #creates a regular spatial structure 
    cdef void regular(self, double h):
        
        self.h = h
        cdef double l = h*(<double> self.N + 1)**(-1)
        
        cdef int i 
        for i in range(self.N):
            self.width[i] = l
            self.spacing[i] = l
            self.depth_c[i] = (i+1)*l
            self.depth_i[i] = i*l+0.5*l
         
        self.width[self.N] = l
        self.spacing[self.N] = l
        self.depth_i[self.N] = h
        self.width[self.N+1] = l
    
    cdef void free(self):
        free(self.width)
        free(self.spacing)
        free(self.depth_c)
        free(self.depth_i)

#to build a conduction matrix for discretized equations 
cdef class Umatrix:
    #number of main cells
    cdef int N
    cdef Tridiag Umat
    #auxiliary array used in boundary conditions
    cdef double* B_U  
    cdef Geometry geo
    #conductivities    
    cdef double* L
    #capacities
    cdef double* C
    
    cdef void init(self, int N, Geometry geo, double* Lambda, double* C):
        self.N = N
        self.Umat = Tridiag()
        self.Umat.init(N)
        self.B_U = <double*> malloc(2 * sizeof(double))
        self.geo = geo
        self.L = Lambda
        self.C = C
    
    #assigns matrix Umat coef values using formulas given in theoretical doc
    #also computes B_U
    cdef void compute(self):
        
        #first row
        self.Umat.set(0,0,
                      (-self.L[0]*self.geo.spacing[0]**(-1)-self.L[1]*self.geo.spacing[1]**(-1))
                      *(self.C[0]*self.geo.width[1])**(-1))
        self.Umat.set(0,1,
                      self.L[1]
                      *(self.C[0]*self.geo.width[1]*self.geo.spacing[1])**(-1))
        
        cdef int i
        for i in range(1,self.N-1):
            self.Umat.set(i,i-1,
                          self.L[i]
                          *(self.C[i]*self.geo.width[i+1]*self.geo.spacing[i])**(-1))
            self.Umat.set(i,i,
                          (-self.L[i]*self.geo.spacing[i]**(-1)-self.L[i+1]*self.geo.spacing[i+1]**(-1))
                          *(self.C[i]*self.geo.width[i+1])**(-1))
            self.Umat.set(i,i+1,
                          self.L[i+1]
                          *(self.C[i]*self.geo.width[i+1]*self.geo.spacing[i+1])**(-1))
                          
        #last row
        self.Umat.set(self.N-1,self.N-2,
                      self.L[self.N-1]
                      *(self.C[self.N-1]*self.geo.width[self.N]*self.geo.spacing[self.N-1])**(-1))
        self.Umat.set(self.N-1,self.N-1,
                      (-self.L[self.N-1]*self.geo.spacing[self.N-1]**(-1)-self.L[self.N]*self.geo.spacing[self.N]**(-1))
                      *(self.C[self.N-1]*self.geo.width[self.N])**(-1))
        
        self.B_U[0] = (self.L[0]
                       *(self.C[0]*self.geo.width[1]*self.geo.spacing[0])**(-1))
        self.B_U[1] = (self.L[self.N]
                       *(self.C[self.N-1]*self.geo.width[self.N]*self.geo.spacing[self.N])**(-1))
        
    cdef void free(self):
        self.Umat.free()
        free(self.B_U)

#to build an advection matrix for discretized equations        
cdef class Vmatrix:
    #number of mail cells
    cdef int N
    cdef Tridiag Vmat
    #auxiliary array used in boundary conditions
    cdef double* B_V
    cdef Geometry geo
    #conductivities
    cdef double* L
    #capacities
    cdef double* C
    #permeabilities
    cdef double* K
    #water heat capacity [J*kg^{-1}*K^{-1}]
    cdef double cw
    #water density [kg*m^{-3}] 
    cdef double rhow
    
    cdef void init(self, int N, Geometry geo, double* Lambda, double* C, double* K):
        self.N = N
        self.Vmat = Tridiag()
        self.Vmat.init(N)
        self.B_V = <double*> malloc(2 * sizeof(double))
        self.geo = geo
        self.L = Lambda
        self.C = C
        self.K = K
        self.cw = 4180
        self.rhow = 1000
     
    #assigns matrix Vmat coef values using formulas given in theoretical doc
    #also computes B_V
    cdef void compute(self, double* grad):        
        
        #first row
        self.Vmat.set(0,0,
                      self.cw*self.rhow*(-self.K[0]*grad[0]*self.geo.width[0]*(2*self.geo.spacing[0])**(-1)
                                         +self.K[1]*grad[1]*self.geo.width[2]*(2*self.geo.spacing[1])**(-1))
                      *(self.C[0]*self.geo.width[1])**(-1))
        self.Vmat.set(0,1,
                      self.cw*self.rhow*self.K[1]*grad[1]
                      *(2*self.C[0]*self.geo.spacing[1])**(-1))
        
        cdef int i
        for i in range(1,self.N-1):
            self.Vmat.set(i,i-1,
                          -self.cw*self.rhow*self.K[i]*grad[i]
                          *(2*self.C[i]*self.geo.spacing[i])**(-1))
            self.Vmat.set(i,i,
                          self.cw*self.rhow*(-self.K[i]*grad[i]*self.geo.width[i]*(2*self.geo.spacing[i])**(-1)
                                             +self.K[i+1]*grad[i+1]*self.geo.width[i+2]*(2*self.geo.spacing[i+1])**(-1))
                          *(self.C[i]*self.geo.width[i+1])**(-1))
            self.Vmat.set(i,i+1,
                          self.cw*self.rhow*self.K[i+1]*grad[i+1]
                          *(2*self.C[i]*self.geo.spacing[i+1])**(-1))
        
        #last row
        self.Vmat.set(self.N-1,self.N-2,
                      -self.cw*self.rhow*self.K[self.N-1]*grad[self.N-1]
                      *(2*self.C[self.N-1]*self.geo.spacing[self.N-1])**(-1))
        self.Vmat.set(self.N-1,self.N-1,
                      self.cw*self.rhow*(-self.K[self.N-1]*grad[self.N-1]*self.geo.width[self.N-1]*(2*self.geo.spacing[self.N-1])**(-1)
                                             +self.K[self.N]*grad[self.N]*self.geo.width[self.N+1]*(2*self.geo.spacing[self.N])**(-1))
                      *(self.C[self.N-1]*self.geo.width[self.N])**(-1))
        
        self.B_V[0] = (-self.cw*self.rhow*self.K[0]*grad[0]
                       *(2*self.geo.spacing[0]*self.C[0])**(-1))
        self.B_V[1] = (self.cw*self.rhow*self.K[self.N]*grad[self.N]
                       *(2*self.geo.spacing[self.N]*self.C[self.N-1])**(-1))
        
    cdef void free(self):
        self.Vmat.free()
        free(self.B_V)

#to build an efficient linear data interpolation function
#requires data sampled with a constant sampling step        
cdef class QuickInterpol:
    #number of samples
    cdef int Ntimes
    #sampling step
    cdef double dt
    #sampling start
    cdef double t0
    #sampling end
    cdef double tf
    #array storing data to interpolate
    cdef double* X
    
    cdef void init(self,int Ntimes, double dt, double t0, double tf, double* X):
        self.Ntimes = Ntimes
        self.dt = dt
        self.t0 = t0
        self.tf = tf
        self.X = X
    
    #returns a linear interpolation at "time" t
    cdef double eval(self,double t):
        cdef int n
        cdef double frac
        cdef double e
        #before sampling start
        if t <= self.t0:    
            return self.X[0]
        #after sampling end
        elif t >= self.tf:
            return self.X[self.Ntimes-1]
        else:
            frac = (t-self.t0)*(self.dt)**(-1)
            n = <int>(frac)
            e = frac-n            
            return self.X[n]*(1-e) + self.X[n+1]*e
        
    cdef void free(self):
        free(self.X)

#to build a linear data interpolation function
#with possibly a non constant sampling step
cdef class SlowInterpol:
    #number of samples
    cdef int Ntimes
    #sampling times
    cdef double* times
    #sampling start
    cdef double t0
    #sampling end
    cdef double tf
    #array storing data to interpolate
    cdef double* X
    
    cdef void init(self,int Ntimes, double* times, double* X):
        self.Ntimes = Ntimes
        self.times = times
        self.t0 = times[0]
        self.tf = times[Ntimes-1]
        self.X = X
    
    #returns a linear interpolation at "time" t
    #uses dichotomic method
    cdef double eval(self,double t):
        cdef int a = 0
        cdef int b = self.Ntimes
        cdef int m
        cdef double e
        if t<self.t0:    
            return self.X[0]
        elif t>=self.tf:
            return self.X[self.Ntimes-1]
        else:
            while b-a>1:
                m = (a+b)//2
                if t < self.times[m]:
                    b = m
                else:
                    a = m
            e = (t-self.X[a])*(self.X[a+1]-self.X[a])**(-1)
            return self.X[a]*(1-e) + self.X[a+1]*e
        
    cdef void free(self):
        free(self.X)
        free(self.times)

#tool to summarize physical properties of ground layers and sublayers
cdef class StratifiedParams:
    
    #number of layers
    cdef int Nl
    #depths of layers boundaries [m]
    #[right limit layer 0, right limit interlayer 01, right limit layer 1 ...]
    cdef double* border
    #conductivies in layers
    cdef double* Ll
    #conductivies in sublayers
    cdef double* L
    #capacities in layers
    cdef double* Cl
    #capacities in sublayers
    cdef double* C
    #permeabilities in layers
    cdef double* Kl
    #permeabilities in sublayers
    cdef double* K
    #specific capacity in layers
    cdef double* Sl
    #specific capacity in sublayers
    cdef double* S
    cdef Geometry geo
    
    cdef void init(self, int Nl, double* border, Geometry geo):
        self.Nl = Nl
        self.border = border
        self.L = <double*> malloc((geo.N+1) * sizeof(double))
        self.C = <double*> malloc(geo.N * sizeof(double))
        self.K = <double*> malloc((geo.N+1) * sizeof(double))
        self.S = <double*> malloc(geo.N * sizeof(double))
        self.geo = geo
        
    cdef void update_layers_params(self, double* Ll, double* Cl, double* Kl, double* Sl):
        self.Ll = Ll
        self.Cl = Cl
        self.Kl = Kl
        self.Sl = Sl       
    
    #assigns sublayers parameters values according to the layer they belong to    
    cdef void compute(self):
        
        cdef int i
        cdef int d = 0
        cdef int layer_bool = 1
        cdef int layer_id = 0
        cdef double e
        
        #conductive properties (specific to an interface)
        for i in range(self.geo.N+1):
            
            while self.geo.depth_i[i] > self.border[d]:
                d = d + 1
                if layer_bool == 0:
                    layer_bool = 1
                    layer_id = layer_id + 1
                else:
                    layer_bool = 0
            
            #in the layer
            if layer_bool == 1:
                self.L[i] = self.Ll[layer_id]
                self.K[i] = self.Kl[layer_id]
            #in the interlayer (or interface)
            else:
                e = (self.border[d]-self.geo.depth_i[i])*(self.border[d]-self.border[d-1])**(-1)
                self.L[i] = e*self.Ll[layer_id] + (1-e)*self.Ll[layer_id+1]
                self.K[i] = e*self.Kl[layer_id] + (1-e)*self.Kl[layer_id+1]
        
        d = 0
        layer_bool = 1
        layer_id = 0
        
        #capacitive properties (specific to a cell or sublayer)
        for i in range(self.geo.N):
            
            while self.geo.depth_c[i] > self.border[d]:
                d = d + 1
                if layer_bool == 0:
                    layer_bool = 1
                    layer_id = layer_id + 1
                else:
                    layer_bool = 0
            
            #in the layer
            if layer_bool == 1:
                self.C[i] = self.Cl[layer_id]
                self.S[i] = self.Sl[layer_id]
            #in the interlayer 
            else:
                e = (self.border[d]-self.geo.depth_i[i])*(self.border[d]-self.border[d-1])**(-1)
                self.C[i] = e*self.Cl[layer_id] + (1-e)*self.Cl[layer_id+1]
                self.S[i] = e*self.Sl[layer_id] + (1-e)*self.Sl[layer_id+1]
    
    cdef void free(self):
        free(self.L)
        free(self.Ll)
        free(self.C)
        free(self.Cl)
        free(self.K)
        free(self.Kl)
        free(self.S)
        free(self.Sl)
        free(self.border)
        
cdef double norm(double* X, int n, int id = 2):
    cdef double result = 0
    cdef int i
    for i in range(n):
        result = result + X[i]**(id)
    return result**((<double> id)**(-1))
    
cdef double distance(double* X, double* Y, int n, int id = 2):
    cdef double result = 0
    cdef int i
    for i in range(n):
        result = result + (X[i]-Y[i])**(id)
    return result**((<double> id)**(-1))
    
#tool to solve discretized equations                
cdef class StratifiedModel:
    
    #number of main cells
    cdef int N
    cdef StratifiedParams params
    cdef Umatrix Umatrix_T
    cdef Vmatrix Vmatrix_T
    cdef Umatrix Umatrix_H
    cdef Geometry geo
    #array storing cells hydraulic charges [m]
    cdef double* H
    #array storing hydraulic gradient
    cdef double* Hz
    #array storing cells temperatures [K]
    cdef double* T
    
    #to get boundary conditions
    cdef QuickInterpol Hriv
    cdef QuickInterpol Haq
    cdef QuickInterpol Triv
    cdef QuickInterpol Taq
    
    #to facilitate computations
    cdef Tridiag I
    cdef Tridiag A
    
    cdef double* depths_meas
    cdef int nb_meas
    #location of the cells at measures depths
    cdef int* interpol_index
    #weights necessary for linear interpolation
    cdef double* interpol_weights
    cdef double norm_H0
    cdef double norm_H1
    cdef double norm_T0
    cdef double norm_T1
    cdef double atol_H
    cdef double rtol_H
    cdef double atol_T
    cdef double rtol_T
    cdef int norm_id
    
    cdef void init(self,
                 int N,
                 double h,
                 double* Hriv,
                 double* Haq,
                 double* Triv,
                 double* Taq,
                 int Ntimes,
                 double dt,
                 double t0,
                 double tf,
                 int Nl,
                 double* borders,
                 double* depths_meas,
                 int nb_meas):
        
        self.N = N
        self.geo = Geometry()
        self.geo.init(N)
        self.geo.regular(h)
        
        self.Hriv = QuickInterpol()
        self.Hriv.init(Ntimes,dt,t0,tf,Hriv)
        self.Haq = QuickInterpol()
        self.Haq.init(Ntimes,dt,t0,tf,Haq)
        self.Triv = QuickInterpol()
        self.Triv.init(Ntimes,dt,t0,tf,Triv)
        self.Taq = QuickInterpol()
        self.Taq.init(Ntimes,dt,t0,tf,Taq)
        
        self.params = StratifiedParams()
        self.params.init(Nl,borders,self.geo)
        
        self.Umatrix_H = Umatrix()
        self.Umatrix_T = Umatrix()
        self.Vmatrix_T = Vmatrix()
               
        self.Hz = <double*> malloc((self.N+1) * sizeof(double))
        self.H = <double*> malloc(self.N * sizeof(double))
        self.T = <double*> malloc(self.N * sizeof(double))
        
        self.I = Tridiag()
        self.I.init(N)
        self.I.identity()
        
        self.A = Tridiag()
        self.A.init(N)
        
        self.depths_meas = depths_meas
        self.nb_meas = nb_meas
    
    #updates static paremeters and associated objects
    cdef void update_params(self,double* Ll, double* Cl, double* Kl, double* Sl):
        self.params.update_layers_params(Ll,Cl,Kl,Sl)
        self.params.compute()
        self.Umatrix_T.init(self.N,self.geo,self.params.L,self.params.C)
        self.Umatrix_T.compute()
        self.Vmatrix_T.init(self.N,self.geo,self.params.L,self.params.C,self.params.K)
        self.Umatrix_H.init(self.N,self.geo,self.params.K,self.params.S)
        self.Umatrix_H.compute()
    
    #computes interpol_index and interpol_weights
    cdef void prepare_interpol_T(self):
        
        self.interpol_index = <int*> malloc(self.nb_meas * sizeof(int))
        self.interpol_weights = <double*> malloc(self.nb_meas * sizeof(double))
        cdef int i, a, b, m
        cdef double e, d
        
        for i in range(self.nb_meas):
            
            d = self.depths_meas[i]
            
            if d <= self.geo.depth_c[0]:    
                self.interpol_index[i] = 0
                self.interpol_weights[i] = 1
            elif d >= self.geo.depth_c[self.N-1]:
                self.interpol_index[i] = self.N-2
                self.interpol_weights[i] = 0
            else:
                a = 0
                b = self.N
                while b-a>1:
                    m = (a+b)//2
                    if self.depths_meas[i] < self.geo.depth_c[m]:
                        b = m
                    else:
                        a = m
                e = (d-self.geo.depth_c[a])*(self.geo.depth_c[a+1]-self.geo.depth_c[a])**(-1)
                self.interpol_index[i] = a
                self.interpol_weights[i] = 1-e
    
    #computes hydraulic gradient
    cdef void compute_Hz(self,double hriv, double haq):
        self.Hz[0] = (self.H[0]-hriv)*(self.geo.spacing[0])**(-1)
        cdef int i
        for i in range(1,self.N):
            self.Hz[i] = (self.H[i]-self.H[i-1])*(self.geo.spacing[i])**(-1)
        self.Hz[self.N] = (haq-self.H[self.N-1])*(self.geo.spacing[self.N])**(-1)
        
    #One Step Implicit Euler
    #computes the next T and H at t + dt 
    cdef void OSIEuler(self,double t, double dt):
        
        #boundaries parameters        
        cdef double hriv = self.Hriv.eval(t+dt)
        cdef double haq = self.Haq.eval(t+dt)
        cdef double triv = self.Triv.eval(t+dt)
        cdef double taq = self.Taq.eval(t+dt)
        
        cdef double* aux = <double*> malloc(self.N * sizeof(double))
        cdef int i
        
        #hydraulic boundary conditions
        aux[0] = dt*self.Umatrix_H.B_U[0]*hriv + self.H[0]        
        for i in range(1,self.N-1):            
            aux[i] = self.H[i]            
        aux[self.N-1] = dt*self.Umatrix_H.B_U[1]*haq + self.H[self.N-1]
        
        #hydraulic conduction matrix
        self.A.copy(self.Umatrix_H.Umat.mat)
        self.A.scalarmul(-dt)
        self.A.add(self.I.mat,self.A.mat)
        
        free(self.H)
        #computes H[t+dt]        
        self.H = self.A.solve(aux)
        
        #heat exchange matrix
        self.compute_Hz(hriv,haq)
        self.Vmatrix_T.compute(self.Hz)
        self.A.add(self.Umatrix_T.Umat.mat,self.Vmatrix_T.Vmat.mat)
        self.A.scalarmul(-dt)
        self.A.add(self.I.mat,self.A.mat)
        
        #heat boundary conditions
        aux[0] = dt*(self.Umatrix_T.B_U[0]+self.Vmatrix_T.B_V[0])*triv + self.T[0]        
        for i in range(1,self.N-1):            
            aux[i] = self.T[i]            
        aux[self.N-1] = dt*(self.Umatrix_T.B_U[1]+self.Vmatrix_T.B_V[1])*taq  + self.T[self.N-1]
        
        free(self.T)
        #computes T[t+dt]
        self.T = self.A.solve(aux)
        free(aux)
    
    #One Step Heun
    #computes the next T and H at t + dt            
    cdef void OSHeun(self,double t, double dt):
        
        #boundaries parameters
        cdef double hriv0 = self.Hriv.eval(t)
        cdef double haq0 = self.Haq.eval(t)
        cdef double triv0 = self.Triv.eval(t)
        cdef double taq0 = self.Taq.eval(t)
                
        cdef double hriv = self.Hriv.eval(t+dt)
        cdef double haq = self.Haq.eval(t+dt)
        cdef double triv = self.Triv.eval(t+dt)
        cdef double taq = self.Taq.eval(t+dt)
        
        cdef double* aux = <double*> malloc(self.N * sizeof(double))
        cdef int i
        
        cdef double* f = self.Umatrix_H.Umat.dot(self.H)
        
        #hydraulic boundary conditions
        aux[0] = 0.5*dt*self.Umatrix_H.B_U[0]*(hriv0+hriv) + self.H[0] + 0.5*dt*f[0]       
        for i in range(1,self.N-1):            
            aux[i] = self.H[i] + 0.5*dt*f[i]           
        aux[self.N-1] = 0.5*dt*self.Umatrix_H.B_U[1]*(haq0+haq) + self.H[self.N-1] + 0.5*dt*f[self.N-1]
        free(f)
        
        #hydraulic conduction matrix
        self.A.copy(self.Umatrix_H.Umat.mat)
        self.A.scalarmul(-0.5*dt)
        self.A.add(self.I.mat,self.A.mat)
        
        free(self.H)
        #computes H[t+dt]        
        self.H = self.A.solve(aux)
        
        #heat exchange matrix
        self.A.add(self.Umatrix_T.Umat.mat,self.Vmatrix_T.Vmat.mat)
        f = self.A.dot(self.T)
        
        cdef double B_U0 = self.Umatrix_T.B_U[0]
        cdef double B_V0 = self.Vmatrix_T.B_V[0]
        cdef double B_U = self.Umatrix_T.B_U[1]
        cdef double B_V = self.Vmatrix_T.B_V[1]
        
        self.compute_Hz(hriv,haq)
        self.Vmatrix_T.compute(self.Hz)
        self.A.add(self.Umatrix_T.Umat.mat,self.Vmatrix_T.Vmat.mat)
        self.A.scalarmul(-0.5*dt)
        self.A.add(self.I.mat,self.A.mat)
        
        #heat boundary conditions
        aux[0] = 0.5*dt*((B_U0+B_V0)*triv0+(self.Umatrix_T.B_U[0]+self.Vmatrix_T.B_V[0])*triv) + self.T[0] + 0.5*dt*f[0]       
        for i in range(1,self.N-1):            
            aux[i] = self.T[i] + 0.5*dt*f[i]           
        aux[self.N-1] = 0.5*dt*((B_U+B_V)*taq0+(self.Umatrix_T.B_U[1]+self.Vmatrix_T.B_V[1])*taq)  + self.T[self.N-1] + 0.5*dt*f[self.N-1]
        free(f)
        free(self.T)
        #computes T[t+dt]
        self.T = self.A.solve(aux)
        free(aux)
    
    #One Time Solve
    #computes T and H at tf
    def OTSolve(self, double t0, double tf, double dt, bint autostep = False):
        cdef double t = t0
        while t < tf:
            if autostep:
                #adaptive step size parameters
                dt = self.stepscaler(t,dt)
                self.norm_H0 = self.norm_H1
                self.norm_H1 = norm(self.H,self.N,id=self.norm_id)
                self.norm_T0 = self.norm_T1
                self.norm_T1 = norm(self.T,self.N,id=self.norm_id)
            if t + dt > tf:           
                dt = tf - t
                self.OSHeun(t,dt)
                t = tf + 1
            else:
                self.OSHeun(t,dt)
                t = t + dt
                
    cdef void set_H(self,double* H0):
        cdef int i
        for i in range(self.N):
            self.H[i] = H0[i] 
        
    cdef void set_T(self,double* T0):
        cdef int i
        for i in range(self.N):
            self.T[i] = T0[i]
    
    def init_stepscaler(self, double atol_H, double rtol_H, double atol_T, double rtol_T, int norm_id):
        self.norm_id = norm_id
        self.norm_H0 = norm(self.H,self.N,id=norm_id)
        self.norm_T0 = norm(self.T,self.N,id=norm_id)
        self.norm_H1 = self.norm_H0
        self.norm_T1 = self.norm_T0
        self.atol_H = atol_H
        self.rtol_H = rtol_H
        self.atol_T = atol_T
        self.rtol_T = rtol_T
    
    #adapts solver time step    
    def stepscaler(self, double t, double dt):
        
        cdef int i
        cdef double* aux0_H = <double*> malloc(self.N * sizeof(double))
        cdef double* aux0_T = <double*> malloc(self.N * sizeof(double))
        cdef double* aux1_H = <double*> malloc(self.N * sizeof(double))
        cdef double* aux1_T = <double*> malloc(self.N * sizeof(double))

        for i in range(self.N):
            aux0_H[i] = self.H[i]
            aux0_T[i] = self.T[i]
            aux1_H[i] = self.H[i]
            aux1_T[i] = self.T[i]
        
        #computes Euler predictions
        self.OSIEuler(t,dt)
        cdef double* H_IEuler = self.H
        cdef double* T_IEuler = self.T
        
        self.H = aux0_H
        self.T = aux0_T
        self.compute_Hz(self.Hriv.eval(t),self.Haq.eval(t))
        self.Vmatrix_T.compute(self.Hz)
        
        #computes Heun predictions
        self.OSHeun(t,dt)
        cdef double* H_Heun = self.H
        cdef double* T_Heun = self.T
        
        self.H = aux1_H
        self.T = aux1_T
        
        #time step adapted according to the prediction error 
        #error estimated with the difference between Euler and Heun predictions
        cdef double dt_H = dt*((self.atol_H + self.rtol_H*max(self.norm_H0,self.norm_H1)) * distance(H_IEuler,H_Heun,self.N,id=self.norm_id)**(-1))**(0.5)
        cdef double dt_T = dt*((self.atol_T + self.rtol_T*max(self.norm_T0,self.norm_T1)) * distance(T_IEuler,T_Heun,self.N,id=self.norm_id)**(-1))**(0.5)
        
        self.compute_Hz(self.Hriv.eval(t),self.Haq.eval(t))
        self.Vmatrix_T.compute(self.Hz)
        
        free(H_IEuler)
        free(H_Heun)
        free(T_IEuler)
        free(T_Heun)
        
        return min(dt_H,dt_T)
    
    #computes H and T at different times        
    cdef void solve(self, Matrix memo, int ntimes, double* times, double t0, double dt, bint interpol_T = False, bint autostep = False):
        
        cdef double t = t0
        cdef double val, e
        cdef int i, j, a
        
        self.compute_Hz(self.Hriv.eval(t0),self.Haq.eval(t0))
        self.Vmatrix_T.compute(self.Hz)
        
        for i in range(ntimes):
                
            self.OTSolve(t,times[i],dt,autostep = autostep)
            
            #to only store temperatures at measures depths
            if interpol_T:
                for j in range(self.nb_meas):
                    a = self.interpol_index[j]
                    e = self.interpol_weights[j]
                    val = e*self.T[a] + (1-e)*self.T[a+1]
                    memo.set(i,j,val)
                    
            #to keep all temperatures and hydraulic charges
            else:
                memo.slicerowset(i,0,self.N,self.H)
                memo.slicerowset(i,self.N,2*self.N,self.T)
            
            t = times[i]
            
    cdef void free(self, bint interpol_T = False):        
        self.Umatrix_T.free()
        self.Umatrix_H.free()
        self.Vmatrix_T.free()
        self.A.free()
        self.I.free()
        self.geo.free()
        self.params.free()
        self.Hriv.free()
        self.Haq.free()
        self.Triv.free()
        self.Taq.free()
        free(self.Hz)
        free(self.H)
        free(self.T)
        free(self.depths_meas)
        if interpol_T:
            free(self.interpol_index)
            free(self.interpol_weights)
            
#function to call in a python script to test StratifiedModel 
cpdef test_SM(int N,
          double h,
          double[:] Hriv,
          double[:] Haq,
          double[:] Triv,
          double[:] Taq,
          int Ntimes,
          double dt,
          double t0,
          double tf,
          int Nl,
          double[:] borders,
          double[:] depths_meas,
          double[:] Ll,
          double[:] Cl,
          double[:] Kl,
          double[:] Sl,
          double[:] H0,
          double[:] T0,
          int ntimes,
          double[:] times,
          double t02,
          double step,
          double atol_H,
          double rtol_H,
          double atol_T,
          double rtol_T,
          bint interpol_T = False,
          bint autostep = False):
    #conversion of python objects into C objects
    cdef double* Hriv2 = numpy_to_C(Hriv)
    cdef double* Haq2 = numpy_to_C(Haq)
    cdef double* Triv2 = numpy_to_C(Triv)
    cdef double* Taq2 = numpy_to_C(Taq)
    cdef double* borders2 = numpy_to_C(borders)
    cdef double* depths_meas2 = numpy_to_C(depths_meas)
    cdef double* Ll2 = numpy_to_C(Ll)
    cdef double* Cl2 = numpy_to_C(Cl)
    cdef double* Kl2 = numpy_to_C(Kl)
    cdef double* Sl2 = numpy_to_C(Sl)
    cdef double* H02 = numpy_to_C(H0)
    cdef double* T02 = numpy_to_C(T0)
    cdef double* times2 = numpy_to_C(times)
    #solver tool
    cdef StratifiedModel sm = StratifiedModel()
    sm.init(N,h,Hriv2,Haq2,Triv2,Taq2,Ntimes,dt,t0,tf,Nl,borders2,depths_meas2,depths_meas.shape[0])
    sm.update_params(Ll2,Cl2,Kl2,Sl2)
    sm.set_T(T02)
    sm.set_H(H02)
    if autostep:
        sm.init_stepscaler(atol_H,rtol_H,atol_T,rtol_T,2)
    cdef Matrix memo = Matrix()
    if interpol_T:       
        memo.init(ntimes,len(depths_meas))
        sm.prepare_interpol_T()
        sm.solve(memo,ntimes,times2,t02,step,interpol_T=True,autostep=autostep)
        sm.free(interpol_T=True)
    else:
        memo.init(ntimes,2*N)
        sm.solve(memo,ntimes,times2,t02,step,interpol_T=False,autostep=autostep)
        sm.free(interpol_T=False)
    free(times2)
    free(H02)
    free(T02)
    A =  memo.convert_to_numpy()
    memo.free()
    return A

###Bayesian inference

#sets the random seed of rand using the clock
srand(time(NULL))

#uniformly draws a sample from [0,1]
cdef double random_uniform_std():
    cdef double r = rand()
    return (<double> r) * (<double> RAND_MAX)**(-1)

#draws a standard gaussian sample
#uses a polar version of the Box-Muller transformation
cdef double random_normal_std():
    cdef double x1, x2, w
    w = 2.0
    while (w >= 1.0):
        x1 = 2.0 * random_uniform_std() - 1.0
        x2 = 2.0 * random_uniform_std() - 1.0
        w = x1 * x1 + x2 * x2
    w = ((-2.0 * log(w)) * w**(-1)) ** 0.5
    return x1 * w

#uniformly draws a sample from [a,b]
cdef double random_uniform(double a, double b):
    return a + (b-a)*random_uniform_std()

#draws a gaussian sample of law (mean, sigma)
cdef double random_normal(double mean, double sigma):
    return mean + sigma*random_normal_std()

#probability of a set of consecutively numbered events
cdef double slicesum(double* probas, int a, int b):
    cdef double prob = 0
    cdef int i
    for i in range(a,b):
        prob = prob + probas[i]
    return prob

#to efficiently draw a sample from a finite distribution
#the idea: decompose a draw in a sequence of binomial experiments
#in practice, we use a binary tree
cdef class DiscreteRandomVariable:
    cdef int nb_events
    #probabilities
    cdef double* proba
    cdef int tree_depth
    #probabilities tree stored in an array
    cdef double* tree
    cdef int result
    
    cdef void init(self, int nb_events, double* proba):
        self.nb_events = nb_events
        self.proba = proba
        self.tree_depth = 1 + <int> (log(nb_events) * log(2)**(-1))
        self.tree = <double*> malloc((2**(self.tree_depth+1)) * sizeof(double))
    
    #to build the tree
    cdef void update_leaf(self,int a, int b, int id, int level, double previous):
        cdef int m = (b+a)//2
        if level == -1:
            self.tree[0] = 1
        else:
            self.tree[2**(level+1)-1+id] = slicesum(self.proba,a,b) * previous**(-1)
        if b-a>1:
            self.update_leaf(a, m, 2*id, level+1, slicesum(self.proba,a,b))
            self.update_leaf(m, b, 2*id+1, level+1, slicesum(self.proba,a,b))
    cdef void update(self):
        self.update_leaf(0, self.nb_events, 0, -1, 1)
    
    #to use the tree for random generation
    cdef void moove(self, int a, int b, int id, int level):
        cdef int m = (a+b)//2
        cdef double p_left = self.tree[2**(level+2)-1+2*id]
        
        if b-a>1:
            if random_uniform_std()<p_left:
                self.moove(a,m,2*id,level+1)
            else:
                self.moove(m,b,2*id+1,level+1)
        else:
            self.result = a
    cdef int generate(self):
        self.moove(0,self.nb_events,0,-1)
        
    cdef void free(self):
        free(self.tree)

cdef class MCMC:
    cdef int nb_layers
    #total number of parameters (of all layers)
    cdef int nb_params
    #number of Markov chains
    cdef int nb_chains
    #number of random walk steps
    cdef int nb_iter
    #number of ordered pairs
    cdef int nb_opairs
    #number of crossover probabilities
    cdef int nCR
    #number of a state dimensions
    cdef int nb_dim
    #static paremeters for random generation
    cdef double cn
    cdef double c
    cdef double t0
    #boolean arrays to keep track of selected elements (ex:chains or dimensions)
    cdef bint* dim_selector
    cdef bint* aux_selector
    cdef int* opairs_selector
    #ranges of physical parameters
    cdef double* range_L
    cdef double* range_C
    cdef double* range_K
    cdef double* range_S
    cdef double* range_sigma
    #layers parameters
    cdef double* Ll
    cdef double* Cl
    cdef double* Kl
    cdef double* Sl
    #measure times
    cdef double* times
    #crossover probabilities
    cdef double* probas
    #records the random walk
    cdef Matrix past
    #stores real physical measures
    cdef Matrix meas
    #stores current temperature predictions given by SM
    cdef Matrix pred
    #stores chain energies
    cdef Matrix energy
    cdef StratifiedModel sm
    
    cdef void init(self,
                   StratifiedModel sm,
                   int nb_chains,
                   int nb_iter,
                   Matrix meas,
                   double* times,
                   double t0,
                   double cn, double c,
                   int nb_opairs,
                   int nCR,
                   double* range_L,
                   double* range_C,
                   double* range_K,
                   double* range_S,
                   double* range_sigma):  
        self.nb_iter = nb_iter
        self.times = times
        self.t0 = t0
        self.sm = sm
        self.nb_layers = sm.params.Nl
        self.nb_params = 4*sm.params.Nl+1
        self.nb_chains = nb_chains
        self.past = Matrix()
        self.past.init(nb_iter, self.nb_params * nb_chains)
        self.meas = meas
        self.pred = Matrix()
        self.pred.init(meas.n,meas.m)
        self.cn = cn
        self.c = c
        self.nb_opairs = nb_opairs
        self.nCR = nCR
        self.probas = <double*> malloc(nCR * sizeof(double))
        self.range_L = range_L
        self.range_C = range_C
        self.range_K = range_K
        self.range_S = range_S
        self.range_sigma = range_sigma
        self.energy = Matrix()
        self.energy.init(nb_iter,nb_chains)
        self.dim_selector = <bint*> malloc(self.nb_params * sizeof(bint))
        self.opairs_selector = <int*> malloc(2*nb_opairs * sizeof(int))
        self.aux_selector = <bint*> malloc(nb_chains * sizeof(bint))
        self.Ll = <double*> malloc(self.nb_layers * sizeof(double))
        self.Cl = <double*> malloc(self.nb_layers * sizeof(double))
        self.Kl = <double*> malloc(self.nb_layers * sizeof(double))
        self.Sl = <double*> malloc(self.nb_layers * sizeof(double))
    
    #assigns parameter j of chain i at given time
    cdef void set_chain_param(self, int time, int i, int j, double val):       
        self.past.set(time, i * self.nb_params + j, val)
    
    #returns parameter j of chain i at given time
    cdef double get_chain_param(self, int time, int i, int j):       
        return self.past.get(time, i * self.nb_params + j)
    
    #updateq layer parameters
    cdef void params_for_SM(self,int time, int id_chain):
        cdef int i
        for i in range(self.nb_layers):
            #conductivity
            self.Ll[i] = self.get_chain_param(time, id_chain, 4*i + 1)
            #thermal capacity
            self.Cl[i] = self.get_chain_param(time, id_chain, 4*i + 2)
            #permeability
            self.Kl[i] = self.get_chain_param(time, id_chain, 4*i + 3)
            #hydraulic capacity
            self.Sl[i] = self.get_chain_param(time, id_chain, 4*i + 4)
    
    cdef void init_chains(self):
        cdef int i, j
        cdef double sigma, L, C, K, S
        for i in range(self.nb_layers):
            for j in range(self.nb_chains):
                #sigma
                sigma = random_uniform(self.range_sigma[0],self.range_sigma[1])
                self.set_chain_param(0, j, 0, sigma)
                #conductivity
                L = random_uniform(self.range_L[2*i],self.range_L[2*i+1])
                self.set_chain_param(0, j, 4*i + 1, L)
                #thermal capacity
                C = random_uniform(self.range_C[2*i],self.range_C[2*i+1])
                self.set_chain_param(0, j, 4*i + 2, C)
                #permeability
                K = random_uniform(self.range_K[2*i],self.range_K[2*i+1])
                self.set_chain_param(0, j, 4*i + 3, K)
                #hydraulic capacity
                S = random_uniform(self.range_S[2*i],self.range_S[2*i+1])
                self.set_chain_param(0, j, 4*i + 4, S)
    
    #keeps chains within the bounded domain defined by parameters ranges            
    cdef void mod(self, int time, int id_chain):
        cdef int i
        cdef double sigma, L, C, K, S, r, frac
        cdef int n
        cdef int j = id_chain
        for i in range(self.nb_layers):
            #sigma
            sigma = self.get_chain_param(time, j, 0)
            r = abs(sigma - self.range_sigma[2*i]) * (self.range_sigma[2*i+1] - self.range_sigma[2*i])**(-1)
            n = <int> r
            frac = r - n
            sigma = self.range_sigma[2*i] + frac*(self.range_sigma[2*i+1] - self.range_sigma[2*i])
            self.set_chain_param(time, j, 0, sigma)
            #conductivity
            L = self.get_chain_param(time, j, 4*i + 1)
            r = abs(L - self.range_L[2*i]) * (self.range_L[2*i+1] - self.range_L[2*i])**(-1)
            n = <int> r
            frac = r - n
            L = self.range_L[2*i] + frac*(self.range_L[2*i+1] - self.range_L[2*i])
            self.set_chain_param(time, j, 4*i + 1, L)
            #thermal capacity
            C = self.get_chain_param(time, j, 4*i + 2)
            r = abs(C - self.range_C[2*i]) * (self.range_C[2*i+1] - self.range_C[2*i])**(-1)
            n = <int> r
            frac = r - n
            C = self.range_C[2*i] + frac*(self.range_C[2*i+1] - self.range_C[2*i])
            self.set_chain_param(time, j, 4*i + 2, C)
            #permeability
            K = self.get_chain_param(time, j, 4*i + 3)
            r = abs(K - self.range_K[2*i]) * (self.range_K[2*i+1] - self.range_K[2*i])**(-1)
            n = <int> r
            frac = r - n
            K = self.range_K[2*i] + frac*(self.range_K[2*i+1] - self.range_K[2*i])
            self.set_chain_param(time, j, 4*i + 3, K)
            #hydraulic capacity
            S = self.get_chain_param(time, j, 4*i + 4)
            r = abs(S - self.range_S[2*i]) * (self.range_S[2*i+1] - self.range_S[2*i])**(-1)
            n = <int> r
            frac = r - n
            S = self.range_S[2*i] + frac*(self.range_S[2*i+1] - self.range_S[2*i])
            self.set_chain_param(time, j, 4*i + 4, S)
    
    #init with approximated hydraulic steady state solution
    cdef void init_H(self):
        
        cdef int i
        cdef double Itot = 0
        for i in range(self.sm.N):
            Itot = Itot + self.sm.geo.width[i] * self.sm.params.K[i]**(-1)
        cdef double Hz0 = (self.sm.Haq.eval(self.t0) - self.sm.Hriv.eval(self.t0)) * Itot**(-1)
            
        self.sm.H[0] = self.sm.Hriv.eval(self.t0) + Hz0 * self.sm.geo.width[0] * self.sm.params.K[0]**(-1)
        for i in range(1,self.sm.N):
            self.sm.H[i] = self.sm.H[i-1] + Hz0 * self.sm.geo.width[i] * self.sm.params.K[i]**(-1)
    
    #init with approximated thermal steady state solution
    cdef void init_T(self):
        
        cdef int i
        cdef double* exponan = <double*> malloc(self.sm.N * sizeof(double))
        cdef double Itot = 0
        cdef double cw = self.sm.Vmatrix_T.cw
        cdef double rhow = self.sm.Vmatrix_T.rhow
        
        exponan[0] = self.sm.geo.width[0]*(cw*rhow*self.sm.params.K[0]*(self.sm.H[0]-self.sm.Hriv.eval(self.t0))
                      *(self.sm.geo.spacing[0]*self.sm.params.L[0])**(-1))
                      
        for i in range(1,self.sm.N):
            exponan[i] = exponan[i-1] + self.sm.geo.width[i]*(cw*rhow*self.sm.params.K[i]*(self.sm.H[i]-self.sm.H[i-1])
                                         *(self.sm.geo.spacing[i]*self.sm.params.L[i])**(-1))
            
        for i in range(self.sm.N):
            Itot = Itot + self.sm.geo.width[i] * exp(-exponan[i])
            
        cdef double Tz0 = (self.sm.Taq.eval(self.t0) - self.sm.Triv.eval(self.t0)) * Itot**(-1)
                    
        self.sm.T[0] = self.sm.Triv.eval(self.t0) + Tz0 * self.sm.geo.width[0] * exp(-exponan[0])
        
        for i in range(1,self.sm.N):
            self.sm.T[i] = self.sm.T[i-1] + Tz0 * self.sm.geo.width[i] * exp(-exponan[i])
            
        free(exponan)
    
    #init crossover probabilities
    cdef void init_probas(self):
        cdef int i
        for i in range(self.nCR):
            self.probas[i] = (<double> self.nCR)**(-1)
    
    cdef void predict(self, bint autostep = False, double dt = 300):
        self.sm.solve(self.pred,self.meas.n,self.times,self.t0,dt,interpol_T=True,autostep=autostep)
        
    cdef void compute_energy(self, int time, int id_chain):
        cdef double e = 0
        cdef int i, j
        cdef double sigma = self.get_chain_param(time,id_chain,0)
        for i in range(self.meas.n):
            for j in range(self.meas.m):
                e = e + (self.meas.get(i,j) - self.pred.get(i,j))**2
        self.energy.set(time,id_chain, 0.5*e*sigma**(-2)+self.meas.n*self.meas.m*log(sigma))    
    
    cdef double compute_acceptancy(self, int time, int id_chain):
        cdef double e0 = self.energy.get(time-1,id_chain)
        cdef double e1 = self.energy.get(time,id_chain)
        if e1<=e0:
            return 1
        else:
            return exp(e0-e1)
    
    #select crossover dimensions
    cdef void crossover(self):
        
        cdef int a = 0
        cdef int b = self.nCR
        cdef int m, i
        cdef double rnd, ceil
        cdef bint onetrue = False
        
        #rmk: instead you could use DiscreteRandomVariable to replace this loop
        while b-a > 1:
            m = (a+b)//2
            p = slicesum(self.probas,a,m)*(slicesum(self.probas,a,b))**(-1)
            rnd = random_uniform_std()
            if rnd < p:
                b = m
            else:
                a = m
        ceil = (a + 1) * self.nCR**(-1)
        
        self.nb_dim = 0
        for i in range(self.nb_params):
            rnd = random_uniform_std()
            if rnd < ceil:
                self.dim_selector[i] = True
                onetrue = True
                self.nb_dim = self.nb_dim + 1
            else:
                self.dim_selector[i] = False
                
        if not onetrue:
            rnd = self.nb_params * random_uniform_std()
            self.dim_selector[<int> rnd] = True
            self.nb_dim = 1
            
    cdef void opairs_selection(self):
        
        cdef int i, j
        for i in range(self.nb_chains):
            self.aux_selector[i] = True
        
        for i in range(self.nb_opairs):
            
            j = <int> (self.nb_chains * random_uniform_std())
            while not self.aux_selector[j]:
                j = j + 1
                if j > self.nb_chains-1:
                    j = 0
            self.opairs_selector[2*i] = j
            self.aux_selector[j] = False

            j = <int> (self.nb_chains * random_uniform_std())
            while not self.aux_selector[j]:
                j = j + 1
                if j > self.nb_chains-1:
                    j = 0
            self.opairs_selector[2*i+1] = j
            self.aux_selector[j] = False
    
    #random generators used in DREAMS            
    cdef double alpha(self):
        return random_normal(0,self.cn)
    cdef double beta(self,double gamma = 2.38*2**(-0.5)):
        cdef double inf = (1-self.c)*gamma*(self.nb_opairs*self.nb_dim)**(-0.5)
        cdef double sup = (1+self.c)*gamma*(self.nb_opairs*self.nb_dim)**(-0.5)
        return random_uniform(inf,sup)
    
    #new chain state generation            
    cdef void generate(self,int time, int id_chain):
        cdef int i,j
        cdef double a, b, s
        cdef int id1, id2
        for i in range(self.nb_params):
            s = 0
            if self.dim_selector[i]:
                a = self.alpha()
                b = self.beta()
                for j in range(self.nb_opairs):
                    id1 = self.opairs_selector[2*j]
                    id2 = self.opairs_selector[2*j+1]
                    s = s + self.get_chain_param(time,id2,i) - self.get_chain_param(time,id1,i)
                s = a + b*s
            s = s + self.get_chain_param(time,id_chain,i)
            self.set_chain_param(time+1,id_chain,i,s)
    
    #when new chain state is not accepted, rewrites the previous one
    cdef void rewrite(self,int time, int id_chain):
        cdef int i
        cdef double past_val
        for i in range(self.nb_params):
            past_val = self.get_chain_param(time-1,id_chain,i)
            self.set_chain_param(time,id_chain,i,past_val)
    
    #rmk: to rigorously respect symmetric increments
    #you should modify the last two intricated loops
    cdef void walk(self,bint autostep=False):
        
        cdef int i, k
        cdef double rnd
        cdef double accept = 0
        self.init_chains()
        self.init_probas()
        for i in range(self.nb_chains):
            self.params_for_SM(0,i)
            self.sm.update_params(self.Ll,self.Cl,self.Kl,self.Sl)
            self.init_H()
            self.init_T()
            self.predict(autostep=autostep)
            self.compute_energy(0,i)
        
        for k in range(self.nb_iter-1):
            for i in range(self.nb_chains):
                self.crossover()
                self.opairs_selection()
                self.generate(k,i)
                self.mod(k+1,i)
                self.params_for_SM(k+1,i)
                self.sm.update_params(self.Ll,self.Cl,self.Kl,self.Sl)
                self.init_H()
                self.init_T()
                self.predict(autostep=autostep)
                self.compute_energy(k+1,i)
                accept = self.compute_acceptancy(k+1,i)
                rnd = random_uniform_std()
                if rnd > accept:
                    self.rewrite(k+1,i)
                    
    cdef void free(self):
        self.sm.free()
        self.past.free()
        self.pred.free()
        self.energy.free()
        free(self.probas)
        free(self.range_L)
        free(self.range_C)
        free(self.range_K)
        free(self.range_S)
        free(self.range_sigma)
        free(self.times)
        free(self.dim_selector)
        free(self.opairs_selector)
        free(self.aux_selector)
        
#function to call in a python script to test StratifiedModel 
def test_MCMC(int N,
          double h,
          double[:] Hriv,
          double[:] Haq,
          double[:] Triv,
          double[:] Taq,
          int Ntimes,
          double dt,
          double t0,
          double tf,
          int Nl,
          double[:] borders,
          double[:] depths_meas,
          int nb_chains,
          int nb_iter,
          int nb_layers,
          double[:, ::1] meas,
          double[:] times,
          double t0_solve,
          double cn,
          double c,
          int nb_opairs,
          int nCR,
          double[:] range_L,
          double[:] range_C,
          double[:] range_K,
          double[:] range_S,
          double[:] range_sigma,
          double atol_H,
          double rtol_H,
          double atol_T,
          double rtol_T,
          bint autostep = False):
    
    #conversion to C arrays
    cdef double* Hriv_C = numpy_to_C(Hriv)
    cdef double* Haq_C = numpy_to_C(Haq)
    cdef double* Triv_C = numpy_to_C(Triv)
    cdef double* Taq_C = numpy_to_C(Taq)
    cdef double* borders_C = numpy_to_C(borders)
    cdef double* depths_meas_C = numpy_to_C(depths_meas)
    cdef Matrix meas_C = Matrix()
    meas_C.init(meas.shape[0],meas.shape[1])
    meas_C.extract_from_numpy(meas)
    cdef double* times_C = numpy_to_C(times)
    cdef double* range_L_C = numpy_to_C(range_L)
    cdef double* range_C_C = numpy_to_C(range_C)
    cdef double* range_K_C = numpy_to_C(range_K)
    cdef double* range_S_C = numpy_to_C(range_S)
    cdef double* range_sigma_C = numpy_to_C(range_sigma)
    
    #physical model
    cdef StratifiedModel sm = StratifiedModel()
    sm.init(N,h,Hriv_C,Haq_C,Triv_C,Taq_C,Ntimes,dt,t0,tf,Nl,borders_C,depths_meas_C,depths_meas.shape[0])
    if autostep:
        sm.init_stepscaler(atol_H,rtol_H,atol_T,rtol_T,2)
    sm.prepare_interpol_T()
    
    #MCMC random walk
    cdef MCMC mcmc = MCMC()
    mcmc.init(sm,nb_chains,nb_iter,meas_C,times_C,t0_solve,cn,c,nb_opairs,nCR,range_L_C,range_C_C,range_K_C,range_S_C,range_sigma_C)
    mcmc.walk(autostep=autostep)
    
    return mcmc.past.convert_to_numpy()
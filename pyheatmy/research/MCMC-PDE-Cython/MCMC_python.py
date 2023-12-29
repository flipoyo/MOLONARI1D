import numpy as np
import matplotlib.pyplot as plt

##Elementary functions

def generate_uncorrelated_multivariate_normal(sigmas:np.array):
    Y = np.empty(len(sigmas))
    for i in range(len(sigmas)):
        Y[i] = np.random.normal(loc=0,scale=sigmas[i])
    return Y

def is_valid(D:np.array,
             Y:np.array):
    return np.all((D[:,0]<=Y)*(Y<=D[:,1]))

def energy(X:np.array,
          Ymeas:np.array,
          F,
          sigma:float):

    if sigma > 0:
        return np.sum((Ymeas-F(X))**2)/(2*sigma**2)
    else:
        sigma = X[-1]
        logsigma = len(Ymeas)*np.log(X[-1])
        return np.sum((Ymeas-F(X[:-1]))**2)/(2*sigma**2)+logsigma

def acceptancy(X0:np.array,
               X1:np.array,
               D:np.array,
               Ymeas:np.array,
               F,
               sigma:float):

    if is_valid(D,X1):

        eX0 = energy(X0,Ymeas,F,sigma)
        eX1 = energy(X1,Ymeas,F,sigma)

        if eX1<=eX0:
            return 1
        else:
            return np.exp(eX0-eX1)

    return 0

##DREAMS

def walk(Xall,D,Ymeas,sigma,F,nb_iter,pi,cn,c,Psize,gamma=2.38/(2)**(0.5)):

    past = np.empty((nb_iter,len(Xall)*len(Xall[0])))

    indices = make_indices(len(Xall[0]),pi)
    alpha = make_alpha(cn)
    beta = make_beta(c,Psize,gamma)
    pairs = make_pairs(len(Xall),Psize)

    for i in range(nb_iter):

        chain_id = i%len(Xall)
        Xp = propose(Xall,chain_id,D,Ymeas,F,alpha,beta,indices,pairs)
        p_accept = acceptancy(Xall[chain_id],Xp,D,Ymeas,F,sigma)

        if (np.random.random()<p_accept):
            Xall[chain_id] = Xp
            past[i,:] = Xall.reshape(len(Xall)*len(Xall[0]))
        else:
            past[i,:] = Xall.reshape(len(Xall)*len(Xall[0]))

    return past

def propose(Xall,chain_id,D,Ymeas,F,alpha,beta,indices,pairs):

    I = indices()
    a = alpha(len(I))
    b = beta(len(I))
    P = pairs(chain_id)
    SP = pairs_sum(Xall,P)

    dX = np.zeros(len(Xall[chain_id]))

    for i,index in enumerate(I):

        dX[index] = a[i] + b[i]*SP[index]

    Xp = D[:,0] + np.mod(Xall[chain_id] + dX - D[:,0],D[:,1]-D[:,0])

    return Xp

def make_indices(d,pi):

    def indices():

        sizes = np.random.multinomial(1,pi)

        for size in range(len(pi)):
            if sizes[size]==1:
                m = (size+1)/len(pi)
                break

        I = []
        for i in range(len(pi)):
            if np.random.random()<m:
                I.append(i)
        if I == []:
            I.append(int(np.random.random()*len(pi)))

        return np.array(I)

    return indices

def make_alpha(cn):

    def alpha(Isize):
        return np.random.normal(loc=0,scale=cn,size=Isize)

    return alpha

def make_beta(c,Psize,gamma):

    def beta(Isize):

        inf = (1-c)*gamma/(Psize*Isize)**(0.5)
        sup = (1+c)*gamma/(Psize*Isize)**(0.5)

        return np.random.uniform(low=inf,high=sup,size=Isize)

    return beta

def make_pairs(N,nb_pairs):

    tab = np.empty((N*(N-1)//2,2))
    for i in range(N):
        for j in range(i):
            tab[i*(i-1)//2+j] = np.array([i, j])

    def pairs(id_chain):

        choices = np.random.randint(0,(N-1)*(N-2)//2,size=nb_pairs)

        couples = np.empty((nb_pairs,2))

        for i in range(nb_pairs):

            a,b = tab[choices[i]]

            if a >= id_chain:
                a = a + 1
            if b >= id_chain:
                b = b + 1

            if np.random.random()<0.5:

                couples[i,0] = a
                couples[i,1] = b

            else:
                couples[i,0] = b
                couples[i,1] = a

        return couples

    return pairs

def pairs_sum(Xall,P):

    S = np.zeros(len(Xall[0]))

    for p in range(len(P)):

        S = S + Xall[int(P[p,0])]-Xall[int(P[p,1])]

    return S

def init(D):
    X = np.empty(len(D))
    for i in range(len(D)):
        X[i] = np.random.uniform(D[i][0],D[i][1])
    return X

##Test

F = lambda x : x**2
D = np.array([[-2,2]])
sigma = 0.1
Ymeas = np.array([1]) + np.random.normal(loc=0,scale=sigma,size=1)

N = 30
cn = 0.01
c = 0.1
Psize = 10
pi = np.ones(1)
Xall = np.array([init(D) for _ in range(N)])
nb_iter = 1000

past = walk(Xall,D,Ymeas,sigma,F,nb_iter,pi,cn,c,Psize)

past = past.reshape((nb_iter*N))

plt.hist(past,bins=100,density=True)
plt.axvline(x=1,color='red',label='expected solutions')
plt.axvline(x=-1,color='red')
plt.xlabel('x')
plt.ylabel('density')
plt.legend()
plt.show()
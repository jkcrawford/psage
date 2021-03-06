from sage.all import *
from psage import *
import mpmath
from psage.matrix import Matrix_complex_dense
from psage.modform.maass.pullback_algorithms import pullback_pts_mp #,pullback_pts_mp_sym
from psage.modform.maass.automorphic_forms_alg import check_principal_parts
from psage.modform.maass.automorphic_forms import solve_system_for_harmonic_weak_Maass_waveforms,smallest_inf_norm
from psage.modform.maass.linear_system import *
import pstats, cProfile
def setup_harmonic_matrix(S,pp,Y,M0,setc=None,ret_pb=0):
    r"""
    MxM system for Harmonic weak Maass forms at Y=Y with weight k
    """
    Q = M0+10; Qs=1-Q; Qf = Q
    Ql = Qf-Qs + 1
    prec = Y.parent().prec()
    mpmath.mp.prec=prec
    X = S.multiplier()
    RF = RealField(prec)
    CF = MPComplexField(prec)
    pb = pullback_pts_mp(S,Qs,Qf,Y)
    if ret_pb==1:        
        return pb
    xm = pb['xm']; xpb=pb['xpb']; ypb=pb['ypb']; cvec=pb['cvec']
    verbose = S._verbose
    if S._verbose>0:
        print "Cvec[0,1,0]=",cvec.get(0,{}).get(1,{}).get(0,{})    
        print "Ypb[0,1,0]=",ypb.get(0,{}).get(1,{}).get(0,{})    
    sz = (2*M0+1)*S.group().ncusps()
    V = Matrix_complex_dense(MatrixSpace(CF,sz,sz),0)
    RHS = Matrix_complex_dense(MatrixSpace(CF,sz,1),0)
    nc = S.group().ncusps()
    k = S.weight()
    km1 = 1-k
    twopi=RF.pi()*RF(2)
    pp_info = check_principal_parts(H,[pp])
    if S._holomorphic==1:
        Ms=0; Mf=M0
    else:
        Ms=-M0; Mf=M0
    Ml=Mf-Ms+1
    f1d = {}
    f2d = {}
    for l in range(Ms,Mf+1):
        f2d[l]={}
        #f1d[l]={}
        for icusp in range(nc):
            #f1d[l][icusp]={};
            f2d[l][icusp]={}
            lr = RF(l + S.alpha(icusp)[0])
            for j in range(Ql):
                f2d[l][icusp][j]=CF(0,-xm[j]*lr).exp()
                #for jcusp in range(nc):
                #    f1d[l][icusp][jcusp]={}
                #    for j in range(Ql):
                #        f1d[l][icusp][jcusp][j]=CF(0,lr*xpb[icusp][jcusp][j]).exp()
    ymax = 0
    xdmax=0
    Q0 = 0; Q1 = Ql
    for l in range(Ms,Mf+1):
        for jcusp in range(nc):
            lj = l-Ms+jcusp*Ml
            lr = RF(l + S.alpha(jcusp)[0])
            if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==0 and int(pp_info['variable_a0_minus'][0][jcusp])==0:
                continue
            for icusp in range(nc):
                for j in range(Q0,Q1):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    #print "ypb=",icusp,jcusp,j,":",ypb[icusp][jcusp][j]
                    f11 = CF(1)
                    if lr>0:
                        f11 = (-twopi*lr*ypb[icusp][jcusp][j]).exp()
                        bes = CF(1)
                    elif lr<0:
                        f11 = (-twopi*lr*ypb[icusp][jcusp][j]).exp()
                        arg = RF.pi()*RF(4)*abs(lr)*ypb[icusp][jcusp][j]
                        bes = RF(mpmath.mp.gammainc(km1,arg))
                        if S._verbose>3 and icusp == 1 and l==Ms:
                            print "arg[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,arg)
                    elif lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                        bes = RF(1)
                    elif lr==0 and int(pp_info['variable_a0_minus'][0][jcusp])==1:
                        if k==1:
                            bes = ypb[icusp][jcusp][j].log()
                        else:
                            bes = ypb[icusp][jcusp][j]**RF(1-k)
                    else:
                        ## In this case we should have simply skipped this
                        bes = RF(0)
                    #f1 = f1d[l][icusp][jcusp][j]*cvec[icusp][jcusp][j]
                    #f1 = f1*cvec[icusp][jcusp][j]
                    #if use_sym == 0: 
                    f1 = CF(0,lr*xpb[icusp][jcusp][j]).exp()
                    cv = cvec[icusp][jcusp][j]
                    #else:
                    #    f1 = RF(2)*RF(lr*xpb[icusp][jcusp][j]).cos()
                    #    cv = cvec[icusp][jcusp][j]+cvec[icusp][jcusp][2*Q-1-j]
                    if S._verbose>3 and icusp == 1 and l==Ms:
                        print "f1[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,f1*f11)
                        print "be[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,bes)
                    bes = bes*f11  
                    for n in range(Ms,Mf+1):
                        nr = RF(n)+S.alpha(icusp)[0]
                        #f2 = CF(0,-xm[j]*nr).exp()
                        ni = n-Ms+icusp*(2*M0+1)
                        vtmp = f1*cv*bes*f2d[n][icusp][j]
                        #if abs(vtmp)<2.**(1-prec):
                        #    print "vtm=",f1,":",f2,":",bes
                        V[ni,lj]+=vtmp
                        if S._verbose>2 and ni==0 and lj==11:
                            print "-------------------"
                            print "V[1,1](",j,")=",V[ni,lj]
                            print "ef1(",j,")=",f1*cv*f2d[n][icusp][j]
                            #print "cv(",j,")=",cv
                            #print "ef2(",j,")=",f2d[n][icusp][j]
    Qfak = RF(1)/RF(2*Q)
    if verbose>0:
        print "V[0,0]0=",V[0,0]
        print "V[1,0]0=",V[1,0]
        print "V[0,1]0=",V[0,1]
        print "V[1,1]0=",V[1,1]
        if V.nrows()>11:
            print "V[0,11] 1=",V[0,11]
        if V.nrows()>16:
            print "V[16,16] 1=",V[16,16]
        print "Y=",Y
        print "Q=",Q
    for n in range(V.nrows()):
        for l in range(V.ncols()):
            V[n,l]=V[n,l]*Qfak
            #print "V[0,11] 1=",V[0,11]
    if verbose>0:
        print "V[0,0]1=",V[0,0]
        print "V[1,0]1=",V[1,0]
        print "V[0,1]1=",V[0,1]
        print "V[1,1]1=",V[1,1]
        print "pp_info=",pp_info
    ## Setting up the right hand side and subtracting left-hand side
    pp_plus = pp_info['PPplus'][0]
    pp_minus = pp_info['PPminus'][0]
    for n in range(Ms,Mf+1):
        for icusp in range(nc):
            #print "n,icusp=",n,icusp
            nr = RF(n)+S.alpha(icusp)[0]
            ni = n -Ms + icusp*(2*M0+1)
            if nr>0:
                bes = RF(-Y*twopi*nr).exp()
            elif nr<0:
                arg = RF.pi()*RF(4)*abs(nr)*Y
                bes = RF(-Y*twopi*nr).exp()
                bes = bes*RF(mpmath.mp.gammainc(km1,arg))
                #bes = RF(bes)
                #bes = incomplete_gamma(km1,arg)
            elif nr==0 and int(pp_info['variable_a0_plus'][0][icusp])==1:
                bes = RF(1)
            elif nr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                if k==1:
                    bes = Y.log()
                else:
                    bes = Y**RF(1-k)
            else:
                bes = 0
            #if ni==1 or ni==16 and S._verbose>0:
            #    print "ni=",ni
            #    print "nr=",nr
            #    print "bes(1)=",bes
            V[ni,ni]-=bes
                #raise ArithmeticError,"a0 not correct set!"
            if verbose>1:
                print "n=",n
            for jcusp,l in pp_plus.keys():
                ppc = CF(pp_plus[(jcusp,l)])
                lr = RF(l)+S.alpha(jcusp)[0]
                if verbose>1:
                    print "l=",l
                summa = CF(0)
                if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                    continue
                #print "MAking RHS! with l,jcusp=",l,jcusp
                for j in range(Ql):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if lr<0:
                        bes = RF(-y*twopi*lr).exp()
                    elif lr==0:
                        bes = RF(1)
                    else:
                        raise ArithmeticError,"This princpal part should be holomorphic!"
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j]
                    f2 = CF(0,arg).exp()
                    tmpc = bes*f2*cvec[icusp][jcusp][j]
                    if verbose>4:
                        print "tmpc = (",j,")",y,bes,"*",f2,"*",cvec[icusp][jcusp][j],"=",tmpc
                    summa = summa + tmpc
                if verbose>1:
                    print "MAking RHS! summma = ",summa
                summa = summa*Qfak
                RHS[ni,0] = RHS[ni,0] + summa*ppc
                if l==n and icusp==jcusp:
                    if verbose>0:
                        print "Subtract! ni,n,nr=",ni,n,nr
                        print "ppc=",ppc
                    if nr<0:
                        bes = RF(-Y*twopi*nr).exp()
                        RHS[ni,0] = RHS[ni,0] - bes*ppc
                    else:
                        if nr==0 and pp_info['variable_a0_plus'][0][icusp]==0:
                            bes = RF(1)
                            RHS[ni,0] = RHS[ni,0] - bes*ppc
            # Set the non-holomorphic principal part
            for jcusp,l in pp_minus.keys():
                ppc = pp_minus[(jcusp,l)]
                lr = RF(l)+S.alpha(jcusp)[0]
                summa = 0
                if ppc==0:
                    continue
                if lr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                    continue
                if lr<>0:
                    raise NotImplementedError,"Only implemented n=0 in non-holom. principal part!"
                for j in range(Ql):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if k==1:
                        bes = y.log()
                    else:
                        bes = y**RF(1-k)
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j]
                    f2 = CF(0,arg).exp()
                    tmpc = bes*f2*cvec[icusp][jcusp][j]
                    summa += tmpc
     
                summa = summa*ppc*Qfak
                RHS[ni,0] +=summa                                
                if l==n and icusp==jcusp:
                    if k==1:
                        bes = Y.log()
                    else:
                        bes = Y**RF(1-k)
                    RHS[ni,0] -= bes*ppc
    if verbose>0:
        print "ymax = ",ymax

    if setc==None:
        return V,RHS
    W={}
    W['V']=V
    W['RHS']=RHS
    W['space']=S
    W['Ms']=-M0;    W['Mf']=M0
    W['Ml']=2*M0+1
    W['rdim']=1
    W['pp']=pp
    W['nc']=S.group().ncusps()
    W['var_a+']=pp_info['variable_a0_plus']
    W['var_a-']=pp_info['variable_a0_minus']
 
    N = S.set_normalization([setc])
    
    C=solve_system_for_harmonic_weak_Maass_waveforms(W,N)
    return C


def solve_system_for_harmonic_weak_Maass_waveforms(W,N):
    r"""
    Solve the linear system to obtain the Fourier coefficients of Maass forms

    INPUT:

    - ``W`` --   (system) dictionary
        - ``W['Ms']``  -- M start
        - ``W['Mf']``  -- M stop
        - ``W['nc']``  -- number of cusps
        - ``W['space']``  -- space of automorphic forms
        - ``W['V']``   -- matrix of size ((Ms-Mf+1)*nc)**2
        - ``W['RHS']`` -- right hand side (for inhomogeneous system) matrix of size ((Ms-Mf+1)*nc)*(dim)
    - ``N`` -- normalisation (dictionary, output from the set_norm_for_maass function)
        - ``N['SetCs']``   -- Which coefficients are set and their values
        - ``N['comp_dim']``-- How large is the assumed dimension of the solution space
        - ``N['num_set']`` -- Number of coefficients which are set
        

    OUTPUT:
    
    - ``C`` -- Fourier coefficients

    EXAMPLES::

        sage: G=MySubgroup(Gamma0(1))
        sage: mpmath.mp.dps=20
        sage: R=mpmath.mpf(9.533695261353557554344235235928770323821256395107251982375790464135348991298347781769255509975435366)
        sage: Y=mpmath.mpf(0.5)
        sage: W=setup_matrix_for_Maass_waveforms(G,R,Y,12,22)
        sage: N=set_norm_maass(1)
        sage: C=solve_system_for_Maass_waveforms(W,N)
        sage: C[0][2]*C[0][3]-C[0][6]
        mpc(real='-1.8055426724989656270259e-14', imag='1.6658248366482944572967e-19')

    If M is too large and the precision is not high enough the matrix might be numerically singular

        W=setup_matrix_for_Maass_waveforms(G,R,Y,20,40)  
        sage: C=solve_system_for_Maass_waveforms(W,N)
        Traceback (most recent call last)
        ...
        ZeroDivisionError: Need higher precision! Use > 23 digits!

    Increasing the precision helps
    
        sage: mpmath.mp.dps=25
        sage: R=mpmath.mpf(9.533695261353557554344235235928770323821256395107251982375790464135348991298347781769255509975435366)
        sage: C=solve_system_for_Maass_waveforms(W,N)
        sage: C[0][2]*C[0][3]-C[0][6]
        mpc(real='3.780824715556976438911480324e-25', imag='2.114746048869188750991752872e-99')


        """
    V=W['V']
    Ms=W['Ms']
    Mf=W['Mf']
    nc=W.get('nc',1)
    PP=W.get('PP',[])
    H = W.get('space',None)
    if not H:
        raise TypeError,"Need a space together with our W!"
    verbose = H._verbose
    #alphas=W['alphas']
    alphas = H.alphas()
    Ml=W['Ml'] #Mf-Ms+1
    variable_a_plus=W['var_a+']
    variable_a_minus=W['var_a-']
    if(V.ncols()<>Ml*nc or V.nrows()<>Ml*nc):
        raise Exception," Wrong dimension of input matrix!"
    # we have to assume that all normalizations use the same coefficients
    maxit=1000
    SetCs=N['SetCs']
    SetCs_neg=N.get('SetCs_neg',{})
    CF = MPComplexField(H.prec())
    zero = CF(0)
    comp_dim=N['comp_dim']
    use_sym=0
    SetClist=dict()
    for j in range(0,comp_dim):
        SetClist[j]=dict()
    if len(PP)>0 and ((comp_dim<>len(SetCs.keys()) and comp_dim<>len(PP))):
        print "comp_dim=",comp_dim
        print "SetC=",SetCs
        print "PP=",PP
        raise ValueError," Inconsistent normalization SetCs:%s" % SetCs
    num_set=0
    for j in range(0,comp_dim):
        # # First we treat set values of coefficients not corresponsing to the principal part
        for (r,n) in SetCs[j].keys():
            nr = r*Ml+n
            if nr>=0 or not H.is_holomorphic():
                SetClist[j][nr]=SetCs[j][(r,n)]
            elif PP[j]['+'].has_key((r,n)) and PP[j]['-'].has_key((r,n)):
                SetClist[j][nr]=0
        if verbose>0:
            print "SetClist_pos=",SetClist
            print "var_a+=",variable_a_plus[j]
            print "var_a-=",variable_a_minus[j]
        ## Then we check the zeroth coefficients
        for r in range(nc):
            if(alphas[r][1]==1):
                if( (not variable_a_plus[j][r]) and (not variable_a_minus[j][r])):
                    nr = r*Ml
                    if(SetCs_neg.get(j,{}).has_key((r,0))):
                        SetClist[j][nr]=CF(SetCs_neg[j][(r,0)]) 
        num_set=len(SetClist[0].keys())
    if verbose>0:
        print "SetClist_tot=",SetClist
    t=V[0,0]
    if(isinstance(t,float)):
        mpmath_ctx=mpmath.fp
    else:  
        mpmath_ctx=mpmath.mp
    if verbose>0:
        print "mpmath_ctx=",mpmath_ctx
    #use_symmetry=False
    MS = MatrixSpace(CF,int(Ml*nc-num_set),int(comp_dim))
    RHS = Matrix_complex_dense(MS,0,True,True)
    # We allow for either a variation of principal parts or of set coefficients
    if(W.has_key('RHS')):
        l=W['RHS'].ncols()
        if(l>1 and l<>comp_dim):
            raise ValueError,"Incorrect number of right hand sides!"
        
    MS2 = MatrixSpace(CF,int(Ml*nc-num_set),int(Ml*nc-num_set))
    LHS = Matrix_complex_dense(MS2,0,True,True)
    #LHS=mpmath_ctx.matrix(int(Ml*nc-num_set),int(Ml*nc-num_set))
    roffs=0
    if verbose>0:
        print "Ml=",Ml
        print "num_set=",num_set
        print "SetCs=",SetCs
        print "SetClist=",SetClist
        #print "Valslist=",Valslist
        print "V.rows=",V.nrows()
        print "V.cols=",V.ncols()
        print "LHS.rows=",LHS.nrows()
        print "LHS.cols=",LHS.ncols()
        print "RHS.rows=",RHS.nrows()
        print "RHS.cols=",RHS.ncols()
        print "use_sym=",use_sym
    for r in range(V.nrows()):
        cr=r+Ms
        if(SetClist[0].keys().count(r+Ms)>0):
            roffs=roffs+1
            continue
        for fn_j in range(comp_dim):
            if(W.has_key('RHS') and W['RHS'].ncols()>fn_j):
                RHS[r-roffs,fn_j]=CF(-W['RHS'][r,fn_j])
            elif(W.has_key('RHS')):
                RHS[r-roffs,fn_j]=CF(-W['RHS'][r,0])
            else:
                RHS[r-roffs,fn_j]=zero
            for c in SetClist[fn_j].keys():
                v=CF(SetClist[fn_j][c])
                tmp=v*V[r,c-Ms]
                RHS[r-roffs,fn_j]=RHS[r-roffs,fn_j]-tmp
        coffs=0
        for k in range(V.ncols()):            
            if(SetClist[0].keys().count(k+Ms)>0):
                coffs=coffs+1
                continue
            try:                
                LHS[r-roffs,k-coffs]=V[r,k]
            except IndexError:
                print "r,k=",r,k
                print "V.rows=",V.nrows()
                print "V.cols=",V.ncols()
                print "roffs,coffs=",roffs,coffs
                print "r-roffs,k-coffs=",r-roffs,k-coffs
                print "LHS.rows=",LHS.nrows()
                print "LHS.cols=",LHS.ncols()                
                raise IndexError,"Matrix / coefficients is set up wrong!"
            #print "LHS[",r,k,"]=",LHS[r-roffs,k-coffs]
    #return LHS,RHS
    smin=smallest_inf_norm(LHS)
    if verbose>0:
        print "sminfn=",smin
    dps0=CF.prec()
    done=False
    i=1
    while (not done and i<=maxit):
        try:
            Q,R = LHS.qr_decomposition()
            #A, p = mpmath_ctx.LU_decomp(LHS)
            done=True
        except ZeroDivisionError:
            #t=int(mpmath_ctx.ceil(-mpmath_ctx.log10(smallest_inf_norm(LHS))))
            t=int(ceil(-log_b(smallest_inf_norm(LHS),10)))
            dps=t+5*i; i=i+1
            if verbose>-1:
                print "raising number of digits to:",dps
            LHS.set_prec(dps)
            # raise ZeroDivisionError,"Need higher precision! Use > %s digits!" % t
    if(i>=maxit):
        raise ZeroDivisionError,"Can not raise precision enough to solve system! Should need > %s digits! and %s digits was not enough!" % (t,dps)
    X=dict()
    for fn_j in range(comp_dim):
        X[fn_j] = dict() 
        X[fn_j][0] = dict() 
        v = RHS.column(fn_j)
        if verbose>0:
            print "len(B)=",len(v)
            #print "RHS=",v
        #b = mpmath_ctx.L_solve(A, RHS.column(fn_j), p)
        TMP = LHS.solve(v) #mpmath_ctx.U_solve(A, b)
        roffs=0
        res = (LHS*TMP-v).norm()
        if verbose>0:
            print "res(",fn_j,")=",res
        #res = mpmath_ctx.norm(mpmath_ctx.residual(LHS, TMP, RHS.column(fn_j)))
        #print "res(",fn_j,")=",res
        for i in range(0,nc):
            X[fn_j][0][i]=dict()
        for i in range(nc):
            roffs2=0
            for n in range(Ml):
                nn=i*Ml+n+Ms
                key=n+Ms
                #if(i==1):
                #    print n,key
                if(SetClist[fn_j].keys().count(nn)>0):
                    if verbose>1:
                        print "We have set ",nn
                    roffs=roffs+1
                    X[fn_j][0][i][key]=SetClist[fn_j][nn] 
                    if verbose>0:
                        print "X[",fn_j,",",i,",",key,"]=",SetClist[fn_j][nn]
                        print "nn=",nn
                    continue
                try:
                    #X[fn_j][0][i][n-roffs2+Ms]=TMP[nn-Ms-roffs,0]
                    X[fn_j][0][i][key]=TMP[nn-Ms-roffs]
                except IndexError:
                    print "n*Mli-roffs=",n,'+',Ml,'*',i,'-',roffs,"=",n+Ml*i-roffs
                ## We also insert the principal part if it is applicable
    #mpmath.mp.dps=dpold
    # return x
    return X

def get_parameters(N,k,m,eps):
    r"""
    INPUT:  (used in later functions as well)
    - N -- level
    - k - weight
    - m -- the largest index (in absoulute value) of the principal part
    - -- eps -- desired precision
    OUTPUT:
     -- M -- truncation point
     -- Y -- Y-value to use

    """

    Y = sqrt(3.0)/RR(2*N)*0.99
    for M in range(10,100000,5):
        ep = err_estimate(N,Y,k,m,M)
        if abs(ep)<eps:
              return M,Y
    raise ArithmeticError,"Could not find good M!"


def err_estimate(N,Y,k,m,M):
    r""" compute the error estimate of the coefficient vector  with a truncation at M of both holomorphic and non holomorphic part
     This correspnds to the 2epsilon [[Y_k]] in the paper by me and Jan. We do not compute the error from the ||V^-1||_infinity
"""
    delta = 2*RR.pi()*Y-4*RR.pi()*sqrt(abs(m))/N/sqrt(M)
    arg1 = sqrt(M)*4*RR.pi()*sqrt(abs(m))/N

    f1 = 6*max(1-k,1)*max(3/2*k+3/4,1)/RR.pi()**2/16*Y**(-k+1)*M**(k/2+3/4)*arg1.exp()
    f2 = 1/delta.exp()-1
    fak = exp(-M*delta)
    err_non_hol = f1*fak
    err_holom = f2*fak
    eps = err_non_hol + err_holom
    return eps*(1+Y**-(2*k))


def size_of_coefficient_D(N,k,m,D):
   r" Gives the asymptotic of the Fourier coefficient c(D)"
   return exp(RR(abs(m)*abs(D)).sqrt()*4*RR.pi()/N)

def size_of_num_err_by_coeff_app(N,k,m,M,eps=1):
     r""" 
     Gives a rough estimate of the error coming from approximating each fourier coefficients with precision epsilon.
     """
     Y = sqrt(3.0)/(2*N)
     ar1 = RR.pi()*RR(M+1)*Y
     ar2 = RR.pi()*Y
     f1 = (ar1.exp()-1)/(1-ar2.exp())
      
     f2 = Y**(-3/2*k-3/4)*3*max(1-k,1)*RR(gamma(k/2+3/4))/(4*RR.pi())**(k/2+7/4)
     return abs((f1+f2)*eps)


def est_of_diagonal_det(N,k,m,M):
     r""" 
     Gives a rough estimate of the determinant of the linear system (matrix) A based on taking a product over the dominant terms on the diagonal.
     The error in the solution of system A*X will more or less be inverse proportional to this number times the error in the initial matrix A.  This is used to estimate the necessary working precision when computing the special functions etc. in A.
     """
     RF = RealField(100)
     pi2Y = RF.pi()*RF(2*Y)
     f = 1
     for n in range(1,M):
         f = f* RF( mpmath.mp.gammainc(k-1,pi2Y*2*n).real)*(pi2Y*n).exp()
     f = f * (-pi2Y*RF(M)).exp()
     return abs(f)

def setup_harmonic_matrix_sym(S,pp,Y,M0,setc=None,ret_pb=0):
    r"""
    MxM system for Harmonic weak Maass forms at Y=Y with weight k
    """
    Q = M0+10; Qs=1-Q; Qf = Q
    Ql = Qf-Qs + 1
    prec = Y.parent().prec()
    mpmath.mp.prec=prec
    X = S.multiplier()
    RF = RealField(prec)
    CF = MPComplexField(prec)
    pb = pullback_pts_mp(S,1-Q,Q,Y)
    if ret_pb==1:        
        return pb
    xm = pb['xm']; xpb=pb['xpb']; ypb=pb['ypb']; cvec=pb['cvec']
    assert S.group().ncusps()==2
    verbose = S._verbose
    if S._verbose>0:
        print "Cvec[0,1,0]=",cvec.get(0,{}).get(1,{}).get(0,0)
        print "Ypb[0,1,0]=",ypb.get(0,{}).get(1,{}).get(0,0)
    sz = (2*M0+1)*S.group().ncusps()
    V = Matrix_complex_dense(MatrixSpace(CF,sz,sz),0)
    RHS = Matrix_complex_dense(MatrixSpace(CF,sz,1),0)
    nc = S.group().ncusps()
    k = S.weight()
    km1 = 1-k
    twopi=RF.pi()*RF(2)
    pp_info = check_principal_parts(H,[pp])
    if S._holomorphic==1:
        Ms=0; Mf=M0
    else:
        Ms=-M0; Mf=M0
    Ml=Mf-Ms+1
    f1d = {}
    f2d = {}
    for l in range(Ms,Mf+1):
        f2d[l]={}
        #f1d[l]={}
        for icusp in range(nc):
            #f1d[l][icusp]={};
            f2d[l][icusp]={}
            lr = RF(l + S.alpha(icusp)[0])
            for j in range(Ql):
                f2d[l][icusp][j]=-xm[j]*lr 
                #for jcusp in range(nc):
                #    f1d[l][icusp][jcusp]={}
                #    for j in range(Ql):
                #        f1d[l][icusp][jcusp][j]=CF(0,lr*xpb[icusp][jcusp][j]).exp()
    ymax = 0
    xdmax=0
    cvmax= 0
    sgnv={}
    for icusp in range(nc):
        sgnv[icusp]={}
        for jcusp in range(nc):
            sgnv[icusp][jcusp]={}
            if verbose>0:
                print "i,j:",icusp,jcusp
            for j in range(Ql):
                sgnv[icusp][jcusp][j]={}
                if ypb[icusp][jcusp][j] > ymax:
                    ymax = ypb[icusp][jcusp][j]
            if verbose>0:
                print "icusp,jcusp=",icusp,jcusp
            for j in range(Q+1):
                if verbose>1:
                    print "j=",j
                    print "2Q-1-j=",2*Q-1-j
                x1 = xpb[icusp][jcusp][j]
                x2 = xpb[icusp][jcusp][2*Q-1-j]
                y1 = ypb[icusp][jcusp][j]
                y2 = ypb[icusp][jcusp][2*Q-1-j]
                c1 = cvec[icusp][jcusp][j]
                c2 = cvec[icusp][jcusp][2*Q-1-j]
                ## Calculate the factor
                if icusp==jcusp:
                    f1 = 0
                elif icusp==1 and jcusp==0:
                    f1 = -S.weight()
                else:
                    f1 = S.weight()
                if S.multiplier().character()(-1)==1:
                    f2= 0
                else:
                    f2 = 1
                #z=G.pullback(xm[j],Y)
                #w=z[0]+I*z[1]
                #if abs(w-xm[j]-I*Y)>1e-8:
                #if ypb[icusp][jcusp][j] >Y:
                f3 = S.weight()
                #else:
                #    f3 = 0
                sgnv[icusp][jcusp][j] = (f1 + f2 +  f3) % 2
                c2 = c2.conjugate()*RF((-1)**(f1+f2+f3))
                if j==14 and icusp==0 and jcusp==1:
                    print "ypb=",ypb[icusp][jcusp][j]
                    print "sgnv=",sgnv[icusp][jcusp][j],
                    print "f1,f2,f3=",f1 ,f2 , f3
                #print "xm[j]-xm[1-j]=",xm[j]+xm[2*Q-1-j]
                #print "|x1-x2|=",abs(x2+x1)
                #print "|y1-y2|=",abs(y2-y1)
                if verbose>2:
                    print "cv[j]=",c1
                    print "cv[1-j]=",c2
                #print "|cv1-cv2|=",abs((c1+c2).imag())
                if abs(c1-c2)>cvmax:
                    cvmax = abs(c1-c2)
                    #if abs(c1-c2)>0.01:
                    if verbose>0:
                        print "CV diff=",cvmax
                if abs(y1-y2)>0.01:
                    print "Y diff=",abs(y1-y2)
                if abs(x1+x2)>0.01:
                    print "X diff=",abs(x1+x2)
                #if cvmax > 1:
                #    return 
                if abs(x2+x1)>xdmax:
                    xdmax = abs(x2+x1)
#    return
    if verbose>0:
        print "xdmax=",xdmax
        print "cvmax=",cvmax
    if max(xdmax,cvmax) <= 2.**(8-Y.prec()):
        use_sym = 1
        if verbose>0:
            print "Use symmetry!"
    else:
        raise ArithmeticError,"Could not use symmetry!"
        use_sym = 0
#    return 
    if use_sym==0:
        Q0 = 0; Q1 = Ql
    else:
        Q0 = 1; Q1 = Q+1
    for l in range(Ms,Mf+1):
        for jcusp in range(nc):
            lj = l-Ms+jcusp*Ml
            lr = RF(l + S.alpha(jcusp)[0])
            if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==0 and int(pp_info['variable_a0_minus'][0][jcusp])==0:
                continue
            for icusp in range(nc):
                for j in range(0,Q):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    f11 = CF(1)
                    if lr>0:
                        f11 = (-twopi*lr*ypb[icusp][jcusp][j]).exp()
                        bes = CF(1)
                    elif lr<0:
                        f11 = (-twopi*lr*ypb[icusp][jcusp][j]).exp()
                        arg = RF.pi()*RF(4)*abs(lr)*ypb[icusp][jcusp][j]
                        bes = RF(mpmath.mp.gammainc(km1,arg))
                        if S._verbose>3 and icusp == 1 and l==Ms:
                            print "arg[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,arg)
                    elif lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                        bes = RF(1)
                    elif lr==0 and int(pp_info['variable_a0_minus'][0][jcusp])==1:
                        if k==1:
                            bes = ypb[icusp][jcusp][j].log()
                        else:
                            bes = ypb[icusp][jcusp][j]**RF(1-k)
                    else:
                        ## In this case we should have simply skipped this
                        bes = RF(0)
                    #f1 = f1d[l][icusp][jcusp][j]*cvec[icusp][jcusp][j]
                    #f1 = f1*cvec[icusp][jcusp][j]
                    #if use_sym == 0: 
                    #    f1 = CF(0,lr*xpb[icusp][jcusp][j]).exp()
                    #    cv = cvec[icusp][jcusp][j]
                    #else:
                    if icusp==jcusp:
                        a1 = 0
                    elif icusp==1 and jcusp==0:
                        a1 = -S.weight()
                    else:
                        a1 = S.weight()
                    if  S.multiplier().character()(-1)==1:
                        a2 = 0
                    else:
                        a2 = 1
                    if ypb[icusp][jcusp][j] >Y:
                        a3 = S.weight()
                    else:
                        a3 = 0
                    ep = a1 + a2 + a3
                    ar1 = lr*xpb[icusp][jcusp][j] + cvec[icusp][jcusp][j].argument()
                    bes = bes * cvec[icusp][jcusp][j].abs()
                    #if is_odd(ep):                        
                    #c2 = c2.conjugate()*RF(f2*(-1)**(f1+f3))
                    #cv = cvec[icusp][jcusp][j]+cvec[icusp][jcusp][2*Q-1-j]
                    if S._verbose>3 and icusp == 1 and l==Ms:
                        print "f1[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,f1*f11)
                        print "be[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,bes)
                    bes = bes*f11  
                    for n in range(Ms,Mf+1):
                        nr = RF(n)+S.alpha(icusp)[0]
                        #f2 = CF(0,-xm[j]*nr).exp()
                        ni = n-Ms+icusp*(2*M0+1)
                        if sgnv[icusp][jcusp][j]==1:
                            f1 = CF(0,2)*(ar1 + f2d[n][icusp][j]).sin()
                        else:
                            f1 = RF(2)*(ar1 + f2d[n][icusp][j]).cos()
                        #f1 = CF(0,lr*xpb[icusp][jcusp][j]+f2d[n][icusp][j]).exp()*cvec[icusp][jcusp][j]
                        vtmp = f1*bes #*f2d[n][icusp][j]
                        #f2 = CF(0,lr*xpb[icusp][jcusp][2*Q-1-j]+f2d[n][icusp][2*Q-j-1]).exp()*cvec[icusp][jcusp][2*Q-j-1]
                        #vtmp +=f2*bes #*f2d[n][icusp][j]                        
                        #if abs(vtmp)<2.**(1-prec):
                        #    print "vtm=",f1,":",f2,":",bes
                        V[ni,lj]+=vtmp
                        if S._verbose>0 and ni==0 and lj==11:
                            print "-------------------"
                            print "n=",n
                            print "V[1,1](",j,")=",V[ni,lj]
                            print "ef1(",j,")=",f1
                            print "ef2(",2*Q-j-1,")=",f2
                            print "sgn[v]=",sgnv[icusp][jcusp][j]
                            print "vtmp=",vtmp
                            #print "cv(",j,")=",cv
                            #print "ef2(",j,")=",f2d[n][icusp][j]
                            print "fd2[{0}][{1}][{2}]={3}".format(n,icusp,j,f2d[n][icusp][j])
#    if use_sym ==1:
#        Qfak = RF(1)/RF(Q)
#    else:
    Qfak = RF(1)/RF(2*Q)
    if verbose>0:
        print "V[0,0]0=",V[0,0]
        print "V[1,0]0=",V[1,0]
        print "V[0,1]0=",V[0,1]
        print "V[1,1]0=",V[1,1]
        if V.nrows()>11:
            print "V[0,11] 1=",V[0,11]
        if V.nrows()>16:
            print "V[16,16] 1=",V[16,16]
        print "Y=",Y
        print "Q=",Q
    for n in range(V.nrows()):
        for l in range(V.ncols()):
            V[n,l]=V[n,l]*Qfak
            #print "V[0,11] 1=",V[0,11]
    if verbose>0:
        print "V[0,0]1=",V[0,0]
        print "V[1,0]1=",V[1,0]
        print "V[0,1]1=",V[0,1]
        print "V[1,1]1=",V[1,1]
        print "pp_info=",pp_info
    ## Setting up the right hand side and subtracting left-hand side
    pp_plus = pp_info['PPplus'][0]
    pp_minus = pp_info['PPminus'][0]
    for n in range(Ms,Mf+1):
        for icusp in range(nc):
            #print "n,icusp=",n,icusp
            nr = RF(n)+S.alpha(icusp)[0]
            ni = n -Ms + icusp*(2*M0+1)
            if nr>0:
                bes = RF(-Y*twopi*nr).exp()
            elif nr<0:
                arg = RF.pi()*RF(4)*abs(nr)*Y
                bes = RF(-Y*twopi*nr).exp()
                bes = bes*RF(mpmath.mp.gammainc(km1,arg))
                #bes = RF(bes)
                #bes = incomplete_gamma(km1,arg)
            elif nr==0 and int(pp_info['variable_a0_plus'][0][icusp])==1:
                bes = RF(1)
            elif nr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                if k==1:
                    bes = Y.log()
                else:
                    bes = Y**RF(1-k)
            else:
                bes = 0
            #if ni==1 or ni==16 and S._verbose>0:
            #    print "ni=",ni
            #    print "nr=",nr
            #    print "bes(1)=",bes
            V[ni,ni]-=bes
                #raise ArithmeticError,"a0 not correct set!"
            if verbose>1:
                print "n=",n
            for jcusp,l in pp_plus.keys():
                ppc = CF(pp_plus[(jcusp,l)])
                lr = RF(l)+S.alpha(jcusp)[0]
                if verbose>1:
                    print "l=",l
                summa = CF(0)
                if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                    continue
                #print "MAking RHS! with l,jcusp=",l,jcusp
                for j in range(0,Q):
                    #print "ypb=",ypb[icusp][jcusp][j]
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if lr<0:
                        bes = RF(-y*twopi*lr).exp()
                    elif lr==0:
                        bes = RF(1)
                    else:
                        raise ArithmeticError,"This princpal part should be holomorphic!"
                    z = cvec[icusp][jcusp][j]
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j] + z.argument()
                    ab1 = z.abs()
                    #f2 = CF(0,arg).exp()
                    if sgnv[icusp][jcusp][j]==1:
                        f2 = CF(0,2)*arg.sin()
                    else:
                        f2 = RF(2)*arg.cos()
                    tmpc = bes*f2*ab1
                    if verbose>3:
                        print "tmpc = (",j,")",y,bes,"*",f2,"*",cvec[icusp][jcusp][j],"=",tmpc
                    summa = summa + tmpc
                if verbose>1:
                    print "MAking RHS! summma = ",summa
                summa = summa*Qfak
                RHS[ni,0] = RHS[ni,0] + summa*ppc
                if l==n and icusp==jcusp:
                    if verbose>0:
                        print "Subtract! ni,n,nr=",ni,n,nr
                        print "ppc=",ppc
                    if nr<0:
                        bes = RF(-Y*twopi*nr).exp()
                        RHS[ni,0] = RHS[ni,0] - bes*ppc
                    else:
                        if nr==0 and pp_info['variable_a0_plus'][0][icusp]==0:
                            bes = RF(1)
                            RHS[ni,0] = RHS[ni,0] - bes*ppc
            # Set the non-holomorphic principal part
            for jcusp,l in pp_minus.keys():
                ppc = pp_minus[(jcusp,l)]
                lr = RF(l)+S.alpha(jcusp)[0]
                summa = 0
                if ppc==0:
                    continue
                if lr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                    continue
                if lr<>0:
                    raise NotImplementedError,"Only implemented n=0 in non-holom. principal part!"
                for j in range(0,Q):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if k==1:
                        bes = y.log()
                    else:
                        bes = y**RF(1-k)

                    z = cvec[icusp][jcusp][j]
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j] + z.argument()
                    ab1 = z.abs()
                    if sgnv[icusp][jcusp][j]==1:
                        f2 = CF(0,2)*arg.sin()
                    else:
                        f2 = RF(2)*arg.sin()
                    tmpc = bes*f2*ab1 #*cvec[icusp][jcusp][j]
                    summa += tmpc
                summa = summa*ppc*Qfak
                RHS[ni,0] +=summa                                
                if l==n and icusp==jcusp:
                    if k==1:
                        bes = Y.log()
                    else:
                        bes = Y**RF(1-k)
                    RHS[ni,0] -= bes*ppc
    if verbose>0:
        print "ymax = ",ymax

    if setc==None:
        return V,RHS
    W={}
    W['V']=V
    W['RHS']=RHS
    W['space']=S
    W['Ms']=-M0;    W['Mf']=M0
    W['Ml']=2*M0+1
    W['rdim']=1
    W['pp']=pp
    W['nc']=S.group().ncusps()
    W['var_a+']=pp_info['variable_a0_plus']
    W['var_a-']=pp_info['variable_a0_minus']
 
    N = S.set_normalization([setc])
    
    C=solve_system_for_harmonic_weak_Maass_waveforms(W,N)
    return C


def setup_harmonic_matrix_sym2(S,pp,Y,M0,setc=None,ret_pb=0):
    r"""
    MxM system for Harmonic weak Maass forms at Y=Y with weight k
    """
    Q = M0+10; Qs=1; Qf = Q
    Ql = Qf-Qs + 1
    prec = Y.parent().prec()
    mpmath.mp.prec=prec
    X = S.multiplier()
    RF = RealField(prec)
    CF = MPComplexField(prec)
    pb = pullback_pts_mp(S,1,Q,Y)
    if ret_pb==1:        
        return pb
    xm = pb['xm']; xpb=pb['xpb']; ypb=pb['ypb']; cvec=pb['cvec']
    assert S.group().ncusps()==2
    verbose = S._verbose
    if S._verbose>0:
        print "Cvec[0,1,0]=",cvec.get(0,{}).get(1,{}).get(0,0)
        print "Ypb[0,1,0]=",ypb.get(0,{}).get(1,{}).get(0,0)
    sz = (2*M0+1)*S.group().ncusps()
    V = Matrix_complex_dense(MatrixSpace(CF,sz,sz),0)
    RHS = Matrix_complex_dense(MatrixSpace(CF,sz,1),0)
    nc = S.group().ncusps()
    k = S.weight()
    km1 = 1-k
    twopi=RF.pi()*RF(2)
    pp_info = check_principal_parts(H,[pp])
    if S._holomorphic==1:
        Ms=0; Mf=M0
    else:
        Ms=-M0; Mf=M0
    Ml=Mf-Ms+1
    f1d = {}
    f2d = {}
    for l in range(Ms,Mf+1):
        f2d[l]={}
        #f1d[l]={}
        for icusp in range(nc):
            #f1d[l][icusp]={};
            f2d[l][icusp]={}
            lr = RF(l + S.alpha(icusp)[0])
            for j in range(Q):
                #f2d[l][icusp][j]=(-xm[j] + RF.pi())*lr
                f2d[l][icusp][j]=-xm[j]*lr
                #for jcusp in range(nc):
                #    f1d[l][icusp][jcusp]={}
                #    for j in range(Ql):
                #        f1d[l][icusp][jcusp][j]=CF(0,lr*xpb[icusp][jcusp][j]).exp()
    ymax = 0
    xdmax=0
    cvmax= 0
    sgnv={}
    for icusp in range(nc):
        sgnv[icusp]={}
        for jcusp in range(nc):
            sgnv[icusp][jcusp]={}
            if verbose>0:
                print "i,j:",icusp,jcusp
            for j in range(Q):
                sgnv[icusp][jcusp][j]={}
                if ypb[icusp][jcusp][j] > ymax:
                    ymax = ypb[icusp][jcusp][j]
            #if verbose>0:
            #    print "icusp,jcusp=",icusp,jcusp
            # for j in range(Q+1):
            #     if verbose>1:
            #         print "j=",j
            #         print "2Q-1-j=",2*Q-1-j
            #     x1 = xpb[icusp][jcusp][j]
            #     x2 = xpb[icusp][jcusp][2*Q-1-j]
            #     y1 = ypb[icusp][jcusp][j]
            #     y2 = ypb[icusp][jcusp][2*Q-1-j]
            #     c1 = cvec[icusp][jcusp][j]
            #     c2 = cvec[icusp][jcusp][2*Q-1-j]
            #     ## Calculate the factor
            #     if icusp==jcusp:
            #         f1 = 0
            #     elif icusp==1 and jcusp==0:
            #         f1 = -S.weight()
            #     else:
            #         f1 = S.weight()
            #     f2= S.multiplier().character()(-1)
            #     if ypb[icusp][jcusp][j] >Y:
            #         f3 = S.weight()
            #     else:
            #         f3 = 0
            #     sgnv[icusp][jcusp][j] = (f1 + f2 + f3) % 2
            #     c2 = c2.conjugate()*RF(f2*(-1)**(f1+f3))
                
            #     #print "xm[j]-xm[1-j]=",xm[j]+xm[2*Q-1-j]
            #     #print "|x1-x2|=",abs(x2+x1)
            #     #print "|y1-y2|=",abs(y2-y1)
            #     if verbose>0:
            #         print "cv[j]=",c1
            #         print "cv[1-j]=",c2
            #     #print "|cv1-cv2|=",abs((c1+c2).imag())
            #     if abs(c1-c2)>cvmax:
            #         cvmax = abs(c1-c2)
            #         #if abs(c1-c2)>0.01:
            #         if verbose>0:
            #             print "CV diff=",cvmax
            #     if abs(y1-y2)>0.01:
            #         print "Y diff=",abs(y1-y2)
            #     if abs(x1+x2)>0.01:
            #         print "X diff=",abs(x1+x2)
            #     #if cvmax > 1:
            #     #    return 
            #     if abs(x2+x1)>xdmax:
            #         xdmax = abs(x2+x1)
    if verbose>0:
        print "xdmax=",xdmax
        print "cvmax=",cvmax
    if max(xdmax,cvmax) <= 2.**(8-Y.prec()):
        use_sym = 1
        if verbose>0:
            print "Use symmetry!"
    else:
        raise ArithmeticError,"Could not use symmetry!"
        use_sym = 0
#    return 
#    if use_sym==1:
    Q0 = 1; Q1 = Q+1
#    else:
#        Q0 = 1; Q1 = Q+1
    for l in range(Ms,Mf+1):
        for jcusp in range(nc):
            lj = l-Ms+jcusp*Ml
            lr = RF(l + S.alpha(jcusp)[0])
            if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==0 and int(pp_info['variable_a0_minus'][0][jcusp])==0:
                continue
            for icusp in range(nc):
                for j in range(Q):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    f11 = CF(1)
                    if lr>0:
                        f11 = (-twopi*lr*y).exp()
                        bes = CF(1)
                    elif lr<0:
                        f11 = (-twopi*lr*y).exp()
                        arg = RF.pi()*RF(4)*abs(lr)*y
                        bes = RF(mpmath.mp.gammainc(km1,arg))
                        if S._verbose>3 and icusp == 1 and l==Ms:
                            print "arg[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,arg)
                    elif lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                        bes = RF(1)
                    elif lr==0 and int(pp_info['variable_a0_minus'][0][jcusp])==1:
                        if k==1:
                            bes = y.log()
                        else:
                            bes = y**RF(1-k)
                    else:
                        ## In this case we should have simply skipped this
                        bes = RF(0)
                    #f1 = f1d[l][icusp][jcusp][j]*cvec[icusp][jcusp][j]
                    #f1 = f1*cvec[icusp][jcusp][j]
                    #if use_sym == 0: 
                    #    f1 = CF(0,lr*xpb[icusp][jcusp][j]).exp()
                    #    cv = cvec[icusp][jcusp][j]
                    #else:
                    if icusp==jcusp:
                        a1 = 0
                    elif icusp==1 and jcusp==0:
                        a1 = -S.weight()
                    else:
                        a1 = S.weight()
                    if  S.multiplier().character()(-1)==1:
                        a2 = 0
                    else:
                        a2 = 1
                    if ypb[icusp][jcusp][j] >Y:
                        a3 = S.weight()
                    else:
                        a3 = 0
                    ep = a1 + a2 + a3
                    #ar1 = lr*xpb[icusp][jcusp][j] + cvec[icusp][jcusp][j][1]
                    #bes = bes * cvec[icusp][jcusp][j][0]
                    ar1 = lr*xpb[icusp][jcusp][j] + cvec[icusp][jcusp][j][1]
                    bes = bes * cvec[icusp][jcusp][j][0]
                    #if is_odd(ep):                        
                    #c2 = c2.conjugate()*RF(f2*(-1)**(f1+f3))
                    #cv = cvec[icusp][jcusp][j]+cvec[icusp][jcusp][2*Q-1-j]
                    if S._verbose>3 and icusp == 1 and l==Ms:
                        print "f1[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,f1*f11)
                        print "be[{0},{1},{2},{3}]={4}".format(icusp,jcusp,l-Ms,j,bes)
                    bes = bes*f11  
                    for n in range(Ms,Mf+1):
                        nr = RF(n)+S.alpha(icusp)[0]
                        #f2 = CF(0,-xm[j]*nr).exp()
                        ni = n-Ms+icusp*(2*M0+1)
                        if (cvec[icusp][jcusp][j][2] % 2)==1:
                            f1 = CF(0,2)*(ar1 + f2d[n][icusp][j]).sin()
                        elif (cvec[icusp][jcusp][j][2] % 2)==0:
                            f1 = RF(2)*(ar1 + f2d[n][icusp][j]).cos()
                        else:
                            raise ArithmeticError,"need cos or sine!!"
                        #f1 = CF(0,lr*xpb[icusp][jcusp][j]+f2d[n][icusp][j]).exp()*cvec[icusp][jcusp][j]
                        vtmp = f1*bes #*f2d[n][icusp][j]
                        #f2 = CF(0,lr*xpb[icusp][jcusp][2*Q-1-j]+f2d[n][icusp][2*Q-j-1]).exp()*cvec[icusp][jcusp][2*Q-j-1]
                        #vtmp +=f2*bes #*f2d[n][icusp][j]                        
                        #if abs(vtmp)<2.**(1-prec):
                        #    print "vtm=",f1,":",f2,":",bes
                        V[ni,lj]+=vtmp
                        if S._verbose>0 and ni==0 and lj==11:
                            print "-------------------"
                            print "n=",n
                            print "V[1,1](",j,")=",V[ni,lj]
                            print "ef1(",j,")=",f1
                            print "sgn[v]=",cvec[icusp][jcusp][j][2]
                            #print "ef2(",2*Q-j-1,")=",f2
                            print "vtmp=",vtmp
                            #print "cv(",j,")=",cv
                            #print "ef2(",j,")=",f2d[n][icusp][j]
                            print "fd2[{0}][{1}][{2}]={3}".format(n,icusp,j,f2d[n][icusp][j])
#    if use_sym ==1:
#        Qfak = RF(1)/RF(Q)
#    else:
    Qfak = RF(1)/RF(2*Q)
    if verbose>0:
        print "V[0,0]0=",V[0,0]
        print "V[1,0]0=",V[1,0]
        print "V[0,1]0=",V[0,1]
        print "V[1,1]0=",V[1,1]
        if V.nrows()>11:
            print "V[0,11] 1=",V[0,11]
        if V.nrows()>16:
            print "V[16,16] 1=",V[16,16]
        print "Y=",Y
        print "Q=",Q
    for n in range(V.nrows()):
        for l in range(V.ncols()):
            V[n,l]=V[n,l]*Qfak
            #print "V[0,11] 1=",V[0,11]
    if verbose>0:
        print "V[0,0]1=",V[0,0]
        print "V[1,0]1=",V[1,0]
        print "V[0,1]1=",V[0,1]
        print "V[1,1]1=",V[1,1]
        print "pp_info=",pp_info
    ## Setting up the right hand side and subtracting left-hand side
    pp_plus = pp_info['PPplus'][0]
    pp_minus = pp_info['PPminus'][0]
    for n in range(Ms,Mf+1):
        for icusp in range(nc):
            #print "n,icusp=",n,icusp
            nr = RF(n)+S.alpha(icusp)[0]
            ni = n -Ms + icusp*(2*M0+1)
            if nr>0:
                bes = RF(-Y*twopi*nr).exp()
            elif nr<0:
                arg = RF.pi()*RF(4)*abs(nr)*Y
                bes = RF(-Y*twopi*nr).exp()
                bes = bes*RF(mpmath.mp.gammainc(km1,arg))
                #bes = RF(bes)
                #bes = incomplete_gamma(km1,arg)
            elif nr==0 and int(pp_info['variable_a0_plus'][0][icusp])==1:
                bes = RF(1)
            elif nr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                if k==1:
                    bes = Y.log()
                else:
                    bes = Y**RF(1-k)
            else:
                bes = 0
            #if ni==1 or ni==16 and S._verbose>0:
            #    print "ni=",ni
            #    print "nr=",nr
            #    print "bes(1)=",bes
            V[ni,ni]-=bes
                #raise ArithmeticError,"a0 not correct set!"
            if verbose>1:
                print "n=",n
            for jcusp,l in pp_plus.keys():
                ppc = CF(pp_plus[(jcusp,l)])
                lr = RF(l)+S.alpha(jcusp)[0]
                if verbose>1:
                    print "l=",l
                summa = CF(0)
                if lr==0 and int(pp_info['variable_a0_plus'][0][jcusp])==1:
                    continue
                #print "MAking RHS! with l,jcusp=",l,jcusp
                for j in range(0,Q):
                    #print "ypb=",ypb[icusp][jcusp][j]
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if lr<0:
                        bes = RF(-y*twopi*lr).exp()
                    elif lr==0:
                        bes = RF(1)
                    else:
                        raise ArithmeticError,"This princpal part should be holomorphic!"
                    z = cvec[icusp][jcusp][j][1]
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j] + z
                    ab1 = z.abs()
                    #f2 = CF(0,arg).exp()
                    if (cvec[icusp][jcusp][j][2] % 2)==1: #if sgnv[icusp][jcusp][j]==1:
                        f2 = CF(0,2)*arg.sin()
                    else:
                        f2 = RF(2)*arg.cos()
                    tmpc = bes*f2*ab1
                    if verbose>3:
                        print "tmpc = (",j,")",y,bes,"*",f2,"*",cvec[icusp][jcusp][j],"=",tmpc
                    summa = summa + tmpc
                if verbose>1:
                    print "MAking RHS! summma = ",summa
                summa = summa*Qfak
                RHS[ni,0] = RHS[ni,0] + summa*ppc
                if l==n and icusp==jcusp:
                    if verbose>0:
                        print "Subtract! ni,n,nr=",ni,n,nr
                        print "ppc=",ppc
                    if nr<0:
                        bes = RF(-Y*twopi*nr).exp()
                        RHS[ni,0] = RHS[ni,0] - bes*ppc
                    else:
                        if nr==0 and pp_info['variable_a0_plus'][0][icusp]==0:
                            bes = RF(1)
                            RHS[ni,0] = RHS[ni,0] - bes*ppc
            # Set the non-holomorphic principal part
            for jcusp,l in pp_minus.keys():
                ppc = pp_minus[(jcusp,l)]
                lr = RF(l)+S.alpha(jcusp)[0]
                summa = 0
                if ppc==0:
                    continue
                if lr==0 and int(pp_info['variable_a0_minus'][0][icusp])==1:
                    continue
                if lr<>0:
                    raise NotImplementedError,"Only implemented n=0 in non-holom. principal part!"
                for j in range(0,Q):
                    if ypb[icusp][jcusp][j]==0:
                        continue
                    y = ypb[icusp][jcusp][j]
                    if k==1:
                        bes = y.log()
                    else:
                        bes = y**RF(1-k)

                    z = cvec[icusp][jcusp][j]
                    arg = lr*xpb[icusp][jcusp][j] - nr*xm[j] + z.argument()
                    ab1 = z.abs()
                    if (cvec[icusp][jcusp][j][2] % 2)==1: #if sgnv[icusp][jcusp][j]==1:
                        #if sgnv[icusp][jcusp][j]==1:
                        f2 = CF(0,2)*arg.sin()
                    else:
                        f2 = RF(2)*arg.sin()
                    tmpc = bes*f2*ab1 #*cvec[icusp][jcusp][j]
                    summa += tmpc
                summa = summa*ppc*Qfak
                RHS[ni,0] +=summa                                
                if l==n and icusp==jcusp:
                    if k==1:
                        bes = Y.log()
                    else:
                        bes = Y**RF(1-k)
                    RHS[ni,0] -= bes*ppc
    if verbose>0:
        print "ymax = ",ymax

    if setc==None:
        return V,RHS
    W={}
    W['V']=V
    W['RHS']=RHS
    W['space']=S
    W['Ms']=-M0;    W['Mf']=M0
    W['Ml']=2*M0+1
    W['rdim']=1
    W['pp']=pp
    W['nc']=S.group().ncusps()
    W['var_a+']=pp_info['variable_a0_plus']
    W['var_a-']=pp_info['variable_a0_minus']
 
    N = S.set_normalization([setc])
    
    C=solve_system_for_harmonic_weak_Maass_waveforms(W,N)
    return C


m=TrivialMultiplier(Gamma0(23),dchar=(23,-1))
H=HarmonicWeakMaassForms(23,weight=1,multiplier=m,verbose=0,do_mpmath=0,prec=53)
# attach "/scratch/fredstro/git_test/psage/psage/modform/maass/harmonic_test.py"
RF=RealField(H._prec)
Y=RF(0.0369002128569021638466147119322192090862246962107263820410857672275201091238727713061962280)
CF =MPComplexField(H._prec)
#pp={'+':{(0,-1):1,(1,-2):1},'-':{(0,0):0,(1,0):0}}
pp={'+':{(0,-1):1,(0,0):RF(-1/3),(1,0):CF(0,-1/3)},'-':{(0,0):0,(1,0):0}}
#H._verbose=2
#V2=automorphic_forms_alg.setup_matrix_for_harmonic_Maass_waveforms_sym(H,Y,5,15,[pp])
def testing_new_solve(W,N):

    A,B = solve_system_for_harmonic_weak_Maass_waveforms_mp(N, W['V'],W['RHS'],gr=1)
    setc=N['SetCs']
    D = test_lin_solve(A,B,setc)
    return D
MS=MatrixSpace(CF,3)
A = Matrix_complex_dense(MS,[1,2,0,1,3,0,0,0,1])
MS1=MatrixSpace(CF,3,1)
B = Matrix_complex_dense(MS1,[1,1,1])


# def test_SMAT_filter(W,N,verbose=0):
#     skipping = []
#     ## Need to determine exactly which coefficients in the matrix should be ignored
#     Ml = W['Ml']; Ms = W['Ms']
#     Mf = W['Mf']
#     ncusps = W['space'].group().ncusps()
#     pp = W['PP'][0]
#     if verbose>0:
#         print "pp=",pp
#         print "pp[+].keys()=",pp['+'].keys()
#     for r,n in pp['+'].keys(): ## Only possibly n=0 are included in the matrix
#         if verbose>0:
#             print "r,n=",r,n
#         if n==0:
#             if verbose>0:
#                 print "p[-]=",pp['-']
#             if pp['-'].has_key((r,0)):
#                 ix = r*Ml-Ms
#                 if ix not in skipping:
#                     skipping.append(ix)
#     #if verbose>0:
#     #    print "skipping1 =",skipping
#     for r,n in N['SetCs'][0].keys():
#         ix = r*Ml+n-Ms
#         if ix not in skipping:
#             skipping.append(ix)
#     if verbose>0:
#         print "skipping=",skipping
#     skipping.sort()
#     if verbose>0:
#         print "sorted(skipping)=",skipping
#     return lin_solve_w_filter(W['V'],W['RHS'],setC=N['SetCs'],skipping=skipping,ncusps=ncusps,Ms=Ms,Mf=Mf,verbose=verbose)

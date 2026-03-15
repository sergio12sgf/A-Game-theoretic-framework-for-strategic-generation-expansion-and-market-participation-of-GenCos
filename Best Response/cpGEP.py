from gurobipy import *
import pandas as pd

def resultsData(exGen, newGen, iTER):

    df_Xi = exGen
    df_Xj = newGen
    Xr = pd.DataFrame(columns=["iTER","T","F","X_total"])
    pGenCo = pd.DataFrame(columns=["iTER","T","F","Profit_total"])

    #####################################################
    # Total generation capacity by period and GenCo
    #####################################################
    XiT = exGen.groupby(['T','F'], as_index=False)['g_max'].sum().rename(columns={'g_max':'Xi_T'})
    XjT = newGen.groupby(['T','F'], as_index=False)['gj'].sum().rename(columns={'gj':'Xj_T'})    # Va a tronar aqui
    XjT['Xj_T'] = XjT.groupby('F')['Xj_T'].cummax()

    Xtot = (XiT.set_index(['T','F'])['Xi_T'].add(XjT.set_index(['T','F'])['Xj_T'], fill_value=0.0)).reset_index().rename(columns={0:'X_total'})
            
    for r in Xtot.itertuples(index=False):
        Xr.loc[len(Xr)] = [iTER+1, int(r.T), r.F, float(r.X_total)]

    #####################################################
    #   GenCo's Profit
    #####################################################
    df_Xi['Profit'] = df_Xi.apply(lambda r: (r['ci']*r['sig'] - (-1)*r['sig']*r['lmp'])*r['gi'], axis=1)
    df_Xj['Profit'] = df_Xj.apply(lambda r: (r['cj']*r['sigj'] - (-1)*r['sigj']*r['lmp'])*r['gj'] + r['Ij']*r['uj'], axis=1)

    df_XiT = df_Xi['Profit'].groupby([df_Xi['T'], df_Xi['F']]).sum().reset_index(name='Profit_i')
    df_XjT = df_Xj['Profit'].groupby([df_Xj['T'], df_Xj['F']]).sum().reset_index(name='Profit_j')
    Pgenco = (df_XiT.set_index(['T','F'])['Profit_i'].add(df_XjT.set_index(['T','F'])['Profit_j'], fill_value=0.0)).reset_index().rename(columns={0:'Profit_total'})

    # Aqui

    for r in Pgenco.itertuples(index=False):
        pGenCo.loc[len(pGenCo)] = [iTER+1, int(r.T), r.F, float(r.Profit_total)]

    df_data = {
        "Xr": Xr,
        "pGenCo": pGenCo,
    }

    return df_data

def model(d):

    # model definition
    m = Model("gepResponse")

    # Unpacking information
    T, N, F, G, GN, D, Br, Z, Dat_G, Dat_GN, Dat_D, Dat_Z, Lim_Br, Dat_Br, cParams = \
    (d[k] for k in ["T", "N", "F", "G", "GN", "D", "Br", "Z", 
                      "Dat_G", "Dat_GN", "Dat_D", "Dat_Z", "Lim_Br", "Dat_Br","cParams"])

    keys_DatG   = list(Dat_G[['T','F','G']].drop_duplicates().itertuples(index=False, name=None))
    keys_DatGN  = list(Dat_GN[['T','F','GN']].drop_duplicates().itertuples(index=False, name=None))
    keys_Br     = list(Lim_Br[['T','Br']].drop_duplicates().itertuples(index=False, name=None))
    keys_T      = list(T['T'].drop_duplicates())
    keys_N      = list(N['N'].drop_duplicates())
    keys_lmp    = [(t, n) for t in keys_T for n in keys_N]
    keys_Dat_Br = list(Dat_Br[['T','Br','N']].drop_duplicates().itertuples(index=False,name=None))
    keys_DatZ   = list(Dat_Z[['Z','N']].drop_duplicates().itertuples(index=False,name=None))

    # ======================================================================================== #

    #                              Params definition block

    # ======================================================================================== #

    ci    = {(r.T, r.F, r.G):    r.ci      for r in Dat_G.itertuples(index=False)}
    ni    = {(r.T, r.F, r.G):    r.ni      for r in Dat_G.itertuples(index=False)}
    sig   = {(r.T, r.F, r.G):    r.sig     for r in Dat_G.itertuples(index=False)}
    g_min = {(r.T, r.F, r.G):    r.g_min   for r in Dat_G.itertuples(index=False)}
    g_max = {(r.T, r.F, r.G):    r.g_max   for r in Dat_G.itertuples(index=False)}
    cj    = {(r.T, r.F, r.GN):   r.cj      for r in Dat_GN.itertuples(index=False)}
    nj    = {(r.T, r.F, r.GN):   r.nj      for r in Dat_GN.itertuples(index=False)}
    sigj  = {(r.T, r.F, r.GN):   r.sigj    for r in Dat_GN.itertuples(index=False)}
    Ij    = {(r.T, r.F, r.GN):   r.Ij      for r in Dat_GN.itertuples(index=False)}
    g_Nmax= {(r.T, r.F, r.GN):   r.g_Nmax  for r in Dat_GN.itertuples(index=False)}
    f_min = {(r.T,r.Br):         r.f_min   for r in Lim_Br.itertuples(index=False)}
    f_max = {(r.T,r.Br):         r.f_max   for r in Lim_Br.itertuples(index=False)}
    ptdf  = {(r.T,r.Br,r.N):     r.ptdf    for r in Dat_Br.itertuples(index=False)}
    L     = {(r.T):              r.L       for r in Dat_D.itertuples(index=False)}
    rho   = {(r.Z,r.N):          r.rho     for r in Dat_Z.itertuples(index=False)}
    psi   = {(r.Z,r.N):          r.psi     for r in Dat_Z.itertuples(index=False)}
    gamma   = {(r.Num):          r.gamma   for r in cParams.itertuples(index=False)}[1]
    UP      = {(r.Num):          r.Up      for r in cParams.itertuples(index=False)}[1]

    # ======================================================================================== #

    #                                        Variables

    # ======================================================================================== #

    gi   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="gi")
    Xi   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="Xi")
    gj   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="gj")
    Xj   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="Xj")
    uj   = m.addVars(keys_DatGN,       vtype=GRB.BINARY,    name="uj")
    w    = m.addVars(keys_T,           vtype=GRB.CONTINUOUS, name="w")
    flow = m.addVars(keys_Br,    lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="flow")
    lmp  = m.addVars(keys_lmp,   lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="lmp")
    
    lambda_t = m.addVars(keys_T, lb=-GRB.INFINITY, name="lambda_t")
    muiM = m.addVars(keys_DatG,  lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="muiM")
    muim = m.addVars(keys_DatG,  lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="muim")
    mujM = m.addVars(keys_DatGN, lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="mujM")
    mujm = m.addVars(keys_DatGN, lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="mujm")
    muwM = m.addVars(keys_T,     lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="muwM")
    muwm = m.addVars(keys_T,     lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="muwm")
    murM = m.addVars(keys_Br,    lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="murM")
    murm = m.addVars(keys_Br,    lb=0, ub=UP, vtype=GRB.CONTINUOUS, name="murm")
    murM = m.addVars(keys_Br,          ub=UP, vtype=GRB.CONTINUOUS, name="murM")
    murm = m.addVars(keys_Br,          ub=UP, vtype=GRB.CONTINUOUS, name="murm")

    s1   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s1")
    s2   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s2")
    s3   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s3")
    s4   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s4")
    s5   = m.addVars(keys_Br,    lb=0, vtype=GRB.CONTINUOUS, name="s5")  
    s6   = m.addVars(keys_Br,    lb=0, vtype=GRB.CONTINUOUS, name="s6")
    s7  = m.addVars(keys_T,      lb=0, vtype=GRB.CONTINUOUS, name="s11")
    s8  = m.addVars(keys_T,      lb=0, vtype=GRB.CONTINUOUS, name="s12")

    # ======================================================================================== #

    #                                    Objective Function

    # ======================================================================================== #

    obj = LinExpr(0.0)

    # Investments and Strategic Capacities of GenCo f
    obj += quicksum(Ij[j]*uj[j]               for j in keys_DatGN)
    obj += quicksum(sig[i]*ci[i]*gi[i]        for i in keys_DatG)
    obj += quicksum(sigj[j]*cj[j]*gj[j]       for j in keys_DatGN)

    # Sensitivity to Branch Limits
    obj += quicksum(murm[r]*f_min[r]          for r in keys_Br)
    obj -= quicksum(murM[r]*f_max[r]          for r in keys_Br)

    # Sensitivity to Load Shedding
    obj += quicksum(gamma*(L[t] - w[t])       for t in keys_T)
    obj -= quicksum(muwm[t]*L[t]              for t in keys_T)

    m.setObjective(obj, GRB.MINIMIZE)

    # ======================================================================================== #

    #                                   Primal Constraints

    # ======================================================================================== #

    #m.addConstrs((quicksum(uj[j] for j in keys_DatGN if j[1] == f) == 1 for f in F['F']), name="eq24_f_gn")
    F_set = sorted({f for (t,f,j) in keys_DatGN})
    J_set = sorted({j for (t,f,j) in keys_DatGN})

    for f in F_set:
        for j in J_set:
            if any((t,f,j) in keys_DatGN for t in keys_T):
                m.addConstr(
                    quicksum(uj[(t,f,j)] for t in keys_T if (t,f,j) in keys_DatGN) == 1,
                    name=f"eq24_f_gn[{f},{j}]"
                )

    # eq25: sum_t g_i[t,f,i] + sum_t g_j[t,f,j] = L[t] - w[t]
    m.addConstrs((quicksum(gi[i] for i in keys_DatG  if i[0] == t) +
        quicksum(gj[j] for j in keys_DatGN if j[0] == t) == L[t] - w[t]
        for t in keys_T), name="eq4b")

    # eq26: g_min <= g_i <= giMax 
    m.addConstrs((gi[i] >= g_min[i] for i in keys_DatG), name="eq4c_lo")
    m.addConstrs((gi[i] <= g_max[i] for i in keys_DatG), name="eq4c_hi")

    # eq4d: 0 <= g_j <= sum_{tfj}ujgjMax (GenCo)
    m.addConstrs((gj[j] >= 0 for j in keys_DatGN), name="eq4d_lo")
    m.addConstrs((gj[j1] <= quicksum(uj[j]*g_Nmax[j] for j in keys_DatGN if j[1] == j1[1] and j[2] == j1[2] 
                                     and j[0] <= j1[0]) for j1 in keys_DatGN), name="eq4d_hj")

    m.addConstrs((
        flow[(t,br)] == quicksum(
            ptdf.get((t,br,n), 0.0) * (
                quicksum(gi[i] for i in keys_DatG  if i[0] == t and ni[i] == n) +
                quicksum(gj[j] for j in keys_DatGN if j[0] == t and nj[j] == n) -
                quicksum(rho[(z,n)]*psi[(z,n)]*(L[t] - w[t]) for (z,nd) in keys_DatZ if nd == n)
            )
            for n in keys_N
        )
        for (t,br) in keys_Br
    ), name="eqPTDF")
    
    # eq28: f_min[t,r] <= flow[t,r] <= f_max[t,r] (branch limits)
    m.addConstrs((flow[r] >= f_min[r] for r in keys_Br), name="eq4g_lo")
    m.addConstrs((flow[r] <= f_max[r] for r in keys_Br), name="eq4g_hi")
    
    # eq29: lmp[t,n] == lambda[t] + sum_{t,r,n}ptdf*(murM[t,r] - murm[t,r])
    m.addConstrs((lmp[(t, n)] == lambda_t[t] +
                quicksum(ptdf.get((tt, r, n), 0.0) * (murM[(tt, r)] - murm[(tt, r)])
                for (tt, r, nn) in keys_Dat_Br if tt == t and nn == n )
                for n in keys_N
                for t in keys_T), name="eq4i")
    
    # eq4h: 0 <= w[t] <= L[t]
    m.addConstrs((w[t] >= 0 for t in keys_T), name="eq4h_lo")
    m.addConstrs((w[t] <= L[t] for t in keys_T), name="eq4h_hi")
    
    # ======================================================================================== #

    #                                   Dual Constraints

    # ======================================================================================== #

    # eq29: sig[i]*ci[i] + lambda_t[t] + sum_r ptdf[t,r,n]*(murM[t,r] - murm[t,r]) - muim[i] + muiM[i] = 0 (solo GenCo)
    m.addConstrs((sig[i]*ci[i] + lmp[i[0],ni[i]] - muim[i] + muiM[i] == 0 for i in keys_DatG), name="eq6d")

    # eq30: sigj[j]*cj[j] + lmp[t] + sum_r ptdf[t,r,nj[j]]*(murM[t,r] - murm[t,r]) - mujm[j] + mujM[j] = 0 (solo GenCo)
    m.addConstrs((sigj[j]*cj[j] + lmp[j[0],nj[j]] - mujm[j] + mujM[j]== 0 for j in keys_DatGN), name="eq6e")
    
    m.addConstrs((gamma + lambda_t[t] + 
                quicksum(quicksum(ptdf.get((t, r, n), 0.0) * (murM[t, r] - murm[t, r])
                for r in Br['Br'])*quicksum(rho.get((z, n), 0.0) * psi.get((z, n), 0.0)
                for z in Dat_Z.loc[Dat_Z['N'] == n, 'Z']) for n in N['N'])
                + muwM[t] - muwm[t] == 0 for t in keys_T ), name="eq6h")
    
    # ======================================================================================== #

    #                                    SOS1 Constraints

    # ======================================================================================== #

    for i in keys_DatG:
        m.addConstr(g_max[i] - gi[i] == s1[i])
        m.addConstr(muiM[i] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muiM[i], s1[i]], [1.0, 2.0])

    for i in keys_DatG:
        m.addConstr(gi[i] - g_min[i] == s2[i])
        m.addConstr(muim[i] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muim[i], s2[i]], [1.0, 2.0])

    for j in keys_DatGN:
        m.addConstrs((-gj[j1]+ quicksum(uj[j] * g_Nmax[j] for j in keys_DatGN if j[1] == j1[1]
                        and j[2] == j1[2] and j[0] <= j1[0]) == s3[j] for j1 in keys_DatGN))
        m.addConstr(mujM[j] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [mujM[j], s3[j]], [1.0, 2.0])

    for j in keys_DatGN:
        m.addConstr(gj[j] == s4[j])
        m.addConstr(mujm[j] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [mujm[j], s4[j]], [1.0, 2.0])

    for r in keys_Br:
        m.addConstr(flow[r] - f_min[r] == s5[r])
        m.addConstr(murm[r]>= 0)
        m.addSOS(GRB.SOS_TYPE1, [murm[r],s5[r]], [1.0, 2.0])

    for r in keys_Br:
        m.addConstr(f_max[r] - flow[r] == s6[r])
        m.addConstr(murM[r]>= 0)
        m.addSOS(GRB.SOS_TYPE1, [murM[r],s6[r]], [1.0, 2.0])

    for t in keys_T:
        m.addConstr(L[t] - w[t] == s7[t])
        m.addConstr(muwM[t] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muwM[t],s7[t]], [1.0, 2.0])

    for t in keys_T:
        m.addConstr(w[t] == s8[t])
        m.addConstr(muwm[t] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muwm[t],s8[t]], [1.0, 2.0])
    
    # ======================================================================================== #

    m.write("pcGEP.lp")

    m.Params.DualReductions = 0
    m.optimize()

    # ======================================================================================== #

    #                               Soluction Information Data

    # ======================================================================================== #

    sol = m.Status
    print(sol)

    # Market Prices
    lmp = {k: v.X for k, v in lmp.items()}
    df_lmp = pd.DataFrame([(*k, v) for k, v in lmp.items()], columns=["T", "N", "LMP"])

    Lr = {k: L[k] for k in L.keys()}
    df_Lt = d['Dat_Z'].merge(Dat_D, how = 'cross')
    df_Lt['Ln'] = df_Lt["L"]*df_Lt["rho"]*df_Lt["psi"]
    df_Lt = df_Lt[['T','Z','N','Ln','L']].sort_values(["T","Z","N"]).reset_index(drop=True)
    df_Lt['lmp'] = df_Lt.apply(lambda row: (1)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['N']), 'LMP'].values[0], axis=1)

    wr = {k: v.X for k, v in w.items()}
    df_wr = pd.DataFrame(list(wr.items()), columns=["T", "wr"]).sort_values("T").reset_index(drop=True)
    print(Lr)
    
    # Existing generation capacity of GenCos
    exGen = Dat_G[['T','F','G','sig','ni','g_max','ci']].copy()
    gi_sol = {k: v.X for k, v in gi.items()}
    exGen['gi'] = exGen.apply(lambda row: gi_sol.get((row['T'], row['F'], row['G']), 0.0), axis=1)
    exGen['lmp'] = exGen.apply(lambda row: (-1/8760)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['ni']), 'LMP'].values[0], axis=1)
    map = {"F1": "F1_pc", "F2": "F2_pc", "F3": "F3_pc"}
    exGen["F"] = exGen["F"].replace(map)
    
    #exGen['Xi'] = exGen.apply(lambda row: Xi_sol.get((row['T'], row['F'], row['G']), 0.0), axis=1)

    # New generation capacity of GenCos
    newGen = Dat_GN[['T','F','GN','Ij','sigj','nj','g_Nmax','cj']].copy()
    ujr = {k: v.X for k, v in uj.items()}
    df_uj = pd.DataFrame([(*k, v) for k, v in ujr.items()], columns=["T", "F", "GN", "uj"])
    gj_sol = {k: v.X for k, v in gj.items()}
    newGen['gj'] = newGen.apply(lambda row: gj_sol.get((row['T'], row['F'], row['GN']), 0.0), axis=1)
    newGen['lmp'] = newGen.apply(lambda row: (-1/8760)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['nj']), 'LMP'].values[0], axis=1)
    #newGen['Xj'] = newGen.apply(lambda row: Xj_sol.get((row['T'], row['F'], row['GN']), 0.0), axis=1)
    newGen['uj'] = newGen.apply(lambda row: df_uj.loc[(df_uj['T'] == row['T']) & (df_uj['GN'] == row['GN']), 'uj'].values[0], axis=1)
    newGen["F"] = newGen["F"].replace(map)

    rGenCo = resultsData(exGen,newGen,iTER = 1)

    exGenf = exGen.copy()
    newGenf = newGen.copy()
    exGenf = exGenf.groupby(['T','F'], as_index=False)['g_max'].sum()
    newGenf = newGenf.groupby(['T','F'], as_index=False)['gj'].sum()
    newGenf['Xj'] = newGenf.groupby('F')['gj'].cummax()
    exGenf['iTER'] = 0
    newGenf['iTER'] = 0
    exGenf = exGenf.rename(columns={"g_max": "Xi"})
    #newGenf['Xj'] = newGenf['gj']
    exGenf = exGenf[['iTER','T','F','Xi']]
    newGenf = newGenf[['iTER','T','F','Xj']]
    map = {"F1_pc": "F1", "F2_pc": "F2", "F3_pc": "F3"}
    exGenf["F"] = exGenf["F"].replace(map)
    newGenf["F"] = newGenf["F"].replace(map)

    results = {
        "obj": m.ObjVal,
        "Sol" : m.Status,
        "Xr": rGenCo['Xr'],
        "Profit": rGenCo['pGenCo'],
        "LMP": df_lmp,
        "Lnodal" : df_Lt,
        'wr' : df_wr,
        'Xi' : exGenf,
        'Xj' : newGenf,
    }

    return results

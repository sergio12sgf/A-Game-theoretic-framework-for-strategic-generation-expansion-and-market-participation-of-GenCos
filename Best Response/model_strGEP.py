from gurobipy import *
import pandas as pd

def model(d,varXi,varXj,GenCo):

    # model definition
    m = Model("gepResponse")

    # Unpacking information
    T, N, F, G, GN, D, Br, Z, Dat_G, Dat_GN, Dat_D, Dat_Z, Lim_Br, Dat_Br, cParams = \
    (d[k] for k in ["T", "N", "F", "G", "GN", "D", "Br", "Z", 
                      "Dat_G", "Dat_GN", "Dat_D", "Dat_Z", "Lim_Br", "Dat_Br","cParams"])
    
    # ======================================================================================== #

    #                                  Keys or Index block

    # ======================================================================================== #

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

    ci      = {(r.T, r.F, r.G) : r.ci     for r in Dat_G.itertuples(index=False)}
    ni      = {(r.T, r.F, r.G) : r.ni     for r in Dat_G.itertuples(index=False)}
    sig     = {(r.T, r.F, r.G) : r.sig    for r in Dat_G.itertuples(index=False)}
    g_min   = {(r.T, r.F, r.G) : r.g_min  for r in Dat_G.itertuples(index=False)}
    g_max   = {(r.T, r.F, r.G) : r.g_max  for r in Dat_G.itertuples(index=False)}
    cj      = {(r.T, r.F, r.GN): r.cj     for r in Dat_GN.itertuples(index=False)}
    nj      = {(r.T, r.F, r.GN): r.nj     for r in Dat_GN.itertuples(index=False)}
    sigj    = {(r.T, r.F, r.GN): r.sigj   for r in Dat_GN.itertuples(index=False)}
    Ij      = {(r.T, r.F, r.GN): r.Ij     for r in Dat_GN.itertuples(index=False)}
    g_Nmax  = {(r.T, r.F, r.GN): r.g_Nmax for r in Dat_GN.itertuples(index=False)}
    f_min   = {(r.T,r.Br)      : r.f_min  for r in Lim_Br.itertuples(index=False)}
    f_max   = {(r.T,r.Br)      : r.f_max  for r in Lim_Br.itertuples(index=False)}
    ptdf    = {(r.T,r.Br,r.N)  : r.ptdf   for r in Dat_Br.itertuples(index=False)}
    L       = {(r.T)    : r.L             for r in Dat_D.itertuples(index=False)}
    rho     = {(r.Z,r.N): r.rho           for r in Dat_Z.itertuples(index=False)}
    psi     = {(r.Z,r.N): r.psi           for r in Dat_Z.itertuples(index=False)}
    gamma_f = {(r.Num)  : r.gamma_f       for r in cParams.itertuples(index=False)}[1]
    gamma   = {(r.Num)  : r.gamma         for r in cParams.itertuples(index=False)}[1]
    UP      = {(r.Num)  : r.Up            for r in cParams.itertuples(index=False)}[1]

    # ======================================================================================== #

    #                                        Variables

    # ======================================================================================== #

    gi   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="gi")
    Xi   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="Xi")
    gj   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="gj")
    Xj   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="Xj")
    uj   = m.addVars(keys_DatGN,       vtype=GRB.BINARY,    name="uj")
    w    = m.addVars(keys_T,     lb=0, vtype=GRB.CONTINUOUS, name="w")
    flow = m.addVars(keys_Br,    lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="flow")
    lmp  = m.addVars(keys_lmp,   lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name="lmp")
    
    lambda_t = m.addVars(keys_T, lb=-GRB.INFINITY, name="lambda_t")
    muiM = m.addVars(keys_DatG,  ub=UP, vtype=GRB.CONTINUOUS, name="muiM")
    muim = m.addVars(keys_DatG,  ub=UP, vtype=GRB.CONTINUOUS, name="muim")
    mujM = m.addVars(keys_DatGN, ub=UP, vtype=GRB.CONTINUOUS, name="mujM")
    mujm = m.addVars(keys_DatGN, ub=UP, vtype=GRB.CONTINUOUS, name="mujm")
    muwM = m.addVars(keys_T,     ub=UP, vtype=GRB.CONTINUOUS, name="muwM")
    muwm = m.addVars(keys_T,     ub=UP, vtype=GRB.CONTINUOUS, name="muwm")
    murM = m.addVars(keys_Br,    ub=UP, vtype=GRB.CONTINUOUS, name="murM")
    murm = m.addVars(keys_Br,    ub=UP, vtype=GRB.CONTINUOUS, name="murm")

    s1   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s1")
    s2   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s2")
    s3   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s3")
    s4   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s4")
    s5   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s5")
    s6   = m.addVars(keys_DatG,  lb=0, vtype=GRB.CONTINUOUS, name="s6")
    s7   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s7")
    s8   = m.addVars(keys_DatGN, lb=0, vtype=GRB.CONTINUOUS, name="s8")
    s9   = m.addVars(keys_Br,    lb=0, vtype=GRB.CONTINUOUS, name="s9")  
    s10  = m.addVars(keys_Br,    lb=0, vtype=GRB.CONTINUOUS, name="s10")
    s11  = m.addVars(keys_T,     lb=0, vtype=GRB.CONTINUOUS, name="s11")
    s12  = m.addVars(keys_T,     lb=0, vtype=GRB.CONTINUOUS, name="s12")

    # ======================================================================================== #

    #                                    Objective Function

    # ======================================================================================== #

    obj = LinExpr(0.0)

    # Investments and Strategic Capacities of GenCo f
    obj += quicksum(Ij[j]*uj[j]                          for j in keys_DatGN if j[1] == GenCo)
    obj += quicksum(ci[i]*sig[i]*gi[i]                   for i in keys_DatG if i[1] == GenCo)
    obj += quicksum(cj[j]*sigj[j]*gj[j]                  for j in keys_DatGN if j[1] == GenCo)

    # Penalty for Load Shedding
    obj += quicksum(gamma_f*w[t]                         for t in keys_T)

    # Weighted Variable Generation Costs (GenCo and Competitors)
    obj -= quicksum(sig[i]*ci[i]*gi[i]                   for i in keys_DatG if i[1] != GenCo)
    obj -= quicksum(sigj[j]*cj[j]*gj[j]                  for j in keys_DatGN if j[1] != GenCo)

    # Capacity Constraints of Competing GenCos
    obj -= quicksum(muiM[i]*varXi[i]                     for i in keys_DatG if i[1] != GenCo)
    obj += quicksum(muim[i]*g_min[i]                     for i in keys_DatG if i[1] != GenCo)
    obj -= quicksum(mujM[j]*varXj[j]                     for j in keys_DatGN if j[1] != GenCo)

    # Sensitivity to Branch Limits
    obj += quicksum(murm[r]*f_min[r]                     for r in keys_Br)
    obj -= quicksum(murM[r]*f_max[r]                     for r in keys_Br)

    # Sensitivity to Load Shedding
    obj += quicksum(gamma*(L[t] - w[t])                  for t in keys_T)
    obj -= quicksum(muwm[t]*L[t]                         for t in keys_T)

    # To avoid false activation of binary variables
    #obj += 1e-9*quicksum(uj[j] for j in keys_DatGN if j[1]==GenCo)

    m.setObjective(obj, GRB.MINIMIZE)

    # ======================================================================================== #

    #                                   Primal Constraints

    # ======================================================================================== #

    #eq2b: X_fj <= u_fj * g_Nmax (solo GenCo)
    m.addConstrs((Xj[j] <= uj[j]*g_Nmax[j] for j in keys_DatGN if j[1] == GenCo), name="eq2b")

    # eq2c: g_min <= X_fi <= g_max (solo GenCo)
    m.addConstrs((Xi[i] >= g_min[i] for i in keys_DatG if i[1] == GenCo), name="eq2c_lo")
    m.addConstrs((Xi[i] <= g_max[i] for i in keys_DatG if i[1] == GenCo), name="eq2c_hi" )

    # eq2d: sum_t u_fj[t,GenCo,j] = 1 for all j in GenCo
    #m.addConstr(quicksum(uj[j] for j in keys_DatGN if j[1] == GenCo) == 1, name="eq2d")
    J_GenCo = sorted({j for (t,f,j) in keys_DatGN if f == GenCo})
    for j in J_GenCo:
        m.addConstr(quicksum(uj[(t,GenCo,j)] for t in keys_T if (t,GenCo,j) in keys_DatGN) == 1)

    # eq4b: sum_t g_i[t,f,i] + sum_t g_j[t,f,j] = L[t] - w[t]
    m.addConstrs((quicksum(gi[i] for i in keys_DatG  if i[0] == t and i[1] == GenCo) +
        quicksum(gj[j] for j in keys_DatGN if j[0] == t and j[1] == GenCo) + 
        quicksum(gi[i] for i in keys_DatG  if i[0] == t and i[1] != GenCo ) +
        quicksum(gj[j] for j in keys_DatGN if j[0] == t and j[1] != GenCo) 
        == L[t] - w[t] for t in keys_T), name="eq4b")

    # eq4c: g_min <= g_i <= Xi (GenCo)
    m.addConstrs((gi[i] >= g_min[i] for i in keys_DatG if i[1] == GenCo), name="eq4c_lo")
    m.addConstrs((gi[i] <= Xi[i] for i in keys_DatG if i[1] == GenCo), name="eq4c_hi")

    m.addConstrs((gj[j1] <= quicksum(Xj.get((s, j1[1], j1[2]), 0.0) for s in sorted({k[0] for k in keys_DatGN
                            if k[1] == j1[1] and k[2] == j1[2] and k[0] <= j1[0]}))
                            for j1 in keys_DatGN if j1[1] == GenCo),name="eq4d_hi")

    # eq4d: 0 <= g_j <= sum_{tfj}Xj (GenCo)
    m.addConstrs((gj[j] >= 0 for j in keys_DatGN if j[1] == GenCo), name="eq4d_lo")
    m.addConstrs((gj[j1] <= quicksum(Xj[j] for j in keys_DatGN if j[1] == GenCo) for j1 in keys_DatGN if j1[1] == GenCo), name="eq4d_hj")

    # eq4e: g_min <= g_i <= varXi (!= GenCo)
    m.addConstrs((gi[i] >= g_min[i] for i in keys_DatG if i[1] != GenCo), name="eq4e_lo")
    m.addConstrs((gi[i] <= varXi[i] for i in keys_DatG if i[1] != GenCo), name="eq4e_hi")

    # eq4f: 0 <= g_j <= varXj (!= GenCo)
    m.addConstrs((gj[j] >= 0 for j in keys_DatGN if j[1] != GenCo), name="eq4f_lo")
    m.addConstrs((gj[j] <= varXj[j] for j in keys_DatGN if j[1] != GenCo), name="eq4f_hi")

    # eq3a-3c: sum_r ptdf[r]*( sum_i g_i[t,r,ni] + sum_j g_j[t,r,nj] - sum_z rho[z,nz]*psi[z,nz] ) = flow[t,r]
    m.addConstrs((
        flow[(t,br)] == quicksum(
            ptdf.get((t,br,n), 0.0) * (
                quicksum(gi[i] for i in keys_DatG  if i[0] == t and ni[i] == n and i[1] == GenCo) +
                quicksum(gj[j] for j in keys_DatGN if j[0] == t and nj[j] == n and j[1] == GenCo) +
                quicksum(gi[i] for i in keys_DatG  if i[0] == t and ni[i] == n and i[1] != GenCo) +
                quicksum(gj[j] for j in keys_DatGN if j[0] == t and nj[j] == n and j[1] != GenCo) -
                quicksum(rho[(z,n)]*psi[(z,n)]*(L[t] - w[t]) for (z,n2) in keys_DatZ if n2 == n)
            )
            for n in keys_N
        )
        for (t,br) in keys_Br
    ), name="eqPTDF")

    # eq4g: f_min[t,r] <= flow[t,r] <= f_max[t,r] (branch limits)
    m.addConstrs((flow[r] >= f_min[r] for r in keys_Br), name="eq4g_lo")
    m.addConstrs((flow[r] <= f_max[r] for r in keys_Br), name="eq4g_hi")

    # eq4i: lmp[t,n] == lambda[t] + sum_{t,r,n}ptdf*(murM[t,r] - murm[t,r])
    m.addConstrs((lmp[(t, n)] == lambda_t[t] +
                quicksum(ptdf.get((tt, r, n), 0.0)*(murM[(tt, r)] - murm[(tt, r)])
                for (tt, r, nn) in keys_Dat_Br if tt == t and nn == n )
                for n in keys_N
                for t in keys_T), name="eq4i")

    # eq4h: 0 <= w[t] <= L[t]
    m.addConstrs((w[t] >= 0 for t in keys_T), name="eq4h_lo")
    m.addConstrs((w[t] <= L[t] for t in keys_T), name="eq4h_hi")

    # ======================================================================================== #

    #                                   Dual Constraints

    # ======================================================================================== #

    # eq6d: sig[i]*ci[i] + lambda_t[t] + sum_r ptdf[t,r,n]*(murM[t,r] - murm[t,r]) - muim[i] + muiM[i] = 0 (solo GenCo)
    m.addConstrs((sig[i]*ci[i] + lmp[i[0],ni[i]] - muim[i] + muiM[i] == 0 for i in keys_DatG if i[1] == GenCo), name="eq6d")

    # eq6e: sigj[j]*cj[j] + lmp[t] + sum_r ptdf[t,r,nj[j]]*(murM[t,r] - murm[t,r]) - mujm[j] + mujM[j] = 0 (solo GenCo)
    m.addConstrs((sigj[j]*cj[j] + lmp[j[0],nj[j]] - mujm[j] + mujM[j]== 0 for j in keys_DatGN if j[1] == GenCo), name="eq6e")

    # eq6f: sig[i]*ci[i] + lmp[t] + sum_r ptdf[t,r,n]*(murM[t,r] - murm[t,r]) - muim[i] + muiM[i] = 0 (solo GenCo)
    m.addConstrs((sig[i]*ci[i] + lmp[i[0], ni[i]] - muim[i] + muiM[i] == 0 for i in keys_DatG if i[1] != GenCo), name="eq6f")

    # eq6g: sigj[j]*cj[j] + lmp[t] + sum_r ptdf[t,r,nj[j]]*(murM[t,r] - murm[t,r]) - mujm[j] + mujM[j] = 0 (solo GenCo)
    m.addConstrs((sigj[j]*cj[j] + lmp[j[0], nj[j]] - mujm[j] + mujM[j]== 0 for j in keys_DatGN if j[1] != GenCo), name="eq6g")

    # eq6h: gamma + lambda_t[t] + sum_n sum_z ptdf[t,r,n]*(murM[t,r] - murm[t,r]) * rho[z,n] * psi[z,n] - muwM[t] + muwm[t] = 0
    m.addConstrs((gamma + lambda_t[t] + 
                quicksum(quicksum(ptdf.get((t, r, n), 0.0) * (murM[t, r] - murm[t, r])
                for r in Br['Br'])*quicksum(rho.get((z, n), 0.0) * psi.get((z, n), 0.0)
                for z in Dat_Z.loc[Dat_Z['N'] == n, 'Z']) for n in N['N'])
                + muwM[t] - muwm[t] == 0 for t in keys_T ), name="eq6h")

    # ======================================================================================== #

    #                                    SOS1 Constraints

    # ======================================================================================== #

    for i in keys_DatG:
        if i[1] == GenCo:
            m.addConstr(Xi[i] - gi[i] == s1[i])
            m.addConstr(muiM[i] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [muiM[i], s1[i]], [1.0, 2.0])

    for i in keys_DatG:
        if i[1] == GenCo:
            m.addConstr(gi[i] - g_min[i] == s2[i])
            m.addConstr(muim[i] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [muim[i], s2[i]], [1.0, 2.0])

    for j in keys_DatGN:  # j = (t, f, gn)
        if j[1] == GenCo:
            m.addConstr(quicksum(Xj.get((s, j[1], j[2]), 0.0)  # X_{s,f,gn}
                for s in sorted({k[0] for k in keys_DatGN if k[1] == j[1] and k[2] == j[2] and k[0] <= j[0]})
                ) - gj[j] == s3[j]) 
            m.addConstr(mujM[j] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [mujM[j], s3[j]], [1.0, 2.0])

    for j in keys_DatGN:
        if j[1] == GenCo:
            m.addConstr(gj[j] == s4[j])
            m.addConstr(mujm[j] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [mujm[j], s4[j]], [1.0, 2.0])

    for i in keys_DatG:
        if i[1] != GenCo:
            m.addConstr(varXi[i] - gi[i] == s5[i])
            m.addConstr(muiM[i] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [muiM[i], s5[i]], [1.0, 2.0])

    for i in keys_DatG:
        if i[1] != GenCo:
            m.addConstr(gi[i] - g_min[i] == s6[i])
            m.addConstr(muim[i] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [muim[i], s6[i]], [1.0, 2.0])

    for j in keys_DatGN:
        if j[1] != GenCo:
            m.addConstr(varXj[j] - gj[j] == s7[j])
            m.addConstr(mujM[j] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [mujM[j], s7[j]], [1.0, 2.0])

    for j in keys_DatGN:
        if j[1] != GenCo:
            m.addConstr(gj[j] == s8[j])
            m.addConstr(mujm[j] >= 0)
            m.addSOS(GRB.SOS_TYPE1, [mujm[j], s8[j]], [1.0, 2.0])
    
    for r in keys_Br:
        m.addConstr(flow[r] - f_min[r] == s9[r])
        m.addConstr(murm[r] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [murm[r],s9[r]], [1.0, 2.0])

    for r in keys_Br:
        m.addConstr(f_max[r] - flow[r] == s10[r])
        m.addConstr(murM[r] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [murM[r],s10[r]], [1.0, 2.0])

    for t in keys_T:
        m.addConstr(L[t] - w[t] == s11[t])
        m.addConstr(muwM[t] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muwM[t],s11[t]], [1.0, 2.0])

    for t in keys_T:
        m.addConstr(w[t] == s12[t])
        m.addConstr(muwm[t] >= 0)
        m.addSOS(GRB.SOS_TYPE1, [muwm[t],s12[t]], [1.0, 2.0])

    # ======================================================================================== #

    #                                    Ejecution Process

    # ======================================================================================== #

    #m.Params.IntFeasTol = 1e-9
    #m.Params.FeasibilityTol = 1e-9
    m.optimize()
    m.write("gepResponse.lp")

    # ======================================================================================== #

    #                               Soluction Information Data

    # ======================================================================================== #

    sol = m.Status
    print(sol)

    # Market Prices
    lmp = {k: v.X for k, v in lmp.items()}
    df_lmp = pd.DataFrame([(*k, v) for k, v in lmp.items()], columns=["T", "N", "LMP"])

    # Consumer's Profit
    Lr = {k: L[k] for k in L.keys()}
    df_Lt = d['Dat_Z'].merge(Dat_D, how = 'cross')
    df_Lt['Ln'] = df_Lt["L"]*df_Lt["rho"]*df_Lt["psi"]
    df_Lt = df_Lt[['T','Z','N','Ln','L']].sort_values(["T","Z","N"]).reset_index(drop=True)
    df_Lt['lmp'] = df_Lt.apply(lambda row: (1)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['N']), 'LMP'].values[0], axis=1)

    wr = {k: v.X for k, v in w.items()}
    df_wr = pd.DataFrame(list(wr.items()), columns=["T", "wr"]).sort_values("T").reset_index(drop=True)
    print(Lr)
    
    # Existing generation capacity of GenCos
    Xi_sol = {k: v.X for k, v in Xi.items() if k[1] == GenCo}
    exGen = Dat_G.loc[Dat_G['F'] == GenCo, ['T','F','G','sig','ni','g_max','ci']]
    gi_sol = {k: v.X for k, v in gi.items() if k[1] == GenCo}
    exGen['gi'] = exGen.apply(lambda row: gi_sol.get((row['T'], row['F'], row['G']), 0.0), axis=1)
    exGen['lmp'] = exGen.apply(lambda row: (1)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['ni']), 'LMP'].values[0], axis=1)
    exGen['Xi'] = exGen.apply(lambda row: Xi_sol.get((row['T'], row['F'], row['G']), 0.0), axis=1)

    # New generation capacity of GenCos
    Xj_sol = {k: v.X for k, v in Xj.items() if k[1] == GenCo}
    newGen = Dat_GN.loc[Dat_G['F'] == GenCo, ['T','F','GN','Ij','sigj','nj','g_Nmax','cj']]
    ujr = {k: v.X for k, v in uj.items()}
    df_uj = pd.DataFrame([(*k, v) for k, v in ujr.items()], columns=["T", "F", "GN", "uj"])
    gj_sol = {k: v.X for k, v in gj.items() if k[1] == GenCo}
    newGen['gj'] = newGen.apply(lambda row: gj_sol.get((row['T'], row['F'], row['GN']), 0.0), axis=1)
    newGen['lmp'] = newGen.apply(lambda row: (1)*df_lmp.loc[(df_lmp['T'] == row['T']) & (df_lmp['N'] == row['nj']), 'LMP'].values[0], axis=1)
    newGen['Xj'] = newGen.apply(lambda row: Xj_sol.get((row['T'], row['F'], row['GN']), 0.0), axis=1)
    newGen['uj'] = newGen.apply(lambda row: df_uj.loc[(df_uj['T'] == row['T']) & (df_uj['GN'] == row['GN']), 'uj'].values[0], axis=1)

    # Transmission information results
    f_sol = {k: v.X for k, v in flow.items()}
    murM_rslt = {k: v.X for k, v in murM.items()}
    murm_rslt = {k: v.X for k, v in murm.items()}
    flow_rslt = Lim_Br.copy()
    flow_rslt['flow'] = flow_rslt.apply(lambda row: f_sol.get((row['T'], row['Br']), 0.0), axis=1)
    flow_rslt['murM'] = flow_rslt.apply(lambda row: murM_rslt.get((row['T'], row['Br']), 0.0), axis=1)/8760
    flow_rslt['murm'] = flow_rslt.apply(lambda row: murm_rslt.get((row['T'], row['Br']), 0.0), axis=1)/8760
    flow_rslt = flow_rslt[['T','Br','f_max','flow','f_min','murM','murm']]
    
    results = {
        "obj": m.ObjVal,
        "Sol" : m.Status,
        "Xi": exGen,
        "Xj": newGen,
        "LMP": df_lmp,
        "Lnodal" : df_Lt,
        "wr" : df_wr,
        "grid" : flow_rslt,
    }

    return results





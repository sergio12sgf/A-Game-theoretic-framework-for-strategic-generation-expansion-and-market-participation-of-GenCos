import pandas as pd
from model_strGEP import model
import numpy as np

def exp_rslt(iTER,m,exp_Xi,exp_Xj):
    
    XiT = m['Xi'].groupby(['T','F'], as_index=False)['Xi'].sum().rename(columns={'Xi':'Xi_T'})
    XjT = m['Xj'].groupby(['T','F'], as_index=False)['Xj'].sum().rename(columns={'Xj':'Xj_T'})
    XjT['Xj_T'] = XjT.groupby('F')['Xj_T'].cummax()

    for r in XiT.itertuples(index=False):
        exp_Xi.loc[len(exp_Xi)] = [iTER+1, int(r.T), r.F, float(r.Xi_T)]

    for r in XjT.itertuples(index=False):
        exp_Xj.loc[len(exp_Xj)] = [iTER+1, int(r.T), r.F, float(r.Xj_T)]
    
    df_data = {
        "expXi": exp_Xi,
        "expXj": exp_Xj,
    }

    return df_data

def results(Xr, pGenCo, iTER, m):

    df_Xi = m['Xi']
    df_Xj = m['Xj']

    #####################################################
    # Total generation capacity by period and GenCo
    #####################################################
    XiT = m['Xi'].groupby(['T','F'], as_index=False)['Xi'].sum().rename(columns={'Xi':'Xi_T'})
    XjT = m['Xj'].groupby(['T','F'], as_index=False)['Xj'].sum().rename(columns={'Xj':'Xj_T'})
    XjT['Xj_T'] = XjT.groupby('F')['Xj_T'].cummax()

    Xtot = (XiT.set_index(['T','F'])['Xi_T'].add(XjT.set_index(['T','F'])['Xj_T'], fill_value=0.0)).reset_index().rename(columns={0:'X_total'})
            
    for r in Xtot.itertuples(index=False):
        Xr.loc[len(Xr)] = [iTER+1, int(r.T), r.F, float(r.X_total)]

    #####################################################
    #   GenCo's Profit
    #####################################################
    df_Xi['Profit'] = df_Xi.apply(lambda r: (r['ci']*r['sig'] - r['lmp'])*r['gi'], axis=1)
    df_Xj['Profit'] = df_Xj.apply(lambda r: (r['cj']*r['sigj'] - r['lmp'])*r['gj'] + r['Ij']*r['uj'], axis=1)

    df_XiT = df_Xi['Profit'].groupby([df_Xi['T'], df_Xi['F']]).sum().reset_index(name='Profit_i')
    df_XjT = df_Xj['Profit'].groupby([df_Xj['T'], df_Xj['F']]).sum().reset_index(name='Profit_j')
    Pgenco = (df_XiT.set_index(['T','F'])['Profit_i'].add(df_XjT.set_index(['T','F'])['Profit_j'], fill_value=0.0)).reset_index().rename(columns={0:'Profit_total'})
    
    for r in Pgenco.itertuples(index=False):
        pGenCo.loc[len(pGenCo)] = [iTER+1, int(r.T), r.F, float(r.Profit_total)]

    df_data = {
        "Xr": Xr,
        "pGenCo": pGenCo,
    }

    return df_data

def consumerP(iTER, Lnodal_iTER, m):

    #####################################################
    #    Consumer's Profit
    #####################################################
    L = m['Lnodal']
    L['Profit'] = L.apply(lambda r: r['Ln']*r['lmp'], axis=1)
    L = L['Profit'].groupby(L['T']).sum().reset_index(name='Profit_c')

    for r in L.itertuples(index=False):
        Lnodal_iTER.loc[len(Lnodal_iTER)] = [iTER+1, int(r.T), float(r.Profit_c)]

    return Lnodal_iTER

def market_index(iTER, Lerner, HHi, m):
    df_Xi = m['Xi'].copy()
    df_Xj = m['Xj'].copy()

    # HHi information process
    df_Xj["Xj"] = df_Xj.groupby(["F","GN"])["Xj"].cummax()
    xi_TF = df_Xi.groupby(['T','F'], as_index=False)['Xi'].sum()
    xj_TF = df_Xj.groupby(['T','F'], as_index=False)['Xj'].sum()
    cap_TF = xi_TF.merge(xj_TF, on=['T','F'], how='outer').fillna(0.0)
    cap_TF['Xt'] = cap_TF['Xi'] + cap_TF['Xj']

    for r in cap_TF.itertuples(index=False):
        HHi.loc[len(HHi)] = [iTER+1, int(r.T), r.F, float(r.Xt)]

    # Lerner index calculation
    df_Xi['Lerner'] = np.where(df_Xi['lmp'] != 0,(-df_Xi['lmp']/8760.0 - df_Xi['ci']) / (-df_Xi['lmp']/8760.0), np.nan)
    df_Xj['Lerner'] = np.where(df_Xj['lmp'] != 0,(-df_Xj['lmp']/8760.0 - df_Xj['cj']) / (-df_Xj['lmp']/8760.0), np.nan)
    lerner = pd.concat([df_Xi[['T','F','G','Lerner']], df_Xj[['T','F','GN','Lerner']].rename(columns={'GN':'G'})], ignore_index=True)
    
    for r in lerner.itertuples(index=False):
        Lerner.loc[len(Lerner)] = [iTER+1, int(r.T), r.F, r.G, float(r.Lerner)]

    df_data = {
        "HHi": HHi,
        "Lerner": Lerner,
    }

    return df_data

def best_response(d,iterations,epsilon):

    sol = pd.DataFrame(columns=['iTER','F','Sol'])
    Xr = pd.DataFrame(columns=["iTER","T","F","X_total"])                    # Total capacity results
    pGenCo = pd.DataFrame(columns=["iTER","T","F","Profit_total"])           # Profit results
    lmp_r = pd.DataFrame(columns=["iTER","T", "N","LMP"])                    # LMP results
    Lnodal_iTER = pd.DataFrame(columns=['iTER','T','Profit'])                # Consumer's profit
    wr_iTER = pd.DataFrame(columns=['iTER', 'T', 'wr'])                      # Load shedding results
    exp_Xi = pd.DataFrame(columns=['iTER', 'T', 'F', 'Xi'])                  # Existing capacity results
    exp_Xj = pd.DataFrame(columns=['iTER', 'T', 'F', 'Xj'])                  # New capacity results
    Lerner = pd.DataFrame(columns=['iTER','T','F','G','Lerner'])             # Lerner index
    HHi = pd.DataFrame(columns=['iTER','T','F','Xt'])
    
    vXi = {(r.T, r.F, r.G): r.g_max for r in d['Dat_G'].itertuples(index=False)}
    vXj = {(r.T, r.F, r.GN): r.g_Nmax for r in d['Dat_GN'].itertuples(index=False)}

    # Diagonalization algorithm 
    for iTER in range(iterations):

        print("\n=======================================================================\n")
        print("\n                     Iteration: " + str(iTER + 1) + "\n")
        print("\n=======================================================================\n")

        for f in d['F'].values.flatten():

            print("\n                     GenCo: " + str(f) + "\n")
            m = model(d,vXi,vXj,f)

            for r in m['Xi'].itertuples(index=False):
                vXi[(r.T, r.F, r.G)] = r.Xi
            
            Xj_df = (m["Xj"].copy().astype({"T": int}).sort_values(["F","GN","T"]))
            Xj_df["Xj"] = Xj_df.groupby(["F","GN"])["Xj"].cummax()                        

            for r in Xj_df.itertuples(index=False):
                if r.F == f:
                    vXj[(int(r.T), r.F, r.GN)] = float(r.Xj)

            # Preparing results m is the vector that contains the dataFrames from model_strGEP
            sol.loc[len(sol)] = [(iTER+1), f, m['obj']]
            dataResults = results(Xr, pGenCo, iTER, m)
            expResults = exp_rslt(iTER, m, exp_Xi, exp_Xj)
            XiTER = dataResults['Xr']
            piTER = dataResults['pGenCo']
            expXi = expResults['expXi']
            expXj = expResults['expXj']
            marketIndex = market_index(iTER, Lerner, HHi, m)
        
        LiTER = consumerP(iTER, Lnodal_iTER, m)    
        df_lmp = m['LMP']
        df_lmp['lmp'] = -df_lmp['LMP']/8760

        # LMP results
        for r in df_lmp.itertuples(index=False):
            lmp_r.loc[len(lmp_r)] = [iTER+1, int(r.T), r.N, float(r.lmp)]

        # Load shedding results
        for r in m['wr'].itertuples(index=False):
            wr_iTER.loc[len(wr_iTER)] = [iTER+1, int(r.T), float(r.wr)]

        # HHi index
        HHi_data = marketIndex['HHi'].copy()
        total_Xt = HHi_data.groupby(['iTER', 'T'])['Xt'].transform('sum')
        HHi_data['s'] = HHi_data['Xt']/total_Xt
    
        # Convergence analysis 
        wide = sol.pivot(index='iTER', columns='F', values='Sol').sort_index()

        if wide.shape[0] >= 2:
            delta = ((wide.iloc[-1] - wide.iloc[-2])).abs()
            if delta.le(epsilon).all() or iTER == iterations:
                print(f"Convergence iteration = {iTER + 1}")
                Xtotal = XiTER[XiTER['iTER'] == iTER + 1]
                Profit = piTER[piTER['iTER'] == iTER + 1]
                lmpT = lmp_r[lmp_r['iTER'] == iTER + 1]
                Profit_consumer = LiTER[LiTER['iTER'] == iTER + 1]
                wr_best = wr_iTER[wr_iTER['iTER'] == iTER + 1]
                expXitotal = expXi[expXi['iTER'] == iTER + 1]
                expXjtotal = expXj[expXj['iTER'] == iTER + 1]
                HHi_total = HHi_data[HHi_data['iTER'] == iTER +1]
                Lerner_total = marketIndex['Lerner'][marketIndex['Lerner']['iTER'] == iTER +1]
                break

    df_results = {
        "Xtotal": Xtotal,
        "Profit": Profit,
        "LMP": lmpT,
        "Profit_consumer" : Profit_consumer,
        'wr_best' : wr_best,
        'exp_Xi' : expXitotal,
        'exp_Xj' : expXjtotal,
        'HHi' : HHi_total,
        'Lerner' : Lerner_total,
    }

    return df_results
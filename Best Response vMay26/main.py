# --------------------------------------------
# Begin: Imports and Runtime Configuration
# --------------------------------------------

from system import system
from dataModel import data
# *** Ajuste 2026-05-06: usa el traductor de estados para imprimir resultados compactos.
from bestResponse import consumerP, gurobi_status_name
import bestResponse as bR
import cpGEP as pcgep
from results import totCap, profit, boxplot, consumerProfit, bar_chartCapacity, HHi_index, Lerner_index
import pandas as pd
import time

pd.set_option("display.max_rows", None)        # muestra todas las filas
pd.set_option("display.max_columns", None)     # muestra todas las columnas
pd.set_option("display.width", 0)              # evita cortes por ancho de consola
pd.set_option("display.max_colwidth", None)    # no limites el ancho de celdas

# --------------------------------------------
# End: Imports and Runtime Configuration
# --------------------------------------------


# --------------------------------------------
# Begin: Sensitivity Analysis Orchestrator
# --------------------------------------------

def sensitivity_Analysis(sist,iterations,epsilon,parameter,stress_test,element):

    # --------------------------------------------
    # Begin: Input Data and Result Tables
    # --------------------------------------------

    file = system(sist)
    d = data(file)

    Xr = pd.DataFrame(columns=["Srio","iTER","T","F","X_total"])
    pGenCo = pd.DataFrame(columns=["Srio","iTER","T","F","Profit_total"])
    Xr2 = pd.DataFrame(columns=["Srio","iTER","T","F","X_total"])
    pGenCo2 = pd.DataFrame(columns=["Srio","iTER","T","F","Profit_total"])
    lmp_r = pd.DataFrame(columns=["Srio","iTER","T","N","LMP"])
    L_profit = pd.DataFrame(columns=["Srio",'iTER','T','Profit'])
    L_profit2 = pd.DataFrame(columns=["Srio",'iTER','T','Profit'])
    wr_f = pd.DataFrame(columns=["Srio",'iTER','T','wr'])
    expXitotal = pd.DataFrame(columns=['Srio','iTER','T','F','Xi'])
    expXjtotal = pd.DataFrame(columns=['Srio','iTER','T','F','Xj'])
    GenCo_hhi = pd.DataFrame(columns=['Srio','iTER','T','F','Xt','s'])
    Lerner = pd.DataFrame(columns=['Srio','iTER','T','F','G','Lerner'])
    demand_srio = pd.DataFrame(columns=['Srio','T','L'])
    st = 0

    # --------------------------------------------
    # End: Input Data and Result Tables
    # --------------------------------------------

    # --------------------------------------------
    # Begin: Scenario Parameter Selection
    # --------------------------------------------

    if parameter == "gamma":
        param = d['cParams']['gamma_f']
        text = "Withholding penalty variation"
        st = 0

    if parameter == "Demand":
        param = d['Dat_D']['L']
        d['cParams']['gamma_f'] = d['cParams']['gamma_f']
        text = "Demand variation"
        st = 1

    if parameter == "grid":
        param = d['Lim_Br'].copy()
        mask = param['Br'] == element
        text = "Grid element "  + str(element) + " variation"
        st = 2

    # --------------------------------------------
    # End: Scenario Parameter Selection
    # --------------------------------------------

    # --------------------------------------------
    # Begin: Strategic Best-Response Scenario Loop
    # --------------------------------------------
    
    for k in stress_test:
        ini_time = time.perf_counter()
        # *** Ajuste 2026-05-06: imprime solo el caso de analisis que se esta resolviendo.
        print(f"\nAnalisis: {text} | sistema {sist} | escenario {k}")
        if st == 0:
            d['cParams']['gamma_f'] = param*k
        if st == 1: 
            d['Dat_D']['L'] = param*k
        if st == 2:
            a = param.copy()
            d['Lim_Br'].loc[mask, ['f_max', 'f_min']] = a.loc[mask, ['f_max', 'f_min']] * k

        strGEP = bR.best_response(d,iterations,epsilon)                     # Best Response ejecution   
        
        X_data = strGEP['Xtotal'].copy()
        p_data = strGEP['Profit'].copy()
        lmp = strGEP['LMP'].copy()
        L_prof = strGEP['Profit_consumer'].copy()
        dfwr = strGEP['wr_best'].copy()
        expXi = strGEP['exp_Xi'].copy()
        expXj = strGEP['exp_Xj'].copy()
        HHi = strGEP['HHi'].copy()
        lerner = strGEP['Lerner'].copy()
        demand = d['Dat_D'].copy()

        # Total GenCos's generation capacity results
        for r in X_data.itertuples(index=False):
            Xr.loc[len(Xr)] = [k, r.iTER, r.T, r.F, r.X_total]

        # GenCo's profit results
        for r in p_data.itertuples(index=False):
            pGenCo.loc[len(pGenCo)] = [k, r.iTER, r.T, r.F, r.Profit_total]

        # LMPs
        for r in lmp.itertuples(index=False):
            lmp_r.loc[len(lmp_r)] = [k, r.iTER, int(r.T), r.N, float(r.LMP)]

        # Profit_Consumer
        for r in L_prof.itertuples(index=False):
            L_profit.loc[len(L_profit)] = [k, r.iTER, int(r.T), float(r.Profit)]

        # Load shedding
        for r in dfwr.itertuples(index=False):
            wr_f.loc[len(wr_f)] = [k, r.iTER, int(r.T), float(r.wr)]

        # Existing GenCos's generation capacity results
        for r in expXi.itertuples(index=False):
            expXitotal.loc[len(expXitotal)] = [k, r.iTER, r.T, r.F, r.Xi]
        
        # New GenCos's generation capacity results
        for r in expXj.itertuples(index=False):
            expXjtotal.loc[len(expXjtotal)] = [k, r.iTER, r.T, r.F, r.Xj]

        # HHi index
        for r in HHi.itertuples(index=False):
            GenCo_hhi.loc[len(GenCo_hhi)] = [k, r.iTER, r.T, r.F, r.Xt, r.s]

        # Lerner index
        for r in lerner.itertuples(index=False):
            Lerner.loc[len(Lerner)] = [k, r.iTER, int(r.T), r.F, r.G, float(r.Lerner)]

        for r in demand.itertuples(index=False):
            demand_srio.loc[len(demand_srio)] = [k, r.T, r.L]

    # --------------------------------------------
    # End: Strategic Best-Response Scenario Loop
    # --------------------------------------------

    # --------------------------------------------
    # Begin: Strategic Results Plotting
    # --------------------------------------------

    ymax = pGenCo['Profit_total'].max()
    yXmax = Xr['X_total'].max()

    end_time = time.perf_counter()
    print(f"Tiempo de ejecución: {end_time - ini_time:.2f} segundos")

    totCap(Xr,wr_f,yXmax, text, sist)
    profit(pGenCo, ymax, text, sist)
    bar_chartCapacity(expXitotal,expXjtotal,demand_srio,text,sist) 
    boxplot(lmp_r, text, sist)

    if text == "Demand variation" or text == "Grid element "  + str(element) + " variation":
        HHi_index(GenCo_hhi,text,sist)
        Lerner_index(Lerner,text,sist)

    # --------------------------------------------
    # End: Strategic Results Plotting
    # --------------------------------------------

    # --------------------------------------------
    # Begin: Perfect Competition Benchmark
    # --------------------------------------------

    if parameter == "Demand": #or parameter == "grid": 

        sistPC = str(sist) + "_PC"    
        lmp_rCP = pd.DataFrame(columns=["Srio","T","N","LMP"])
        wr_fcp = pd.DataFrame(columns=["Srio",'T','wr'])
        expXitotalPC = pd.DataFrame(columns=['Srio','iTER','T','F','Xi'])
        expXjtotalPC = pd.DataFrame(columns=['Srio','iTER','T','F','Xj'])

        for k in stress_test:
            # *** Ajuste 2026-05-06: imprime el caso de competencia perfecta sin log extenso.
            print(f"\nAnalisis: {text} | sistema {sistPC} | escenario {k}")

            if parameter == "Demand":
                d['Dat_D']['L'] = param*k
            if parameter == "grid":
                a = param.copy()
                d['Lim_Br'].loc[mask, ['f_max', 'f_min']] = a.loc[mask, ['f_max', 'f_min']] * k
            
            mpc = pcgep.model(d)
            # *** Ajuste 2026-05-06: reporta el estado final de competencia perfecta.
            print(f"  Competencia perfecta: {gurobi_status_name(mpc['Sol'])}")

            lmp = mpc['LMP'].copy()
            X_data = mpc['Xr'].copy()
            p_data = mpc['Profit'].copy()
            L_prof2 = mpc['Lnodal'].copy()
            dfwrCP = mpc['wr'].copy()
            expXic = mpc['Xi'].copy()
            expXjc = mpc['Xj'].copy()

            lmp['LMP'] = -1*lmp['LMP']/8760
            Lnodal_iTER = pd.DataFrame(columns=['iTER','T','Profit'])
            
            # GenCos's generation capacity results
            for r in X_data.itertuples(index=False):
                Xr2.loc[len(Xr2)] = [k, r.iTER, r.T, r.F, r.X_total]

            # GenCo's profit results
            for r in p_data.itertuples(index=False):
                pGenCo2.loc[len(pGenCo2)] = [k, r.iTER, r.T, r.F, r.Profit_total]

            for r in lmp.itertuples(index=False):
                lmp_rCP.loc[len(lmp_rCP)] = [k, int(r.T), r.N, float(r.LMP)]

            # Profit_Consumer
            m2 = {"Lnodal" : L_prof2}
            L = consumerP(0, Lnodal_iTER, m2)
            
            for r in L.itertuples(index=False):
                L_profit2.loc[len(L_profit2)] = [k, r.iTER, int(r.T), float(r.Profit)]

            # Load shedding
            for r in dfwrCP.itertuples(index=False):
                wr_fcp.loc[len(wr_fcp)] = [k, int(r.T), float(r.wr)]

            # Existing GenCos's generation capacity results
            for r in expXic.itertuples(index=False):
                expXitotalPC.loc[len(expXitotalPC)] = [k, r.iTER, int(r.T), r.F, r.Xi]

            # New GenCos's generation capacity results
            for r in expXjc.itertuples(index=False):
                expXjtotalPC.loc[len(expXjtotalPC)] = [k, r.iTER, int(r.T), r.F, r.Xj]

        if pGenCo['Profit_total'].max() > 0:
            ymax = pGenCo['Profit_total'].max()
        else: 
            ymax = pGenCo2['Profit_total'].max()

        if Xr['X_total'].max() > 0:
            yXmax = Xr['X_total'].max()
        else:
            yXmax = Xr2['X_total'].max()

        totCap(Xr2, wr_f, yXmax, text,sist=sistPC)
        bar_chartCapacity(expXitotalPC,expXjtotalPC,demand_srio,text,sist=sistPC) 
        profit(pGenCo2, ymax, text, sist=sistPC) 
        boxplot(lmp_rCP,text,sist=sistPC)
        consumerProfit(L_profit, L_profit2,sist=sistPC)

    # --------------------------------------------
    # End: Perfect Competition Benchmark
    # --------------------------------------------

# --------------------------------------------
# End: Sensitivity Analysis Orchestrator
# --------------------------------------------


# --------------------------------------------
# Begin: Script Execution Configuration
# --------------------------------------------

sist = 24
iterations = 200
epsilon = 1e-3

stress_test = [0, 0.25, 0.5, 0.75, 1, 2]
parameter = "gamma"
#ini_time = time.perf_counter()
sensitivity_Analysis(sist,iterations,epsilon,parameter,stress_test,element=None)

stress_test = [0.90, 0.95, 1, 1.05, 1.10, 1.15, 1.20]
parameter = "Demand"
#ini_time = time.perf_counter()
sensitivity_Analysis(sist,iterations,epsilon,parameter,stress_test,element=None)

if sist == 24:
    ini_time = time.perf_counter()
    stress_test = [0,0.50, 0.75, 1, 1.50, 2.00]
    element = 'D1_16_19'
    parameter = "grid"
    sensitivity_Analysis(sist,iterations,epsilon,parameter,stress_test,element)

if sist == 24:
    ini_time = time.perf_counter()
    stress_test = [0,0.50, 0.75, 1, 1.50, 2.00]
    element = 'B6_9_12'
    parameter = "grid"
    sensitivity_Analysis(sist,iterations,epsilon,parameter,stress_test,element)

# --------------------------------------------
# End: Script Execution Configuration
# --------------------------------------------

import pandas as pd
from gurobipy import Model, GRB

# ----------------------
# Datos estilo AMPL
# ----------------------
datos = pd.DataFrame([
    [1, 'F1', 'G1', 1, 1, 8, 2, 9],
    [1, 'F2', 'G2', 2, 1, 5, 2, 9],
    [2, 'F1', 'G1', 1, 1, 8, 2, 9],
    [2, 'F2', 'G2', 2, 1, 5, 2, 9],
    [3, 'F1', 'G1', 1, 1, 8, 2, 9],
    [3, 'F2', 'G2', 2, 1, 5, 2, 9],
], columns=['t', 'f', 'g', 'ni', 'sig', 'ci', 'g_min', 'g_max'])

# Demanda por periodo
demanda = {1: 15, 2: 15, 3: 15}

# Crear modelo
m = Model("DespachoMultiperiodo")
m.setParam('OutputFlag', 0)

# ----------------------
# Variables
# ----------------------
g_vars = {}
for idx, row in datos.iterrows():
    key = (row['t'], row['f'], row['g'])
    g_vars[key] = m.addVar(lb=row['g_min'], ub=row['g_max'], name=f"g_{key[0]}_{key[1]}_{key[2]}")

# ----------------------
# Restricciones de demanda por periodo
# ----------------------
T = datos['t'].unique()
for t in T:
    m.addConstr(
        sum(g_vars[key] for key in g_vars if key[0] == t) == demanda[t],
        name=f"demanda_{t}"
    )

# ----------------------
# Función objetivo
# ----------------------
m.setObjective(
    sum(g_vars[(row['t'], row['f'], row['g'])] * row['ci'] for _, row in datos.iterrows()),
    GRB.MINIMIZE
)

# ----------------------
# Resolver
# ----------------------
m.optimize()

# ----------------------
# Resultados
# ----------------------
datos['Despacho'] = datos.apply(lambda row: g_vars[(row['t'], row['f'], row['g'])].X, axis=1)
datos['Costo Parcial'] = datos['Despacho'] * datos['ci']

print(datos[['t', 'f', 'g', 'Despacho', 'Costo Parcial']])
print(f"\nCosto total del despacho: ${m.ObjVal:.2f}")

from pathlib import Path

def system(nodes):
    if nodes == 3: 
        file = r"D:/10368.CENACE/My Documents/GitHub/Phd-reserch/Articulo 1/Modelo AMPL vJul2025/Python Gurobi/3nodos_gurobi.xlsx"
        #file = r"/Users/sergiogodinez/Documents/GitHub/Phd-reserch/Articulo 1/Modelo AMPL vJul2025/Python Gurobi/3nodos_gurobi.xlsx"
    if nodes == 24:
        file = r"D:/10368.CENACE/My Documents/GitHub/Phd-reserch/Articulo 1/Modelo AMPL vJul2025/Python Gurobi/24nodos_gurobi.xlsx"
        #file = r"/Users/sergiogodinez/Documents/GitHub/Phd-reserch/Articulo 1/Modelo AMPL vJul2025/Python Gurobi/24nodos_gurobi.xlsx"

    base_dir = Path(file).parent
    figures_dir = base_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    sist = "sist_" + str(nodes)
    figures_sist = figures_dir / sist
    figures_sist.mkdir(parents=True, exist_ok=True)
    
    return file
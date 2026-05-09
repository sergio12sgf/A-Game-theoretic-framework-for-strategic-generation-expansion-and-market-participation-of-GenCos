from pathlib import Path

# --------------------------------------------
# Begin: Project Paths Configuration
# --------------------------------------------

# *** Ajuste 2026-05-06: detecta la carpeta raiz del proyecto sin depender del sistema operativo.
PROJECT_ROOT = Path(__file__).resolve().parent

# *** Ajuste 2026-05-06: centraliza los archivos de datos por sistema.
SYSTEM_FILES = {
    3: "3nodos_gurobi.xlsx",
    24: "24nodos_gurobi.xlsx",
}

# --------------------------------------------
# End: Project Paths Configuration
# --------------------------------------------


# --------------------------------------------
# Begin: System Data File Resolver
# --------------------------------------------

def system(Number_nodes):
    if Number_nodes not in SYSTEM_FILES:
        valid_systems = ", ".join(str(k) for k in sorted(SYSTEM_FILES))
        raise ValueError(f"Sistema no reconocido: {Number_nodes}. Sistemas disponibles: {valid_systems}")

    file = PROJECT_ROOT / SYSTEM_FILES[Number_nodes]
    if not file.exists():
        raise FileNotFoundError(f"No se encontro el archivo de datos: {file}")

    base_dir = file.parent
    figures_dir = base_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    sist = "sist_" + str(Number_nodes)
    figures_sist = figures_dir / sist
    figures_sist.mkdir(parents=True, exist_ok=True)
    
    return str(file)

# --------------------------------------------
# End: System Data File Resolver
# --------------------------------------------

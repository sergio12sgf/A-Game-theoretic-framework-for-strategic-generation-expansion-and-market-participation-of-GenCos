import pandas as pd

def data(file):
    # ======================================================================================== #

    #                                     Information Block

    # ======================================================================================== #
    r = file

    dfs = {
        "T":      pd.read_excel(r, sheet_name="T"),
        "N":      pd.read_excel(r, sheet_name="N"),
        "F":      pd.read_excel(r, sheet_name="F"),
        "G":      pd.read_excel(r, sheet_name="G"),
        "GN":     pd.read_excel(r, sheet_name="GN"),
        "D":      pd.read_excel(r, sheet_name="D"),
        "Br":     pd.read_excel(r, sheet_name="Br"),
        "Z":      pd.read_excel(r, sheet_name="Z"),
        "Dat_G":  pd.read_excel(r, sheet_name="Dat_G"),
        "Dat_GN": pd.read_excel(r, sheet_name="Dat_GN"),
        "Dat_D":  pd.read_excel(r, sheet_name="Dat_D"),
        "Dat_Z":  pd.read_excel(r, sheet_name="Dat_Z"),
        "Lim_Br": pd.read_excel(r, sheet_name="Lim_Br"),
        "Dat_Br": pd.read_excel(r, sheet_name="Dat_Br"),
        "cParams": pd.read_excel(r, sheet_name="configParams")
    }

    return dfs
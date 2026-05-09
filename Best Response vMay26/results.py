# --------------------------------------------
# Begin: Imports and Project Figure Paths
# --------------------------------------------

from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator, MaxNLocator
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import numpy as np
from pathlib import Path
import os
import re

# *** Ajuste 2026-05-06: ancla las figuras a la carpeta raiz del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parent
FIGURES_DIR = PROJECT_ROOT / "figures"

# --------------------------------------------
# End: Imports and Project Figure Paths
# --------------------------------------------


# --------------------------------------------
# Begin: Plot Label Helpers
# --------------------------------------------

def latex_math(s):
    s = str(s).strip()

    # letras + número + resto (cualquier cosa)
    m = re.match(r'^([A-Za-z]+)(\d+)(.*)$', s)
    if not m:
        return s

    letters, num, rest = m.groups()

    # Quita solo el "_" separador inicial del sufijo
    rest = rest.lstrip('_')

    return rf"${letters}_{{{num}}}{rest}$"
    
    return s

# --------------------------------------------
# End: Plot Label Helpers
# --------------------------------------------


# --------------------------------------------
# Begin: Global Plot Style and Palette
# --------------------------------------------

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif', 'Times New Roman', 'Times'],
    'mathtext.fontset': 'cm',
    'font.size': 9,
    'axes.labelsize': 9,
    'axes.titlesize': 9,
    'legend.fontsize': 8,
    'xtick.labelsize': 7,
    'ytick.labelsize': 8,
    'axes.linewidth': 0.6,
    'grid.linewidth': 0.3,
    'grid.alpha': 0.3,
    'lines.linewidth': 1.4,
    'lines.markersize': 5,
    'figure.dpi': 120,
    'savefig.dpi': 120,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.unicode_minus': False,
    'axes.spines.top': False,
    'axes.spines.right': True,
})

# =========================
# Color palette - professional, colorblind-friendly
# =========================
C_F1 = '#2E7D32'    # Dark green
C_F2 = '#C62828'    # Dark red
C_F3 = '#1565C0'    # Dark blue
C_F1_L = '#81C784'  # Light green (new capacity)
C_F2_L = '#EF9A9A'  # Light red
C_F3_L = '#90CAF9'  # Light blue
C_LS = '#7B1FA2'    # Purple (load shedding)
C_DEM = '#E65100'   # Orange (demand)
C_AREA = '#FFF8E1'  # Pale yellow (total capacity area)
C_PC = '#FF6F00'    # Amber (perfect competition)
C_STR = '#2E7D32'   # Green (strategic)

MARKERS = {'F1': 'o', 'F2': 's', 'F3': '^'}
COLORS = {'F1': C_F1, 'F2': C_F2, 'F3': C_F3}
COLORS_NEW = {'F1': C_F1_L, 'F2': C_F2_L, 'F3': C_F3_L}
MARKER_FALLBACK = 'o'
COLOR_FALLBACK = '#9E9E9E'
COLOR_NEW_FALLBACK = '#D0D0D0'

# --------------------------------------------
# End: Global Plot Style and Palette
# --------------------------------------------


# --------------------------------------------
# Begin: Generic Figure Helpers
# --------------------------------------------


def make_triptych(figsize=(10, 3)):
    fig, axs = plt.subplots(1, 3, figsize=figsize, sharey=True)
    return fig, axs


def save_fig(fig, save_path_no_ext):
    fig.savefig(f"{save_path_no_ext}.pdf", format="pdf")
    fig.savefig(f"{save_path_no_ext}.png", format="png")


# *** Ajuste 2026-05-06: helpers maestros para reutilizar formato y rutas de figuras.
def normalize_system_label(sist):
    if sist == "3_PC":
        return 3, "3_PC"
    if sist == "24_PC":
        return 24, "24_PC"
    return sist, str(sist)


def scenario_folder(text):
    if text == "Withholding penalty variation":
        return "Penalty"
    if text == "Demand variation":
        return "Demand"
    return "grid"


def figure_folder(sist_num, text):
    path = FIGURES_DIR / f"sist_{sist_num}" / scenario_folder(text)
    path.mkdir(parents=True, exist_ok=True)
    return path


def set_period_title(ax, period):
    ax.set_title(f"Planning period T{period}", fontweight="semibold", fontsize=10, pad=8)


def set_scenario_axis(ax, text, values=None, fontsize=7):
    ax.set_xlabel(text)
    if values is not None:
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([f"{v:.2f}" for v in values], fontsize=fontsize)


def apply_major_grid(ax, alpha=0.6):
    ax.grid(True, which="major", axis="both",
            color="#D3D3D3", linestyle="-", linewidth=0.5, alpha=alpha)
    ax.set_axisbelow(True)


def apply_light_grid(ax, alpha=0.15):
    ax.grid(True, alpha=alpha)
    ax.set_axisbelow(True)


def set_y_locator(ax, y_step=None, nbins=5):
    if y_step is not None:
        ax.yaxis.set_major_locator(MultipleLocator(y_step))
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=nbins))


def add_bottom_legend(fig, handles, labels=None, ncol=None, y=-0.02,
                      columnspacing=2.5):
    if labels is None:
        labels = [h.get_label() for h in handles]
    if ncol is None:
        ncol = max(1, len(labels))
    fig.legend(handles, labels,
               loc="lower center",
               ncol=ncol,
               frameon=False,
               bbox_to_anchor=(0.5, y),
               columnspacing=columnspacing)


def firm_number(firm):
    match = re.search(r'F[_\s-]*(\d+)', str(firm), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def firm_sort_key(firm):
    number = firm_number(firm)
    return number if number is not None else 999


def base_firm(firm):
    number = firm_number(firm)
    return f"F{number}" if number is not None else str(firm).strip()


def firm_label(firm, include_suffix=False):
    firm = str(firm).strip()
    match = re.search(r'F[_\s-]*(\d+)(.*)', firm, flags=re.IGNORECASE)
    if not match:
        return f"GenCo {firm}"

    number = match.group(1)
    label = rf"GenCo $F_{{{number}}}$"
    suffix = match.group(2).strip('_ -')

    if include_suffix and suffix:
        label += f" ({suffix.replace('_', '-').upper()})"

    return label


def firm_color(firm, default=COLOR_FALLBACK):
    return COLORS.get(base_firm(firm), default)


def firm_new_color(firm, default=COLOR_NEW_FALLBACK):
    return COLORS_NEW.get(base_firm(firm), default)


def firm_marker(firm, default=MARKER_FALLBACK):
    return MARKERS.get(base_firm(firm), default)


def prepare_plot_frame(data, numeric_cols=None, firm_col=None):
    numeric_cols = numeric_cols or []
    df = data.copy()

    if "T" in df.columns:
        df["T"] = df["T"].astype(int)

    if "Srio" in df.columns:
        df["Srio"] = pd.to_numeric(df["Srio"], errors="coerce")

    if "iTER" in df.columns:
        df["iTER"] = pd.to_numeric(df["iTER"], errors="coerce")

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if firm_col is not None and firm_col in df.columns:
        df[firm_col] = df[firm_col].astype(str).str.strip()

    return df


def scenario_values(df):
    return np.sort(df["Srio"].dropna().unique())


def combined_scenario_values(*frames):
    values = [frame["Srio"].dropna().unique() for frame in frames if not frame.empty]
    if not values:
        return np.array([])
    return np.sort(np.unique(np.concatenate(values)))


def with_scenario_positions(df, values):
    pos = {value: idx for idx, value in enumerate(values)}
    return df.assign(xpos=df["Srio"].map(pos))

# --------------------------------------------
# End: Generic Figure Helpers
# --------------------------------------------

'''def bar_chartCapacity(expXiTotal, expXjtotal, demand_srio, text, sist):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    figsize=(10, 4)
    bar_width=0.27

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    # ---- Copias y tipos ----
    df_xi = expXiTotal.copy()
    df_xj = expXjtotal.copy()
    df_L  = demand_srio.copy()

    # Xi y Xj
    for df in (df_xi, df_xj):
        df['T']    = df['T'].astype(int)
        df['Srio'] = pd.to_numeric(df['Srio'], errors='coerce')
        df['iTER'] = pd.to_numeric(df['iTER'], errors='coerce')
        df['F']    = df['F'].astype(str).str.strip()

    df_xi['Xi'] = pd.to_numeric(df_xi['Xi'], errors='coerce')
    df_xj['Xj'] = pd.to_numeric(df_xj['Xj'], errors='coerce')

    # Demanda
    df_L['T']    = df_L['T'].astype(int)
    df_L['Srio'] = pd.to_numeric(df_L['Srio'], errors='coerce')
    df_L['L']    = pd.to_numeric(df_L['L'],   errors='coerce')

    # máximo de la demanda en todos los escenarios y periodos
    L_max = df_L['L'].max()

    # ---- Orden de GenCos ----
    F_all   = sorted(set(df_xi['F'].unique()).union(set(df_xj['F'].unique())),
                     key=lambda s: int(str(s).replace('F','')))
    periods = sorted(df_xi['T'].unique())

    # ---- Paletas y mapeos (F1,F2,F3) ----
    order_map = {"F1": 0, "F2": 1, "F3": 2}
    
    palette  = ["#4BA50F", "#CC5A3A", "#4390CA"]   # Xi
    palette2 = ["#84C45A", "#DF8B74", "#7BBDF0"]   # Xj

    # Colores por F para Xi y Xj (otros F en gris)
    colors_xi = {f: (palette[order_map[f]]  if f in order_map else "#9E9E9E") for f in F_all}
    colors_xj = {f: (palette2[order_map[f]] if f in order_map else "#7E7E7E") for f in F_all}

    fig, axs = plt.subplots(1, len(periods), figsize=figsize, sharey=True)
    if len(periods) == 1:
        axs = [axs]

    for ax, t in zip(axs, periods):
        # ---- Filtrar periodo ----
        xi_T = (df_xi[df_xi['T'] == t]
                .sort_values(['Srio','F','iTER'])
                .drop_duplicates(subset=['Srio','F'], keep='last'))
        xj_T = (df_xj[df_xj['T'] == t]
                .sort_values(['Srio','F','iTER'])
                .drop_duplicates(subset=['Srio','F'], keep='last'))

        # Demanda en ese periodo
        L_T = (df_L[df_L['T'] == t]
               .sort_values(['Srio'])
               .drop_duplicates(subset=['Srio'], keep='last'))

        # ---- Escenarios presentes (unión Xi/Xj) ----
        srio_vals = np.sort(np.unique(np.concatenate([
            xi_T['Srio'].unique(), xj_T['Srio'].unique()
        ])))

        # ---- Pivotes Srio x F ----
        pvt_xi = (xi_T.pivot(index='Srio', columns='F', values='Xi')
                        .reindex(index=srio_vals, columns=F_all)).fillna(0.0)
        pvt_xj = (xj_T.pivot(index='Srio', columns='F', values='Xj')
                        .reindex(index=srio_vals, columns=F_all)).fillna(0.0)

        # Demanda alineada con los mismos Srio
        pvt_L = (L_T.set_index('Srio')['L']
                      .reindex(srio_vals))

        # ---- Capacidad total del mercado (Xi + Xj) por escenario ----
        total_capacity = (pvt_xi + pvt_xj).sum(axis=1)  # Serie index=Srio_vals

        # ---- Posiciones en X por grupo ----
        x = np.arange(len(srio_vals))
        offsets = np.linspace(-(len(F_all)-1)/2, (len(F_all)-1)/2, len(F_all)) * bar_width

        # ---- Área amarilla de capacidad total ----
        ax.fill_between(
            x,
            0,
            total_capacity.values,
            color="#EEE3C6",   # amarillo suave
            alpha=0.5,
            zorder=0
        )

        # ---- Barras apiladas por GenCo ----
        for j, f in enumerate(F_all):
            xi_y = pvt_xi[f].values if f in pvt_xi.columns else np.zeros_like(x)
            xj_y = pvt_xj[f].values if f in pvt_xj.columns else np.zeros_like(x)

            # base Xi (palette)
            ax.bar(x + offsets[j], xi_y, width=bar_width,
                   linewidth=0.3, color=colors_xi[f])

            # capa Xj apilada (palette2)
            ax.bar(x + offsets[j], xj_y, width=bar_width, bottom=xi_y,
                   linewidth=0.3, color=colors_xj[f])

        # ---- Línea de demanda en eje secundario ----
        ax2 = ax.twinx()
        ax2.plot(
            x,
            pvt_L.values,
            marker='o',
            linestyle='-.',
            mfc='white',
            linewidth=1.5,
            color='#7B1FA2'   # morado
        )
        ax2.set_ylabel('Demand [MW]')
        ax2.grid(False)  # para que no se sobrepongan grids

        # misma escala 0–(L_max + 10%) en ambos ejes
        ax.set_ylim(0, L_max + L_max*0.1)
        ax2.set_ylim(0, L_max + L_max*0.1)

        # ---- Ejes y estilo ----
        ax.set_title(f'Planning period T{t}')
        ax.set_xlabel(text)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{v:.2f}" for v in srio_vals])
        if t == periods[0]:
            ax.set_ylabel('Generation capacity [MW]')

    # ---- Leyenda global (barras + demanda + capacidad total) ----
    anchor = [f for f in ["F1","F2","F3"] if f in F_all]  # solo F1..F3 existentes
    legend_items = []

    for f in anchor:
        f_math = latex_math(f)
        legend_items.append(Patch(facecolor=colors_xi[f], label=f"GenCo {f_math}"+ rf"${'X'}_{{{'i'}}}$"))

    for f in anchor:
        f_math = latex_math(f)
        legend_items.append(Patch(facecolor=colors_xj[f], label=f"GenCo {f_math}"+ rf"${'X'}_{{{'j'}}}$"))

    # Proxy para el área de capacidad total
    total_cap_proxy = Patch(
        facecolor="#EEE3C6",
        alpha=0.5,
        edgecolor='none',
        label='Total capacity'
    )
    legend_items.append(total_cap_proxy)

    # Proxy para la línea de demanda
    demand_line_proxy = Line2D(
        [0], [0],
        linestyle='-.',
        marker='o',
        mfc='white',
        linewidth=1.5,
        color='#7B1FA2',
        label='Demand'
    )
    legend_items.append(demand_line_proxy)

    # --- Ajuste dinámico de columnas de la leyenda ---
    total_items = len(legend_items)
    num_gencos = len(anchor)

    if num_gencos > 2:
        # 2 filas: columnas = mitad (redondeando hacia arriba)
        ncols = (total_items + 1) // 2
    else:
        # 1 fila
        ncols = total_items

    if sist ==3:
        bottom_adjust = 0.26
    else:
        bottom_adjust = 0.333

    fig.subplots_adjust(top=0.88, bottom=bottom_adjust, left=0.071, right=0.933, wspace=0.355)
    fig.legend(handles=legend_items,
               loc='lower center', bbox_to_anchor=(0.5, 0.03),
               frameon=False, ncol=ncols)

    # ---- Rutas para guardar figura ----
    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "exp" + str(text1) + Nsist + ".eps"
    save_path = path / file_name

    fig.savefig(save_path, format="eps", bbox_inches="tight")
    plt.show()'''

# --------------------------------------------
# Begin: Capacity Expansion Bar Charts
# --------------------------------------------

def bar_chartCapacity(expXiTotal, expXjtotal, demand_srio, text, sist,
                      y_step=None, cap_max=None, dem_max=None):

    figsize = (10, 3)

    sist_num, Nsist = normalize_system_label(sist)

    # ---- Copias y tipos ----
    df_xi = prepare_plot_frame(expXiTotal, numeric_cols=["Xi"], firm_col="F")
    df_xj = prepare_plot_frame(expXjtotal, numeric_cols=["Xj"], firm_col="F")
    df_L = prepare_plot_frame(demand_srio, numeric_cols=["L"])

    F_all = sorted(set(df_xi['F'].unique()).union(set(df_xj['F'].unique())),
                   key=firm_sort_key)
    periods = sorted(df_xi['T'].unique())

    # ---- Máximo global de capacidad ----
    xi_sum = (df_xi.groupby(['T', 'Srio', 'F'])['Xi'].last()
                   .unstack(fill_value=0))
    xj_sum = (df_xj.groupby(['T', 'Srio', 'F'])['Xj'].last()
                   .unstack(fill_value=0))

    total_cap_global = 0.0
    for t in periods:
        xi_t = xi_sum.loc[t] if t in xi_sum.index.get_level_values(0) else pd.DataFrame()
        xj_t = xj_sum.loc[t] if t in xj_sum.index.get_level_values(0) else pd.DataFrame()

        if isinstance(xi_t, pd.Series):
            xi_t = xi_t.to_frame().T
        if isinstance(xj_t, pd.Series):
            xj_t = xj_t.to_frame().T

        if not xi_t.empty or not xj_t.empty:
            idx = sorted(set(xi_t.index).union(set(xj_t.index)))
            cols = sorted(set(xi_t.columns).union(set(xj_t.columns)))
            xi_t = xi_t.reindex(index=idx, columns=cols, fill_value=0)
            xj_t = xj_t.reindex(index=idx, columns=cols, fill_value=0)
            total_cap_global = max(total_cap_global, (xi_t + xj_t).sum(axis=1).max())

    # ---- Máximo global de demanda ----
    L_max = df_L['L'].max()

    # ---- Límites individuales base ----
    if cap_max is None:
        cap_max = total_cap_global

    if dem_max is None:
        dem_max = L_max

    # ---- Un solo máximo común para ambos ejes ----
    raw_common_max = 1.10 * max(cap_max, dem_max)

    if y_step is not None:
        common_max = np.ceil(raw_common_max / y_step) * y_step
    else:
        common_max = raw_common_max

    # ---- Figura ----
    fig, axs = plt.subplots(1, len(periods), figsize=figsize, sharey=True)
    if len(periods) == 1:
        axs = [axs]

    ax2_list = []

    bw = 0.70 / max(len(F_all), 1)
    offsets = (np.arange(len(F_all)) - (len(F_all) - 1) / 2) * bw

    for j_ax, (ax, t) in enumerate(zip(axs, periods)):
        xi_T = (df_xi[df_xi['T'] == t]
                .sort_values(['Srio', 'F', 'iTER'])
                .drop_duplicates(subset=['Srio', 'F'], keep='last'))

        xj_T = (df_xj[df_xj['T'] == t]
                .sort_values(['Srio', 'F', 'iTER'])
                .drop_duplicates(subset=['Srio', 'F'], keep='last'))

        L_T = (df_L[df_L['T'] == t]
               .sort_values(['Srio'])
               .drop_duplicates(subset=['Srio'], keep='last'))

        srio_vals = np.sort(np.unique(np.concatenate([
            xi_T['Srio'].dropna().unique(),
            xj_T['Srio'].dropna().unique()
        ])))

        x = np.arange(len(srio_vals))

        # ---- Pivotes ----
        pvt_xi = (xi_T.pivot(index='Srio', columns='F', values='Xi')
                       .reindex(index=srio_vals, columns=F_all)
                       .fillna(0.0))

        pvt_xj = (xj_T.pivot(index='Srio', columns='F', values='Xj')
                       .reindex(index=srio_vals, columns=F_all)
                       .fillna(0.0))

        pvt_L = (L_T.set_index('Srio')['L']
                    .reindex(srio_vals)
                    .fillna(0.0))

        # ---- Área de capacidad total ----
        total_capacity = (pvt_xi + pvt_xj).sum(axis=1).values
        ax.fill_between(x, 0, total_capacity,
                        alpha=0.15, color='#FFC107', zorder=0)

        # ---- Barras apiladas por GenCo ----
        for k, f in enumerate(F_all):
            xi_y = pvt_xi[f].values
            xj_y = pvt_xj[f].values

            ax.bar(x + offsets[k], xi_y, bw,
                   color=firm_color(f),
                   edgecolor='white', lw=0.3,
                   label=rf'{firm_label(f)}: $X_i$')

            ax.bar(x + offsets[k], xj_y, bw, bottom=xi_y,
                   color=firm_new_color(f),
                   edgecolor='white', lw=0.3,
                   label=rf'{firm_label(f)}: $X_j$')

        # ---- Demanda en eje secundario ----
        ax2 = ax.twinx()
        ax2_list.append(ax2)

        ax2.plot(x, pvt_L.values,
                 color=C_DEM, marker='o', mfc='white', ls='-.',
                 lw=1.5, label='Demand')

        set_scenario_axis(ax, text, srio_vals)
        set_period_title(ax, t)
        apply_major_grid(ax)

    # ---- MISMA escala en todos los ejes primarios ----
    for ax in axs:
        ax.set_ylim(0, common_max)
        set_y_locator(ax, y_step)

    # ---- MISMA escala en todos los ejes secundarios ----
    for i, ax2 in enumerate(ax2_list):
        ax2.set_ylim(0, common_max)
        set_y_locator(ax2, y_step)

        ax2.tick_params(axis='y', colors=C_DEM, labelcolor=C_DEM)

        if i == len(ax2_list) - 1:
            ax2.set_ylabel('Demand [MW]', color=C_DEM)
        else:
            ax2.set_yticklabels([])

    axs[0].set_ylabel('Generation capacity [MW]')

    # ---- Leyenda global ----
    legend_items = []

    for f in F_all:
        legend_items.append(
            Patch(fc=firm_color(f),
                  label=rf'{firm_label(f)}: $X_i$')
        )

    for f in F_all:
        legend_items.append(
            Patch(fc=firm_new_color(f),
                  label=rf'{firm_label(f)}: $X_j$')
        )

    legend_items.append(
        Patch(fc='#FFC107', alpha=0.3, label='Total capacity')
    )

    legend_items.append(
        Line2D([0], [0], color=C_DEM, marker='o', mfc='white',
               ls='-.', lw=1.5, label='Demand')
    )

    if sist_num == 3:
        fig.legend(handles=legend_items,
                   loc='lower center',
                   ncol=6,
                   frameon=False,
                   bbox_to_anchor=(0.5, 0),
                   columnspacing=1.5)
        fig.subplots_adjust(bottom=0.26, wspace=0.232, top=0.90)

    if sist_num == 24:
        fig.legend(handles=legend_items,
                   loc='lower center',
                   ncol=4,
                   frameon=False,
                   bbox_to_anchor=(0.5, 0),
                   columnspacing=1.5)
        fig.subplots_adjust(bottom=0.31, wspace=0.232, top=0.90)

    # ---- Guardado ----
    text1 = scenario_folder(text)
    path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"exp{text1}{Nsist}.pdf"
    #save_path = path / file_name

    #fig.savefig(save_path, format="pdf")
    plt.show()


# --------------------------------------------
# Begin: LMP Heatmaps
# --------------------------------------------

def boxplot(lmp, text, sist, p_low=2, p_high=98, annotate=True, fmt=".1f",
            vmin=None, vmax=None):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    sist_num, Nsist = normalize_system_label(sist)

    df = lmp.copy()
    df["T"] = df["T"].astype(int)
    df["N"] = df["N"].astype(int)
    df["Srio"] = pd.to_numeric(df["Srio"], errors="coerce").round(2)
    df["LMP"] = pd.to_numeric(df["LMP"], errors="coerce")

    periods = sorted(df["T"].dropna().unique())
    sr_order = np.sort(df["Srio"].dropna().unique())
    n_order = np.sort(df["N"].dropna().unique())

    if vmin is None:
        vmin = np.percentile(df["LMP"].dropna(), p_low)
    if vmax is None:
        vmax = np.percentile(df["LMP"].dropna(), p_high)

    cmap = LinearSegmentedColormap.from_list(
        "lmp",
        ['#1B5E20', '#4CAF50', '#FFEB3B', '#FF9800', '#F44336', '#B71C1C'],
        N=256
    )

    # Ajuste de tamaño: solo el sistema de 3 nodos más compacto
    if sist_num == 3:
        figsize = (11, 4.2)
        right_margin = 0.86
        cax_pos = [0.88, 0.20, 0.018, 0.62]
        ann_fs = 7.0
    else:
        figsize = (14, 5.5)
        right_margin = 0.88
        cax_pos = [0.90, 0.18, 0.015, 0.68]
        ann_fs = 7.5

    if len(periods) == 3:
        wr = [1, 1, 1.12]
    else:
        wr = [1] * len(periods)

    fig, axs = plt.subplots(
        1, len(periods),
        figsize=figsize,
        sharey=True,
        gridspec_kw={'width_ratios': wr}
    )

    if len(periods) == 1:
        axs = [axs]

    last_im = None

    for ax, t in zip(axs, periods):
        mat = (
            df[df["T"] == t]
            .pivot_table(index="N", columns="Srio", values="LMP", aggfunc="mean")
            .reindex(index=n_order, columns=sr_order)
        )

        im = ax.imshow(
            mat.values,
            aspect="auto",
            origin="lower",
            vmin=vmin,
            vmax=vmax,
            cmap=cmap,
            interpolation="nearest"
        )
        last_im = im

        set_period_title(ax, t)
        ax.set_xticks(np.arange(len(sr_order)))
        ax.set_xticklabels(
            [f"{s:.2f}" for s in sr_order],
            rotation=90,
            ha="center",
            va="top",
            fontsize=8
        )
        ax.set_xlabel(text)

        step = max(1, len(n_order) // 12)
        ax.set_yticks(np.arange(0, len(n_order), step))
        ax.set_yticklabels(np.array(n_order)[::step])

        ax.set_xticks(np.arange(-0.5, len(sr_order), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(n_order), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.3)
        ax.tick_params(which="minor", length=0)

        if annotate:
            vals = mat.values
            for i in range(vals.shape[0]):
                for j in range(vals.shape[1]):
                    v = vals[i, j]
                    if np.isnan(v):
                        continue

                    r = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5

                    # Verde/amarillo -> negro
                    # Cerca del rojo -> blanco
                    c = "white" if r >= 0.72 else "black"

                    ax.text(
                        j, i, f"{v:{fmt}}",
                        ha="center",
                        va="center",
                        fontsize=ann_fs,
                        color=c
                    )

    axs[0].set_ylabel("Node")

    fig.subplots_adjust(
        left=0.07,
        right=right_margin,
        bottom=0.18,
        top=0.90,
        wspace=0.08
    )

    # Barra de color externa, sin invadir el gráfico
    cax = fig.add_axes(cax_pos)
    cbar = fig.colorbar(last_im, cax=cax)
    cbar.set_label("LMP [$/MWh]")

    text1 = scenario_folder(text)
    path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"heatmaps_LMP{text1}{Nsist}.pdf"
    #save_path = os.path.join(path, file_name)

    #fig.savefig(save_path, format="pdf")
    plt.show()

















'''def boxplot(lmp, text, sist, p_low=2, p_high=98, annotate=True, fmt=".1f"):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    df = lmp.copy()
    df["T"]    = df["T"].astype(int)
    df["N"]    = df["N"].astype(int)
    df["Srio"] = df["Srio"].astype(float).round(2)

    periods  = sorted(df["T"].unique())
    sr_order = np.sort(df["Srio"].unique())
    n_order  = np.sort(df["N"].unique())

    # Rango global de color (percentiles para no aplastar contraste)
    vmin = np.percentile(df["LMP"], p_low)
    vmax = np.percentile(df["LMP"], p_high)

    # Reducir ancho total, baja este figsize (vertical x labels ayudan)
    fig, axs = plt.subplots(1, len(periods), figsize=(10, 4), constrained_layout=True, sharey=True)
    if len(periods) == 1:
        axs = [axs]

    last_im = None

    for ax, t in zip(axs, periods):
        # matriz (index=N filas, columns=Srio columnas)
        mat = (df[df["T"] == t]
               .pivot_table(index="N", columns="Srio", values="LMP", aggfunc="mean")
               .reindex(index=n_order, columns=sr_order))

        im = ax.imshow(mat.values, aspect="auto", origin="lower", vmin=vmin, vmax=vmax)
        last_im = im

        ax.set_title(f"Planning period T{t}")
        ax.set_xlabel(text)
        ax.set_xticks(np.arange(len(sr_order)))
        ax.set_xticklabels([f"{s:.2f}" for s in sr_order], rotation=90, ha="right")  # ← vertical
        ax.tick_params(axis='x', labelsize=8)  # etiquetas más pequeñas

        # Y ticks (espaciados si hay muchos N)
        step = max(1, len(n_order)//12)
        ax.set_yticks(np.arange(0, len(n_order), step))
        ax.set_yticklabels(n_order[::step])
        if ax is axs[0]:
            ax.set_ylabel("Node")

        # cuadrícula suave
        ax.set_xticks(np.arange(-.5, len(sr_order), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(n_order), 1), minor=True)
        ax.grid(which="minor", linestyle="-", linewidth=0.2)
        ax.tick_params(which="minor", length=0)

        # Anotar valores en cada celda con contraste automático
        if annotate:
            vals = mat.values
            norm = im.norm  # normalizador con vmin/vmax
            # umbral para decidir blanco/negro (mitad de la escala)
            thr = 0.5
            for i in range(vals.shape[0]):      # filas (N)
                for j in range(vals.shape[1]):  # columnas (Srio)
                    v = vals[i, j]
                    if np.isnan(v):
                        continue
                    # contraste: si es "claro" → texto negro, si es "oscuro" → blanco
                    c = "black" if norm(v) > thr else "white"
                    fmt_ = fmt[1:] if isinstance(fmt, str) and fmt.startswith(":") else fmt
                    ax.text(j, i, format(float(v), fmt_), ha="center", va="center", color=c, fontsize=7)

    # Barra de color común
    cbar = fig.colorbar(last_im, ax=axs, location="right", fraction=0.045, pad=0.02)
    cbar.set_label("LMP [$/MWh]")

    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "heatmaps_LMP"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", bbox_inches="tight")
    plt.show()'''

# _Nuevas graficas

'''def totCap(X, wr, markerStyle, markerStyle2, yXmax, text, sist):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    periods = X['T'].unique()
    fig, axs = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

    for ax in axs:
        ax.set_ylim(0, 1.2*yXmax)

    # --- Límite global para todos los ejes secundarios (wr) ---
    wr_num = pd.to_numeric(wr['wr'], errors='coerce').fillna(0.0)
    yWRmax_total = max(1.0, wr_num.max())

    for ax, t in zip(axs, periods):
        df_T = X.loc[X['T'] == t].copy()
        if df_T.empty:
            ax.set_title(f'T={t}')
            ax.set_xlabel('Srio')
            ax.grid(True, alpha=0.3)
            continue

        # --- Eje X consistente con X y wr ---
        df_T['Srio'] = df_T['Srio'].astype(float)
        wr_T = wr.loc[wr['T'].astype(int) == int(t)].copy()
        if not wr_T.empty:
            wr_T['Srio'] = wr_T['Srio'].astype(float)
            all_vals = np.sort(np.unique(np.concatenate([df_T['Srio'].unique(),
                                                         wr_T['Srio'].unique()])))
        else:
            all_vals = np.sort(df_T['Srio'].unique())

        pos  = {v: i for i, v in enumerate(all_vals)}
        df_T['xpos'] = df_T['Srio'].map(pos)

        # --- Curvas de capacidad (eje primario) ---
        palette = ["#5DA32E", "#CA6D53", "#59A8E4"]

        for i, (f, g) in enumerate(df_T.sort_values(['F', 'xpos']).groupby('F')):
            color = palette[i % len(palette)]
            f_math = latex_math(f)
            ax.plot(g['xpos'], g['X_total'], color=color, linewidth=1.2,
                    linestyle='-.', marker=markerStyle, mfc='white', label=f"GenCo {f_math}")

        # --- Load Shedding en eje secundario (una fila por Srio) ---
        if not wr_T.empty:
            wr_T['iTER'] = wr_T['iTER'].astype(int)

            # Para cada Srio, toma la última iteración con wr>0; si no hay, la última iteración
            nz = wr_T[wr_T['wr'] != 0]
            if not nz.empty:
                idx_nz = nz.groupby('Srio')['iTER'].idxmax()
                wsel = nz.loc[idx_nz]
            else:
                idx_last = wr_T.groupby('Srio')['iTER'].idxmax()
                wsel = wr_T.loc[idx_last]

            # Asegura que todos los Srio presentes en X aparezcan (rellena con última de wr_T si faltan)
            faltan = set(all_vals) - set(wsel['Srio'])
            if faltan:
                extra = wr_T[wr_T['Srio'].isin(faltan)]
                if not extra.empty:
                    idx_extra = extra.groupby('Srio')['iTER'].idxmax()
                    wsel = pd.concat([wsel, extra.loc[idx_extra]], ignore_index=True)

            wsel = wsel.sort_values('Srio')
            wsel['xpos'] = wsel['Srio'].map(pos)

            ax2 = ax.twinx()
            if text=="Demand variation":
                ymax_wr = yXmax
            else:
                ymax_wr = max(1.0, wsel['wr'].max())
            ax2.set_ylim(0, 1.2 * ymax_wr)
            ax2.plot(wsel['xpos'], wsel['wr'], color="#803DD6", linewidth=1.2,
                     linestyle='--', marker=markerStyle2, mfc='white',
                     label="Load Shedding")
            ax2.set_ylabel('Load Shedding [MW]')

            # --- Fuerza el MISMO rango Y en todos los ejes secundarios ---
            if text == "Demand variation":
                ax2.set_ylim(0, 1.2 * yXmax)
            else:
                ax2.set_ylim(0, 1.2 * yWRmax_total)

        # --- Eje X ---
        ax.set_xticks(range(len(all_vals)))
        ax.set_xticklabels([f"{v:.2f}" for v in all_vals])
        ax.set_title(f'Planning period T{t}')
        ax.set_xlabel(text)

    axs[0].set_ylabel('Total Capacity [MW]')

    # --- Leyenda global (incluye ejes secundarios) ---
    handles, labels = [], []
    for a in fig.axes:
        h, l = a.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll and ll not in labels:
                handles.append(hh); labels.append(ll)

    if handles:
        fig.legend(handles, labels, bbox_to_anchor=(0.5, 0.02),
                   loc='lower center', ncol=min(len(labels), 4), frameon=False)

    fig.subplots_adjust(top=0.9, bottom=0.236, left=0.07, right=0.933, wspace=0.355)

    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "Capacity"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    plt.show()
    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")
'''

# --------------------------------------------
# Begin: Total Capacity Charts
# --------------------------------------------

def totCap(X, wr, yXmax, text, sist):
    """
    X must contain at least: ['T', 'Srio', 'F', 'X_total']
    wr must contain at least: ['T', 'Srio', 'iTER', 'wr']
    """

    # -------------------------
    # System naming
    # -------------------------
    sist_num, Nsist = normalize_system_label(sist)

    # -------------------------
    # Figure
    # -------------------------
    X = prepare_plot_frame(X, numeric_cols=["X_total"], firm_col="F")
    wr = prepare_plot_frame(wr, numeric_cols=["wr"])

    periods = sorted(X['T'].unique())
    fig, axs = make_triptych()

    # global max for LS axis
    wr_num = wr['wr'].fillna(0.0)
    yWRmax_total = max(1.0, wr_num.max())

    twinx_axes = []

    for j, (ax, t) in enumerate(zip(axs, periods)):
        df_T = X.loc[X['T'] == t].copy()
        wr_T = wr.loc[wr['T'] == int(t)].copy()

        if df_T.empty:
            set_period_title(ax, t)
            ax.set_xlabel(text)
            ax.grid(True)
            continue

        all_vals = combined_scenario_values(df_T, wr_T)
        df_T = with_scenario_positions(df_T, all_vals)

        # -------------------------
        # Capacity curves
        # -------------------------
        for f, g in df_T.sort_values(['F', 'xpos']).groupby('F'):
            ax.plot(
                g['xpos'], g['X_total'],
                color=firm_color(f),
                marker=firm_marker(f),
                mfc='white',
                ls='-.',
                label=firm_label(f)
            )

        ax.set_ylim(0, 1.2 * yXmax)
        #ax.yaxis.set_major_locator(MultipleLocator(25))
        set_scenario_axis(ax, text, all_vals)
        set_period_title(ax, t)
        ax.grid(True)

        # -------------------------
        # Load shedding (secondary axis)
        # -------------------------
        ax2 = ax.twinx()
        #ax2.yaxis.set_major_locator(MultipleLocator(25))
        twinx_axes.append(ax2)

        if not wr_T.empty:
            nz = wr_T[wr_T['wr'] != 0]
            if not nz.empty:
                idx_nz = nz.groupby('Srio')['iTER'].idxmax()
                wsel = nz.loc[idx_nz].copy()
            else:
                idx_last = wr_T.groupby('Srio')['iTER'].idxmax()
                wsel = wr_T.loc[idx_last].copy()

            faltan = set(all_vals) - set(wsel['Srio'])
            if faltan:
                extra = wr_T[wr_T['Srio'].isin(faltan)]
                if not extra.empty:
                    idx_extra = extra.groupby('Srio')['iTER'].idxmax()
                    wsel = pd.concat([wsel, extra.loc[idx_extra]], ignore_index=True)

            wsel = wsel.sort_values('Srio')
            wsel = with_scenario_positions(wsel, all_vals)

            ax2.plot(
                wsel['xpos'], wsel['wr'],
                color=C_LS,
                marker='d',
                mfc='white',
                ls='--',
                label='Load Shedding'
            )

        # same y range for all secondary axes
        if text == "Demand variation":
            ax2.set_ylim(0, 1.2 * yXmax)
        else:
            ax2.set_ylim(0, 1.2 * yWRmax_total)

        # right axis style only on last panel
        if j == len(periods) - 1:
            ax2.set_ylabel('Load Shedding [MW]', color=C_LS)
        else:
            ax2.set_yticklabels([])

        ax2.tick_params(axis='y', colors=C_LS, labelcolor=C_LS)

    axs[0].set_ylabel('Total Capacity [MW]')

    # -------------------------
    # Combined legend
    # -------------------------
    h1, l1 = axs[0].get_legend_handles_labels()
    h2, l2 = twinx_axes[0].get_legend_handles_labels() if twinx_axes else ([], [])

    add_bottom_legend(fig, h1 + h2, l1 + l2, ncol=4, columnspacing=2.5)

    fig.subplots_adjust(bottom=0.22, wspace=0.30, top=0.90)

    # -------------------------
    # Save path
    # -------------------------
    text1 = scenario_folder(text)

    #path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_stem = path / f"Capacity{text1}{Nsist}"
    #save_fig(fig, str(file_stem))

    plt.show()


# --------------------------------------------
# Begin: GenCo Profit Charts
# --------------------------------------------

def profit(pGenCo, ymax1, text, sist, y_step=None, profit_scale=None):
    """
    pGenCo debe contener al menos:
    ['T', 'Srio', 'F', 'Profit_total']
    """
    sist_num, Nsist = normalize_system_label(sist)

    if sist_num == 3:
        profit_scale=1e7
    if sist_num == 24:
        profit_scale=1e9

    ymax = ymax1 / profit_scale if ymax1 is not None else None

    df = prepare_plot_frame(pGenCo, numeric_cols=["Profit_total"], firm_col="F")

    periods = sorted(df['T'].unique())

    fig, axs = make_triptych()

    # Escalado para que coincida con la etiqueta del eje
    df['Profit_plot'] = df['Profit_total'] / profit_scale

    if ymax is None:
        ymax_raw = df['Profit_plot'].max()
        if y_step is not None:
            ymax = np.ceil(1.10 * ymax_raw / y_step) * y_step
        else:
            ymax = 1.10 * ymax_raw

    for ax, t in zip(axs, periods):
        df_T = df.loc[df['T'] == t].copy()

        if df_T.empty:
            set_period_title(ax, t)
            ax.set_xlabel(text)
            continue

        vals = scenario_values(df_T)
        df_T = with_scenario_positions(df_T, vals)

        for f, g in df_T.sort_values(['F', 'xpos']).groupby('F'):
            y = g['Profit_plot'].values

            ax.plot(
                g['xpos'], y,
                color=firm_color(f),
                marker=firm_marker(f),
                mfc='white',
                ls='-.',
                label=firm_label(f, include_suffix=True)
            )

        set_scenario_axis(ax, text, vals)
        set_period_title(ax, t)
        ax.set_ylim(0, ymax*1.10)

        set_y_locator(ax, y_step)
        apply_major_grid(ax)

    axs[0].set_ylabel(r'Total annual profit [$\times 10^7$]')

    h, l = axs[0].get_legend_handles_labels()
    add_bottom_legend(fig, h, l, ncol=len(l), columnspacing=3)

    fig.subplots_adjust(bottom=0.22, wspace=0.12, top=0.90)

    text1 = scenario_folder(text)

    #path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"Profit{text1}{Nsist}.pdf"
    #save_path = os.path.join(path, file_name)

    #fig.savefig(save_path, format="pdf")
    plt.show()


# --------------------------------------------
# Begin: Consumer Profit Comparison Charts
# --------------------------------------------

def consumerProfit(L_prof, L_profit2, sist, y_step=None, ymax1=None, profit_scale=None):
    """
    L_prof:    enfoque estratégico
    L_profit2: competencia perfecta

    Deben contener al menos:
    ['T', 'Srio', 'Profit']
    """

    sist_num, Nsist = normalize_system_label(sist)

    if profit_scale is None:
        if sist_num == 3:
            profit_scale = 1e7
            scale_label = 7
        else:
            profit_scale = 1e9
            scale_label = 9
    else:
        if np.isclose(profit_scale, 1e7):
            scale_label = 7
        elif np.isclose(profit_scale, 1e9):
            scale_label = 9
        else:
            scale_label = None

    df1 = prepare_plot_frame(L_prof, numeric_cols=["Profit"])
    df2 = prepare_plot_frame(L_profit2, numeric_cols=["Profit"])

    for df in (df1, df2):
        df["Profit_plot"] = df["Profit"] / profit_scale

    srio_vals = sorted(set(df1["Srio"].dropna()).union(set(df2["Srio"].dropna())))
    df1 = with_scenario_positions(df1, srio_vals)
    df2 = with_scenario_positions(df2, srio_vals)

    periods = sorted(set(df1["T"]).union(df2["T"]))

    # ---- Rango global correcto considerando valores negativos ----
    all_vals = pd.concat([df1["Profit_plot"], df2["Profit_plot"]], ignore_index=True).dropna()

    if all_vals.empty:
        ymin, ymax = -1, 1
    else:
        data_min = all_vals.min()
        data_max = all_vals.max()

        if ymax1 is not None:
            # ymax1 viene en unidades originales
            y_top = ymax1 / profit_scale
        else:
            y_top = data_max

        if data_max <= 0:
            # todo es negativo
            ymin_raw = 1.10 * data_min
            ymax_raw = y_top*0.2
        elif data_min >= 0:
            # todo es positivo
            ymin_raw = 0.0
            ymax_raw = 1.10 * y_top
        else:
            # hay positivos y negativos
            span = data_max - data_min
            pad = 0.10 * span
            ymin_raw = data_min - pad
            ymax_raw = y_top + pad

        if y_step is not None:
            ymin = np.floor(ymin_raw / y_step) * y_step
            ymax = np.ceil(ymax_raw / y_step) * y_step
        else:
            ymin, ymax = ymin_raw, ymax_raw

        # evita rango degenerado
        if np.isclose(ymin, ymax):
            ymin -= 1
            ymax += 1

    fig, axs = make_triptych()

    series = [
        ("Strategy approach", df1, "o", C_STR),
        ("Perfect competition approach", df2, "^", C_PC),
    ]

    for ax, t in zip(axs, periods):
        for name, dfx, marker, color in series:
            dft = dfx[dfx["T"] == t].sort_values("xpos")
            if dft.empty:
                continue

            ax.plot(
                dft["xpos"],
                dft["Profit_plot"],
                color=color,
                marker=marker,
                mfc="white",
                ls="-.",
                linewidth=1.4,
                label=name
            )

        set_scenario_axis(ax, "Demand scenario variation", srio_vals)
        set_period_title(ax, t)
        ax.set_ylim(ymin, ymax)

        set_y_locator(ax, y_step)
        apply_light_grid(ax)

    if scale_label is not None:
        axs[0].set_ylabel(rf"Total annual profit [$\times 10^{scale_label}$]")
    else:
        axs[0].set_ylabel("Total annual profit [$]")

    h, l = axs[0].get_legend_handles_labels()
    add_bottom_legend(fig, h, l, ncol=2, columnspacing=3)

    fig.subplots_adjust(bottom=0.22, wspace=0.12, top=0.90)

    path = FIGURES_DIR / f"sist_{sist_num}" / "Demand"
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"ProfitConsumer{Nsist}.pdf"
    #save_path = os.path.join(path, file_name)

    #fig.savefig(save_path, format="pdf")
    plt.show()


# --------------------------------------------
# Begin: HHI Market Concentration Charts
# --------------------------------------------

def HHi_index(GenCo_hhi, text, sist, y_step_hhi=None, ymax_hhi=None):
    sist_num, Nsist = normalize_system_label(sist)

    df_hhi = prepare_plot_frame(GenCo_hhi, numeric_cols=["s"], firm_col="F")

    # ---- HHI promedio por escenario y periodo ----
    HHi_df = (
        df_hhi.groupby(['Srio', 'iTER', 'T'], as_index=False)
              .agg(HHI=('s', lambda x: float(np.square(100.0 * x).sum())))
    )

    HHi_plot = (
        HHi_df.groupby(['T', 'Srio'], as_index=False)['HHI']
              .mean()
              .sort_values(['T', 'Srio'])
    )

    share_plot = (
        df_hhi.groupby(['T', 'Srio', 'F'], as_index=False)['s']
              .mean()
              .sort_values(['T', 'Srio', 'F'])
    )

    periods = sorted(HHi_plot['T'].dropna().unique())

    # ---- Escala global para HHI ----
    if ymax_hhi is None:
        ymax_hhi = 1.02 * HHi_plot['HHI'].max()

    fig, axs = make_triptych()
    ax2_list = []

    for j, (ax, t) in enumerate(zip(axs, periods)):
        d_hhi = HHi_plot[HHi_plot['T'] == t].copy()
        d_s = share_plot[share_plot['T'] == t].copy()

        if d_hhi.empty:
            ax.set_visible(False)
            continue

        srio_vals = scenario_values(d_hhi)
        x = np.arange(len(srio_vals))

        # Alinear HHI
        d_hhi = d_hhi.set_index('Srio').reindex(srio_vals).reset_index()

        ax.plot(
            x, d_hhi['HHI'].to_numpy(),
            color='#6A1B9A',
            marker='^',
            mfc='white',
            ls='-.',
            lw=1.5,
            label='HHI index'
        )

        set_scenario_axis(ax, text, srio_vals)
        set_period_title(ax, t)
        ax.set_ylim(0.75*ymax_hhi, ymax_hhi)

        set_y_locator(ax, y_step_hhi)
        apply_light_grid(ax)

        # ---- Eje secundario: participación s [%] ----
        ax2 = ax.twinx()
        ax2_list.append(ax2)

        pivot_s = (
            d_s.pivot(index='Srio', columns='F', values='s')
               .reindex(index=srio_vals)
        )

        cols = list(pivot_s.columns)
        cols = sorted(cols, key=firm_sort_key)
        pivot_s = pivot_s[cols]

        for col in pivot_s.columns:
            ax2.plot(
                x,
                100.0 * pivot_s[col].to_numpy(),
                color=firm_color(col),
                marker=firm_marker(col),
                mfc='white',
                ls='-.',
                lw=1.5,
                label=firm_label(col)
            )

        ax2.set_ylim(0, 100)
        ax2.set_ylabel('s [%]')

    # Oculta ejes sobrantes si hubiera menos de 3 periodos
    for ax in axs[len(periods):]:
        ax.set_visible(False)

    axs[0].set_ylabel('HHI')

    # ---- Leyenda combinada ----
    h1, l1 = axs[0].get_legend_handles_labels()
    if ax2_list:
        h2, l2 = ax2_list[0].get_legend_handles_labels()
    else:
        h2, l2 = [], []

    add_bottom_legend(fig, h1 + h2, l1 + l2, ncol=4, columnspacing=2)

    fig.subplots_adjust(bottom=0.22, wspace=0.35, top=0.90)

    text1 = scenario_folder(text)
    path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"HHi{text1}{Nsist}.pdf"
    #save_path = os.path.join(path, file_name)

    #fig.savefig(save_path, format="pdf")
    plt.show()



# --------------------------------------------
# Begin: Lerner Index Charts
# --------------------------------------------

def Lerner_index(df_Lerner, text, sist, y_step=None, ymax=None):
    # --- Ajuste de sistema para naming ---
    sist_num, Nsist = normalize_system_label(sist)

    # --- Copia y tipos ---
    df = prepare_plot_frame(df_Lerner, numeric_cols=["Lerner"], firm_col="F")

    periods = sorted(df['T'].dropna().unique())
    F_all = sorted(df['F'].dropna().unique(), key=firm_sort_key)

    # --- Escala global ---
    if ymax is None:
        ymax_raw = df['Lerner'].max()
        if pd.isna(ymax_raw):
            ymax_raw = 1.0
        ymax_raw = max(1.0, ymax_raw)
        if y_step is not None:
            ymax = np.ceil(1.05 * ymax_raw / y_step) * y_step
        else:
            ymax = 1.05 * ymax_raw

    fig, axs = make_triptych()

    for ax, t in zip(axs, periods):
        df_T = df[df['T'] == t].copy()

        if df_T.empty:
            set_period_title(ax, t)
            ax.set_xlabel(text)
            continue

        # Promedio Lerner por Srio y GenCo
        df_avg = (df_T.groupby(['Srio', 'F'], as_index=False)['Lerner']
                    .mean()
                    .sort_values(['Srio', 'F']))

        srio_vals = scenario_values(df_avg)
        x = np.arange(len(srio_vals))

        pvt = (df_avg.pivot(index='Srio', columns='F', values='Lerner')
                     .reindex(index=srio_vals, columns=F_all))

        for f in F_all:
            y = pvt[f].values if f in pvt.columns else np.zeros(len(x))

            ax.plot(
                x, y,
                color=firm_color(f),
                marker=firm_marker(f),
                mfc='white',
                ls='-.',
                lw=1.5,
                label=firm_label(f)
            )

        ax.axhline(0, color='gray', lw=0.5, ls='--')
        ax.set_ylim(0, ymax)
        set_scenario_axis(ax, text, srio_vals)
        set_period_title(ax, t)

        set_y_locator(ax, y_step)
        apply_light_grid(ax)

    # Oculta ejes sobrantes si hubiera menos de 3 periodos
    for ax in axs[len(periods):]:
        ax.set_visible(False)

    axs[0].set_ylabel('Average Lerner index')

    h, l = axs[0].get_legend_handles_labels()
    add_bottom_legend(fig, h, l, ncol=len(l), columnspacing=3)

    fig.subplots_adjust(bottom=0.22, wspace=0.12, top=0.90)

    # --- Guardado ---
    text1 = scenario_folder(text)
    path = figure_folder(sist_num, text)
    #path.mkdir(parents=True, exist_ok=True)

    #file_name = f"lerner{text1}{Nsist}.pdf"
    #save_path = os.path.join(path, file_name)

    #fig.savefig(save_path, format="pdf")
    plt.show()


'''def profit(pGenCo, markerStyle, ymax, text, sist):

    plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "mathtext.fontset": "cm",   # math estilo Computer Modern
    "axes.unicode_minus": False # guiones correctos con serif
    })

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    periods = pGenCo['T'].unique()
    fig, axs = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

    for ax in axs:
        ax.set_ylim(0, 1.12*ymax)

    for ax, t in zip(axs, periods):
        df_T = pGenCo.loc[pGenCo['T'] == t].copy()
        if df_T.empty:
            ax.set_title(f'T={t}')
            ax.set_xlabel('Srio')
            ax.grid(True, alpha=0.3)
            continue

        df_T['Srio'] = df_T['Srio'].astype(float)
        vals = np.sort(df_T['Srio'].unique())
        pos  = {v: i for i, v in enumerate(vals)}
        df_T['xpos'] = df_T['Srio'].map(pos)

        palette = ["#5DA32E","#CA6D53","#59A8E4"]

        for i, (f, g) in enumerate(df_T.sort_values(['F','xpos']).groupby('F')):
            color = palette[i % len(palette)]
            f_math = latex_math(f)
            ax.plot(g['xpos'], g['Profit_total'], color=color, linewidth=1.2,
                    linestyle='-.', marker=markerStyle, mfc='white', label=f"GenCo {f_math}")

        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels([f"{v:.2f}" for v in vals])
        ax.set_title(f'Planning period T{t}')
        ax.set_xlabel(text)
        #ax.grid(True, alpha=0.05)

    axs[0].set_ylabel('Total anual profit [$]')
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, bbox_to_anchor=(0.5, 0.02), loc='lower center', ncol=len(labels), frameon=False)

    fig.subplots_adjust(top=0.88, bottom=0.25, left=0.07, right=0.98, wspace=0.09)
    plt.show()

    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "Profit"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")'''

'''def consumerProfit(L_prof, L_profit2, sist):
    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    df1 = L_prof.copy()
    df2 = L_profit2.copy()
    for df in (df1, df2):
        df["T"] = df["T"].astype(int)
        df["Srio"] = df["Srio"].astype(float)

    srio_vals = sorted(set(df1["Srio"]).union(df2["Srio"]))
    pos = {v: i for i, v in enumerate(srio_vals)}
    df1["xpos"] = df1["Srio"].map(pos)
    df2["xpos"] = df2["Srio"].map(pos)

    periods = sorted(set(df1["T"]).union(df2["T"]))
    ncols = len(periods)

    fig, axs = plt.subplots(1, ncols, figsize=(4*ncols, 4), sharey=True)
    if ncols == 1:
        axs = [axs]

    series = [
        ("Strategy approach", df1, "o", "#5DA32E"),
        ("Perfect competition approach", df2, "^", "#CA6D53"),
    ]

    legend_lines = []
    for ax, t in zip(axs, periods):
        for name, dfx, marker, color in series:
            dft = dfx[dfx["T"] == t].sort_values("xpos")
            if dft.empty:
                continue
            ln, = ax.plot(
                dft["xpos"], dft["Profit"], linestyle='-.',
                marker=marker, mfc="white", linewidth=1.2, color=color, label=name
            )
            if t == periods[0]:
                legend_lines.append(ln)

        ax.set_xticks(range(len(srio_vals)))
        ax.set_xticklabels([f"{v:.2f}" for v in srio_vals])
        ax.set_title(f"Planning period T{t}")
        ax.set_xlabel("Demand scenario variation")
        #ax.grid(True, alpha=0.3)

    axs[0].set_ylabel("Total annual profit [$]") 

    fig.legend(legend_lines, [ln.get_label() for ln in legend_lines],
               bbox_to_anchor=(0.5, 0.02), loc="lower center",
               ncol=len(legend_lines), frameon=False)

    fig.subplots_adjust(top=0.85, bottom=0.25, left=0.08, right=0.98, wspace=0.10)

    path = FIGURES_DIR / f"sist_{sist}" / "Demand"

    file_name = "ProfitConsumer"+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")
    plt.show()'''

'''def HHi_index(GenCo_hhi, text, sist):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    if sist == "3_PC":
        sist = 3 
        Nsist = str(sist) + "_PC"
    elif sist == "24_PC":
        sist = 24
        Nsist = str(sist) + "_PC"
    else:
        Nsist = str(sist)

    df_hhi = GenCo_hhi.copy()
    HHi_df = (df_hhi.groupby(['Srio', 'iTER', 'T'], as_index=False)
              .agg(HHi=('s', lambda x: float(np.square(100.0 * x).sum()))))
    HHi_df = HHi_df.sort_values(['Srio', 'iTER', 'T']).reset_index(drop=True)

    Ts = HHi_df['T'].unique()
    fig, axs = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    if len(Ts) == 1:
        axs = [axs]

    handles_global, labels_global = [], []
    seen = set()
    added_hhi = False  # <-- nuevo flag

    for ax, t in zip(axs, Ts):
        # --- HHI (eje primario) ---
        dft = HHi_df[HHi_df['T'] == t].copy()
        dft = dft.groupby('Srio', as_index=False)['HHi'].mean().sort_values('Srio')

        hhi_line, = ax.plot(dft['Srio'], dft['HHi'], linestyle='-.',
                            marker="^", mfc="white", linewidth=1.2,
                            color="#803DD6", label="HHi index")
        ax.set_title(f"Planning period T{t}")
        ax.set_xlabel(text)
        #ax.set_ylim(dft['HHi'].min() - 200, 1.1 * dft['HHi'].max())
        ax.set_ylabel("HHI")

        # ticks X
        xvals = dft['Srio'].to_numpy()
        ax.set_xticks(xvals)
        ax.set_xticklabels([f"{float(x):.2f}" for x in xvals])

        # **Añadir HHI al legend global una sola vez**
        if not added_hhi:
            handles_global.append(hhi_line)
            labels_global.append("HHi index")
            added_hhi = True

        # --- Eje secundario: s*100 por F ---
        ax2 = ax.twinx()
        dff = (df_hhi[df_hhi['T'] == t]
               .groupby(['Srio', 'F'], as_index=False)['s'].mean())
        pivot_s = dff.pivot(index='Srio', columns='F', values='s').reindex(xvals)

        if pivot_s.columns.dtype == 'O':
            cols = sorted(pivot_s.columns,
                          key=lambda s: int(str(s)[1:]) if str(s)[1:].isdigit() else str(s))
            pivot_s = pivot_s[cols]

        palette = ["#5DA32E", "#CA6D53", "#59A8E4", "#C19BF5", "#B3C855", "#F29F05"]

        for k, col in enumerate(pivot_s.columns):
            color = palette[k % len(palette)]
            f_math = latex_math(col)
            line, = ax2.plot(xvals, 100.0 * pivot_s[col].to_numpy(),
                             linestyle='-.', marker='o', mfc="white",
                             linewidth=1.0, color=color, label=f"GenCo {f_math}")
            if col not in seen:
                handles_global.append(line)
                labels_global.append(f"GenCo {f_math}")
                seen.add(col)

        ax2.set_ylim(0, 100)
        ax2.set_ylabel("s [%]")
        ax2.set_xlim(ax.get_xlim())

    # Legend global (incluye ahora "HHi index")
    ncols = max(1, min(len(labels_global), 6))
    fig.legend(handles_global, labels_global,
               loc='lower center', bbox_to_anchor=(0.5, -0.03),
               ncol=ncols, frameon=False)

    fig.subplots_adjust(top=0.857, bottom=0.3, left=0.08, right=0.98, wspace=0.355)
    plt.tight_layout()
    plt.show()

    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "HHi"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")'''

'''def Lerner_index(df_Lerner, text, sist):

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False
    })

    # --- Ajuste de sistema para naming ---
    if sist == "3_PC":
        sist_num = 3
        Nsist = "3_PC"
    elif sist == "24_PC":
        sist_num = 24
        Nsist = "24_PC"
    else:
        sist_num = sist
        Nsist = str(sist)

    # --- Copia y tipos ---
    df = df_Lerner.copy()
    df['T']    = df['T'].astype(int)
    df['Srio'] = pd.to_numeric(df['Srio'], errors='coerce')
    df['iTER'] = pd.to_numeric(df['iTER'], errors='coerce')
    df['F']    = df['F'].astype(str).str.strip()
    df['Lerner'] = pd.to_numeric(df['Lerner'], errors='coerce')

    # Conjuntos
    periods = sorted(df['T'].unique())
    F_all   = sorted(df['F'].unique(), key=lambda s: int(str(s).replace('F','')))

    # Rango global para el eje Lerner
    lerner_max = 1
    pad = 0.05
    y_max = lerner_max + pad

    # Paleta GenCos
    order_map = {"F1": 0, "F2": 1, "F3": 2}
    palette_F = ["#4BA50F", "#CC5A3A", "#4390CA"]
    colors_F = {
        f: (palette_F[order_map[f]] if f in order_map else "#555555")
        for f in F_all
    }

    fig, axs = plt.subplots(1, len(periods), figsize=(12, 4), sharey=True)
    if len(periods) == 1:
        axs = [axs]

    for ax, t in zip(axs, periods):

        df_T = df[df['T'] == t].copy()

        # Promedio Lerner por Srio y GenCo
        df_avg = (df_T.groupby(['Srio', 'F'], as_index=False)['Lerner'].mean())

        srio_vals = np.sort(df_avg['Srio'].unique())
        x = np.arange(len(srio_vals))

        pvt = (df_avg.pivot(index='Srio', columns='F', values='Lerner')
               .reindex(index=srio_vals, columns=F_all))

        # Líneas por GenCo
        for f in F_all:
            y = pvt[f].values if f in pvt.columns else np.zeros_like(x)
            f_math = latex_math(f)
            ax.plot(
                x,
                y,
                marker='o',
                linestyle='-.',
                mfc="white",
                linewidth=1.5,
                color=colors_F[f],
                label=f"GenCo {f_math}"
            )

        ax.axhline(0, color="gray", linewidth=0.7, linestyle="--")
        ax.set_ylim(0, y_max)

        ax.set_title(f"Planning period T{t}")
        ax.set_xlabel(text)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{v:.2f}" for v in srio_vals])
        if t == periods[0]:
            ax.set_ylabel("Average Lerner index")

    # --- Leyenda global (GenCos) ---
    legend_items = []
    for f in F_all:
        f_math = latex_math(f)
        legend_items.append(
            Line2D(
                [0], [0],
                linestyle='-.',
                marker='o',
                mfc = "white",
                linewidth=1.5,
                color=colors_F[f],
                label=f"GenCo {f_math}"
            )
        )

    total_items = len(legend_items)
    num_gencos = len(F_all)
    if num_gencos > 2:
        ncols = (total_items + 1) // 2
    else:
        ncols = total_items

    fig.subplots_adjust(top=0.915, bottom=0.232, left=0.075, right=0.96, wspace=0.25)
    fig.legend(
        handles=legend_items,
        loc='lower center',
        bbox_to_anchor=(0.5, 0.03),
        frameon=False,
        ncol=4
    )

    plt.show()

    if text == "Withholding penalty variation":
        text1 = "Penalty"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = FIGURES_DIR / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "lerner"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")'''

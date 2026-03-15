from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
from pathlib import Path
import os
import re

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

def bar_chartCapacity(expXiTotal, expXjtotal, demand_srio, text, sist):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "exp" + str(text1) + Nsist + ".eps"
    save_path = path / file_name

    fig.savefig(save_path, format="eps", bbox_inches="tight")
    plt.show()

def boxplot(lmp, text, sist, p_low=2, p_high=98, annotate=True, fmt=".1f"):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "heatmaps_LMP"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", bbox_inches="tight")
    plt.show()

# _Nuevas graficas

def totCap(X, wr, markerStyle, markerStyle2, yXmax, text, sist):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "Capacity"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    plt.show()
    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")

def profit(pGenCo, markerStyle, ymax, text, sist):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "Profit"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")

def consumerProfit(L_prof, L_profit2, sist):
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

    path = Path("figures") / f"sist_{sist}" / "Demand"

    file_name = "ProfitConsumer"+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")
    plt.show()

def HHi_index(GenCo_hhi, text, sist):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "HHi"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")

def Lerner_index(df_Lerner, text, sist):

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
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)

    if text == "Demand variation":
        text1 = "Demand"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    if text != "Demand variation" and text != "Withholding penalty variation":
        text1 = "grid"
        path = Path("figures") / f"sist_{sist}" / text1
        path.mkdir(parents=True, exist_ok=True)
    
    file_name = "lerner"+str(text1)+Nsist+".eps"
    save_path = os.path.join(path, file_name)

    fig.savefig(save_path, format="eps", dpi=300, bbox_inches="tight")
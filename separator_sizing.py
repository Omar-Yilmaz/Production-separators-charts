"""
Separator Sizing Tool — API 12J Mathematical Charts
Purely digital rendering of separator sizing nomographs using API 12J
mathematical models. Eliminates dependencies on scanned image files.
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Separator Sizing Tool",
    page_icon="⚙️",
    layout="wide",
)

st.markdown("""
<style>
.main > div { padding-top: 1.2rem; }
.result-metric { text-align:center; background:#0e2040; border-radius:10px;
                 padding:14px 10px; border:1px solid #1e4080; }
.result-metric .val { font-size:2rem; font-weight:700; color:#4d9fff; }
.result-metric .lbl { font-size:0.78rem; color:#8ab; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ── API 12J Mathematical Model ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# Default Constants
T_STD = 520.0  # °R
P_STD = 14.7   # psia
Z_CONST = 0.85
SG_GAS = 0.65
MW_AIR = 28.97
R_GAS = 10.73

V_RATIOS = {
    1: 0.65, 3: 0.56, 5: 0.52, 10: 0.45, 15: 0.41, 20: 0.375, 25: 0.35,
    30: 0.33, 40: 0.305, 50: 0.29, 60: 0.275, 70: 0.265, 80: 0.255,
    90: 0.245, 100: 0.24
}

def get_v_ratio(vol):
    """Interpolate V_ratio for horizontal separator diameter calculation."""
    keys = sorted(V_RATIOS.keys())
    if vol <= keys[0]: return V_RATIOS[keys[0]]
    if vol >= keys[-1]: return V_RATIOS[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= vol <= keys[i+1]:
            t = (vol - keys[i]) / (keys[i+1] - keys[i])
            return V_RATIOS[keys[i]] + t * (V_RATIOS[keys[i+1]] - V_RATIOS[keys[i]])
    return 0.3

def get_api_param(P, API, T=60):
    """Calculate the X parameter for API 12J charts."""
    T_abs = T + 460.0
    rho_l = (141.5 / (131.5 + API)) * 62.4
    rho_g = (P * SG_GAS * MW_AIR) / (R_GAS * Z_CONST * T_abs)
    if rho_l <= rho_g: return 0.002
    return (1.0 / P) * math.sqrt(rho_g / (rho_l - rho_g))

def calc_vert_diam_math(P, API, Qg, T=60):
    """Vertical Separator ID (inches)."""
    x = get_api_param(P, API, T)
    # Regression coefficient based on API 12J Figure 1
    return (311.0 + 101437.0 * (x - 0.0003673)) * math.sqrt(Qg * x)

def calc_vapor_area_math(P, API, Qg, T=60):
    """Vapor Disengaging Area (sq ft)."""
    x = get_api_param(P, API, T)
    # Regression coefficient based on API 12J Figure 2
    return Qg * (315.8 + 1601092.0 * (x - 0.0003673)) * x

def calc_horiz_diam_math(area, vol):
    """Horizontal Separator ID (inches)."""
    vol_term = vol * get_v_ratio(vol)
    return 13.54 * math.sqrt(area + vol_term)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Digital Plotting Functions ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def apply_chart_style(ax, title, ylabel, xlabel=None):
    ax.set_facecolor('#1e293b')
    ax.set_title(title, color='white', fontsize=12, fontweight='bold', pad=15)
    ax.set_ylabel(ylabel, color='#94a3b8', fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel, color='#94a3b8', fontsize=10)
    ax.tick_params(colors='#94a3b8', labelsize=9)
    ax.grid(True, which='both', color='#334155', linestyle='-', alpha=0.4)
    for spine in ax.spines.values():
        spine.set_edgecolor('#334155')

def plot_vertical_chart(input_p, input_api, input_qg, result_d, input_t):
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 14), gridspec_kw={'height_ratios': [1, 1.2]})
    fig.patch.set_facecolor('#0f172a')

    p_range = np.linspace(50, 1600, 100)
    api_curves = [10, 20, 30, 40, 50, 60, 70]
    qg_curves = [10, 25, 50, 75, 100, 150, 200]

    # Nomograph (API vs Pressure)
    for api in api_curves:
        x_vals = [get_api_param(p, api, input_t) for p in p_range]
        ax_top.plot(x_vals, p_range, color='#64748b', linewidth=1.0, alpha=0.6)
        ax_top.text(x_vals[0], p_range[0], f' {api}°', color='#94a3b8', fontsize=9, verticalalignment='bottom')

    target_x = get_api_param(input_p, input_api, input_t)
    ax_top.scatter([target_x], [input_p], color='#ef4444', s=80, zorder=10, edgecolors='white')
    ax_top.axhline(y=input_p, color='#ef4444', linestyle=':', linewidth=1.5, alpha=0.7)
    ax_top.axvline(x=target_x, color='#ef4444', linestyle=':', linewidth=1.5, alpha=0.7)

    apply_chart_style(ax_top, "NOMOGRAPH: LIQUID GRAVITY VS PRESSURE", "PRESSURE (PSIA)")
    ax_top.invert_xaxis()

    # Diameter vs Param
    x_range_bot = np.linspace(0.0001, 0.002, 150)
    for qg in qg_curves:
        d_vals = [(311 + 101437 * (x - 0.0003673)) * math.sqrt(qg * x) for x in x_range_bot]
        ax_bot.plot(x_range_bot, d_vals, color='#64748b', linewidth=1.0, alpha=0.6)
        ax_bot.text(x_range_bot[-1], d_vals[-1], f' {qg}', color='#94a3b8', fontsize=9)

    ax_bot.scatter([target_x], [result_d], color='#4d9fff', s=100, zorder=10, edgecolors='white')
    ax_bot.axvline(x=target_x, color='#ef4444', linestyle=':', linewidth=1.5, alpha=0.7)
    ax_bot.axhline(y=result_d, color='#4d9fff', linestyle=':', linewidth=1.5, alpha=0.7)

    apply_chart_style(ax_bot, "DIAMETER VS GAS FLOW RATE (MMCF/D)", "INSIDE DIAMETER (INCHES)", "API 12J PARAMETER (X)")
    ax_bot.invert_xaxis()

    plt.tight_layout()
    return fig

def plot_horizontal_charts(input_p, input_api, input_qg, input_vol, result_a, result_d, input_t):
    fig_area, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 14), gridspec_kw={'height_ratios': [1, 1.2]})
    fig_area.patch.set_facecolor('#0f172a')

    p_range = np.linspace(50, 1600, 100)
    api_curves = [10, 40, 70]
    qg_curves = [10, 25, 50, 75, 100, 150, 200]
    target_x = get_api_param(input_p, input_api, input_t)

    for api in api_curves:
        x_vals = [get_api_param(p, api, input_t) for p in p_range]
        ax_top.plot(x_vals, p_range, color='#64748b', linewidth=1.0, alpha=0.6)
        ax_top.text(x_vals[0], p_range[0], f' {api}°', color='#94a3b8', fontsize=9)

    ax_top.scatter([target_x], [input_p], color='#ef4444', s=80, zorder=10, edgecolors='white')
    ax_top.axhline(y=input_p, color='#ef4444', linestyle=':', linewidth=1.5, alpha=0.7)
    ax_top.invert_xaxis()
    apply_chart_style(ax_top, "VAPOR AREA NOMOGRAPH", "PRESSURE (PSIA)")

    x_range_bot = np.linspace(0.0001, 0.002, 150)
    for qg in qg_curves:
        a_vals = [qg * (315.8 + 1601092 * (x - 0.0003673)) * x for x in x_range_bot]
        ax_bot.plot(x_range_bot, a_vals, color='#64748b', linewidth=1.0, alpha=0.6)
        ax_bot.text(x_range_bot[-1], a_vals[-1], f' {qg}', color='#94a3b8', fontsize=9)

    ax_bot.scatter([target_x], [result_a], color='#4d9fff', s=100, zorder=10, edgecolors='white')
    ax_bot.axvline(x=target_x, color='#ef4444', linestyle=':', linewidth=1.5, alpha=0.7)
    ax_bot.axhline(y=result_a, color='#4d9fff', linestyle=':', linewidth=1.5, alpha=0.7)
    ax_bot.invert_xaxis()
    apply_chart_style(ax_bot, "VAPOR DISENGAGING AREA VS GAS FLOW RATE", "AREA (SQ FT)", "API 12J PARAMETER (X)")
    plt.tight_layout()

    fig_diam, ax3 = plt.subplots(figsize=(11, 7))
    fig_diam.patch.set_facecolor('#0f172a')
    a_range = np.linspace(0, 30, 150)
    vol_curves = [1, 5, 10, 20, 50, 100]

    for v in vol_curves:
        d_vals = [calc_horiz_diam_math(a, v) for a in a_range]
        ax3.plot(a_range, d_vals, color='#64748b', linewidth=1.0, alpha=0.6)
        ax3.text(a_range[-1], d_vals[-1], f' {v} bbl', color='#94a3b8', fontsize=9)

    ax3.scatter([result_a], [result_d], color='#4d9fff', s=100, zorder=10, edgecolors='white')
    ax3.axvline(x=result_a, color='#4d9fff', linestyle=':', alpha=0.7)
    ax3.axhline(y=result_d, color='#4d9fff', linestyle=':', alpha=0.7)
    apply_chart_style(ax3, "HORIZONTAL SEPARATOR DIAMETER DETERMINATION", "DIAMETER (INCHES)", "VAPOR DISENGAGING AREA (SQ FT)")
    plt.tight_layout()

    return fig_area, fig_diam

# ═══════════════════════════════════════════════════════════════════════════════
# ── Streamlit UI ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

st.title("⚙️ Precision Separator Sizing — API 12J Model")
st.caption("Enhanced analytical sizing tool utilizing regression-based nomographs for oil/gas separation.")

tab1, tab2 = st.tabs(["📐 Vertical Separator", "📏 Horizontal Separator"])

with tab1:
    st.subheader("Analytical Vertical Sizing")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        v_pres = st.number_input("Pressure (psia)", 14.7, 2000.0, 600.0, 10.0, key="vp")
    with c2:
        v_temp = st.number_input("Temperature (°F)", 20.0, 250.0, 60.0, 5.0, key="vt")
    with c3:
        v_api  = st.number_input("Liquid Gravity (°API)", 10.0, 100.0, 40.0, 1.0, key="va")
    with c4:
        v_flow = st.number_input("Gas Flow (MMcf/d)", 0.1, 1000.0, 50.0, 5.0, key="vf")

    if st.button("🔍 Generate Vertical Analysis", type="primary"):
        diam = calc_vert_diam_math(v_pres, v_api, v_flow, v_temp)

        m1, m2 = st.columns(2)
        m1.markdown(f'<div class="result-metric"><div class="val">{round(diam, 2)}"</div><div class="lbl">Inside Diameter (inches)</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="result-metric"><div class="val">{round(diam * 25.4, 1)} mm</div><div class="lbl">Inside Diameter (mm)</div></div>', unsafe_allow_html=True)

        fig = plot_vertical_chart(v_pres, v_api, v_flow, diam, v_temp)
        st.pyplot(fig)

with tab2:
    st.subheader("Analytical Horizontal Sizing")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h_pres = st.number_input("Pressure (psia)", 14.7, 2000.0, 600.0, 10.0, key="hp")
    with c2:
        h_temp = st.number_input("Temperature (°F)", 20.0, 250.0, 60.0, 5.0, key="ht")
    with c3:
        h_api  = st.number_input("Liquid Gravity (°API)", 10.0, 100.0, 40.0, 1.0, key="ha")
    with c4:
        h_flow = st.number_input("Gas Flow (MMcf/d)", 0.1, 1000.0, 50.0, 5.0, key="hf")

    h_liq = st.number_input("Liquid Residence Volume (bbl)", 0.1, 500.0, 50.0, 5.0, key="hl")

    if st.button("🔍 Generate Horizontal Analysis", type="primary"):
        area = calc_vapor_area_math(h_pres, h_api, h_flow, h_temp)
        diam = calc_horiz_diam_math(area, h_liq)

        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="result-metric"><div class="val">{round(area, 2)} ft²</div><div class="lbl">Vapor Disengaging Area</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="result-metric"><div class="val">{round(diam, 2)}"</div><div class="lbl">Inside Diameter (inches)</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="result-metric"><div class="val">{round(diam * 25.4, 1)} mm</div><div class="lbl">Inside Diameter (mm)</div></div>', unsafe_allow_html=True)

        fig_area, fig_diam = plot_horizontal_charts(h_pres, h_api, h_flow, h_liq, area, diam, h_temp)
        st.pyplot(fig_area)
        st.pyplot(fig_diam)

st.markdown("---")
st.info("**Methodology:** Calculations are based on API Spec 12J regression curves for standard gas-liquid separation. Standard gas SG=0.65 and Z=0.85 are assumed.")
st.caption("⚠️ Verification against specific vendor pressure vessel drawings and liquid level controls is required for final fabrication.")
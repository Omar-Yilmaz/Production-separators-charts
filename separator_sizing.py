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

# Pre-extract keys and values for interpolation
V_RATIO_KEYS = np.array(sorted(V_RATIOS.keys()))
V_RATIO_VALS = np.array([V_RATIOS[k] for k in V_RATIO_KEYS])

def get_v_ratio(vol: float) -> float:
    """Interpolate V_ratio for horizontal separator diameter calculation."""
    return float(np.interp(vol, V_RATIO_KEYS, V_RATIO_VALS))

def get_api_param(P: float, API: float, T: float = 60.0) -> float:
    """Calculate the X parameter for API 12J charts."""
    T_abs = T + 460.0
    rho_l = (141.5 / (131.5 + API)) * 62.4
    rho_g = (P * SG_GAS * MW_AIR) / (R_GAS * Z_CONST * T_abs)
    if rho_l <= rho_g:
        return 0.002
    return (1.0 / P) * math.sqrt(rho_g / (rho_l - rho_g))

def calc_vert_diam_math(P: float, API: float, Qg: float, T: float = 60.0) -> float:
    """Calculate Vertical Separator ID (inches)."""
    x = get_api_param(P, API, T)
    return (311.0 + 101437.0 * (x - 0.0003673)) * math.sqrt(Qg * x)

def calc_vapor_area_math(P: float, API: float, Qg: float, T: float = 60.0) -> float:
    """Calculate Vapor Disengaging Area (sq ft)."""
    x = get_api_param(P, API, T)
    return Qg * (315.8 + 1601092.0 * (x - 0.0003673)) * x

def calc_horiz_diam_math(area: float, vol: float) -> float:
    """Calculate Horizontal Separator ID (inches)."""
    vol_term = vol * get_v_ratio(vol)
    return 13.54 * math.sqrt(area + vol_term)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Digital Plotting Functions ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

CURVE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#eab308', '#f97316', '#ef4444', '#ec4899', '#8b5cf6']

def apply_chart_style(ax, title: str, ylabel: str, xlabel: str = None) -> None:
    """Apply uniform, high-contrast styling to Matplotlib axes."""
    ax.set_facecolor('#1e293b')
    ax.set_title(title, color='#f8fafc', fontsize=13, fontweight='bold', pad=15)
    ax.set_ylabel(ylabel, color='#cbd5e1', fontsize=10, fontweight='bold')
    if xlabel:
        ax.set_xlabel(xlabel, color='#cbd5e1', fontsize=10, fontweight='bold')

    ax.tick_params(colors='#94a3b8', labelsize=9, width=1.5)
    ax.grid(True, which='major', color='#334155', linestyle='-', linewidth=0.8, alpha=0.6)
    ax.grid(True, which='minor', color='#334155', linestyle=':', linewidth=0.5, alpha=0.3)
    ax.minorticks_on()

    for spine in ax.spines.values():
        spine.set_edgecolor('#475569')
        spine.set_linewidth(1.2)

def annotate_target(ax, x: float, y: float, text: str):
    """Add a styled annotation box for target coordinate points."""
    ax.annotate(
        text, xy=(x, y), xytext=(15, 15), textcoords='offset points',
        color='#f8fafc', fontsize=9, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.4", fc="#0f172a", ec="#38bdf8", lw=1.5, alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.5, shrinkA=0, shrinkB=5)
    )

def plot_vertical_chart(input_p: float, input_api: float, input_qg: float, result_d: float, input_t: float, x_lim: tuple, y_lim_top: tuple, y_lim_bot: tuple) -> plt.Figure:
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 14), gridspec_kw={'height_ratios': [1, 1.2]})
    fig.patch.set_facecolor('#0f172a')

    p_range = np.linspace(50, 1600, 100)
    api_curves = [10, 20, 30, 40, 50, 60, 70]
    qg_curves = [10, 25, 50, 75, 100, 150, 200]

    # Nomograph (API vs Pressure)
    for i, api in enumerate(api_curves):
        c = CURVE_COLORS[i % len(CURVE_COLORS)]
        x_vals = [get_api_param(p, api, input_t) for p in p_range]
        ax_top.plot(x_vals, p_range, color=c, linewidth=2.0, alpha=0.8, label=f'{api}° API')

    target_x = get_api_param(input_p, input_api, input_t)

    # Target Point
    ax_top.scatter([target_x], [input_p], color='#38bdf8', s=120, alpha=0.3, zorder=9)
    ax_top.scatter([target_x], [input_p], color='#f8fafc', s=30, zorder=10, edgecolors='#38bdf8', linewidth=1.5)
    ax_top.axhline(y=input_p, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)
    ax_top.axvline(x=target_x, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)

    annotate_target(ax_top, target_x, input_p, f"Target: {input_p} psia\nX: {target_x:.5f}")
    apply_chart_style(ax_top, "NOMOGRAPH: LIQUID GRAVITY VS PRESSURE", "PRESSURE (PSIA)")

    # Apply Limits
    ax_top.set_xlim(x_lim[0], x_lim[1])
    ax_top.set_ylim(y_lim_top[0], y_lim_top[1])
    ax_top.legend(loc='upper right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', framealpha=0.9)

    # Diameter vs Param
    x_range_bot = np.linspace(0.0001, 0.002, 150)
    for i, qg in enumerate(qg_curves):
        c = CURVE_COLORS[i % len(CURVE_COLORS)]
        d_vals = [(311 + 101437 * (x - 0.0003673)) * math.sqrt(qg * x) for x in x_range_bot]
        ax_bot.plot(x_range_bot, d_vals, color=c, linewidth=2.0, alpha=0.8, label=f'{qg} MMscfd')

    ax_bot.scatter([target_x], [result_d], color='#38bdf8', s=120, alpha=0.3, zorder=9)
    ax_bot.scatter([target_x], [result_d], color='#f8fafc', s=30, zorder=10, edgecolors='#38bdf8', linewidth=1.5)
    ax_bot.axvline(x=target_x, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)
    ax_bot.axhline(y=result_d, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)

    ax_bot.text(x_lim[0], result_d, f'{result_d:.2f} ', color='#38bdf8', fontsize=10, fontweight='bold', ha='right', va='center')

    annotate_target(ax_bot, target_x, result_d, f"Target: {result_d:.2f} inches")
    apply_chart_style(ax_bot, "DIAMETER VS GAS FLOW RATE (MMCF/D)", "INSIDE DIAMETER (INCHES)", "API 12J PARAMETER (X)")

    # Apply Limits
    ax_bot.set_xlim(x_lim[0], x_lim[1])
    ax_bot.set_ylim(y_lim_bot[0], y_lim_bot[1])
    ax_bot.legend(loc='upper left', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', framealpha=0.9, ncol=2)

    fig.tight_layout(pad=3.0)
    return fig

def plot_horizontal_charts(input_p: float, input_api: float, input_qg: float, input_vol: float, result_a: float, result_d: float, input_t: float, x_lim_param: tuple, x_lim_area: tuple, y_lim_top: tuple, y_lim_bot: tuple, y_lim_diam: tuple) -> tuple[plt.Figure, plt.Figure]:
    fig_area, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 14), gridspec_kw={'height_ratios': [1, 1.2]})
    fig_area.patch.set_facecolor('#0f172a')

    p_range = np.linspace(50, 1600, 100)
    api_curves = [10, 30, 50, 70]
    qg_curves = [10, 25, 50, 75, 100, 150, 200]
    target_x = get_api_param(input_p, input_api, input_t)

    # Area Top Chart
    for i, api in enumerate(api_curves):
        c = CURVE_COLORS[i % len(CURVE_COLORS)]
        x_vals = [get_api_param(p, api, input_t) for p in p_range]
        ax_top.plot(x_vals, p_range, color=c, linewidth=2.0, alpha=0.8, label=f'{api}° API')

    ax_top.scatter([target_x], [input_p], color='#38bdf8', s=120, alpha=0.3, zorder=9)
    ax_top.scatter([target_x], [input_p], color='#f8fafc', s=30, zorder=10, edgecolors='#38bdf8', linewidth=1.5)
    ax_top.axhline(y=input_p, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)
    ax_top.axvline(x=target_x, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)

    annotate_target(ax_top, target_x, input_p, f"P: {input_p} psia\nX: {target_x:.5f}")
    apply_chart_style(ax_top, "VAPOR AREA NOMOGRAPH", "PRESSURE (PSIA)")

    # Apply Limits
    ax_top.set_xlim(x_lim_param[0], x_lim_param[1])
    ax_top.set_ylim(y_lim_top[0], y_lim_top[1])
    ax_top.legend(loc='upper right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', framealpha=0.9)

    # Area Bottom Chart
    x_range_bot = np.linspace(0.0001, 0.002, 150)
    for i, qg in enumerate(qg_curves):
        c = CURVE_COLORS[i % len(CURVE_COLORS)]
        a_vals = [qg * (315.8 + 1601092 * (x - 0.0003673)) * x for x in x_range_bot]
        ax_bot.plot(x_range_bot, a_vals, color=c, linewidth=2.0, alpha=0.8, label=f'{qg} MMscfd')

    ax_bot.scatter([target_x], [result_a], color='#38bdf8', s=120, alpha=0.3, zorder=9)
    ax_bot.scatter([target_x], [result_a], color='#f8fafc', s=30, zorder=10, edgecolors='#38bdf8', linewidth=1.5)
    ax_bot.axvline(x=target_x, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)
    ax_bot.axhline(y=result_a, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)

    ax_bot.text(x_lim_param[0], result_a, f'{result_a:.2f} ', color='#38bdf8', fontsize=10, fontweight='bold', ha='right', va='center')

    annotate_target(ax_bot, target_x, result_a, f"Area: {result_a:.2f} ft²")
    apply_chart_style(ax_bot, "VAPOR DISENGAGING AREA VS GAS FLOW RATE", "AREA (SQ FT)", "API 12J PARAMETER (X)")

    # Apply Limits
    ax_bot.set_xlim(x_lim_param[0], x_lim_param[1])
    ax_bot.set_ylim(y_lim_bot[0], y_lim_bot[1])
    ax_bot.legend(loc='upper left', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', framealpha=0.9, ncol=2)

    fig_area.tight_layout(pad=3.0)

    # Diameter Chart
    fig_diam, ax3 = plt.subplots(figsize=(11, 7))
    fig_diam.patch.set_facecolor('#0f172a')
    a_range = np.linspace(0, 30, 150)
    vol_curves = [1, 5, 10, 20, 50, 100]

    for i, v in enumerate(vol_curves):
        c = CURVE_COLORS[i % len(CURVE_COLORS)]
        d_vals = [calc_horiz_diam_math(a, v) for a in a_range]
        ax3.plot(a_range, d_vals, color=c, linewidth=2.0, alpha=0.8, label=f'{v} bbl')

    ax3.scatter([result_a], [result_d], color='#38bdf8', s=120, alpha=0.3, zorder=9)
    ax3.scatter([result_a], [result_d], color='#f8fafc', s=30, zorder=10, edgecolors='#38bdf8', linewidth=1.5)
    ax3.axvline(x=result_a, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)
    ax3.axhline(y=result_d, color='#38bdf8', linestyle='--', linewidth=1.5, alpha=0.8)

    ax3.text(x_lim_area[0], result_d, f'{result_d:.2f} ', color='#38bdf8', fontsize=10, fontweight='bold', ha='right', va='center')

    annotate_target(ax3, result_a, result_d, f"Diam: {result_d:.2f} in")
    apply_chart_style(ax3, "HORIZONTAL SEPARATOR DIAMETER DETERMINATION", "DIAMETER (INCHES)", "VAPOR DISENGAGING AREA (SQ FT)")

    # Apply Limits
    ax3.set_xlim(x_lim_area[0], x_lim_area[1])
    ax3.set_ylim(y_lim_diam[0], y_lim_diam[1])
    ax3.legend(loc='lower right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#cbd5e1', framealpha=0.9, ncol=2)

    fig_diam.tight_layout(pad=3.0)

    return fig_area, fig_diam

# ═══════════════════════════════════════════════════════════════════════════════
# ── Streamlit UI ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

st.title("⚙️ Precision Separator Sizing — API 12J Model")
st.caption("Enhanced analytical sizing tool utilizing regression-based nomographs for oil/gas separation.")

tab1, tab2, tab3 = st.tabs(["📐 Vertical Separator", "📏 Horizontal Separator", "📖 Methodology"])

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

    with st.expander("⚙️ Chart Axis Configuration"):
        st.markdown("**X-Axis**")
        c_x1, c_x2 = st.columns(2)
        with c_x1:
            v_x_max = st.number_input("X-Axis Max (API Param)", value=0.0015, format="%.5f", key="v_x_max")
        with c_x2:
            v_x_min = st.number_input("X-Axis Min (API Param)", value=-0.00015, format="%.5f", key="v_x_min")

        st.markdown("**Y-Axis**")
        c_y1, c_y2 = st.columns(2)
        with c_y1:
            v_y_max_top = st.number_input("Top Chart Y Max (Pressure)", value=1600.0, step=100.0, key="v_y_max_top")
            v_y_min_top = st.number_input("Top Chart Y Min (Pressure)", value=0.0, step=100.0, key="v_y_min_top")
        with c_y2:
            v_y_max_bot = st.number_input("Bottom Chart Y Max (Diameter)", value=400.0, step=10.0, key="v_y_max_bot")
            v_y_min_bot = st.number_input("Bottom Chart Y Min (Diameter)", value=0.0, step=10.0, key="v_y_min_bot")

    if st.button("🔍 Generate Vertical Analysis", type="primary"):
        diam = calc_vert_diam_math(v_pres, v_api, v_flow, v_temp)

        m1, m2 = st.columns(2)
        m1.markdown(f'<div class="result-metric"><div class="val">{round(diam, 2)}"</div><div class="lbl">Inside Diameter (inches)</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="result-metric"><div class="val">{round(diam * 25.4, 1)} mm</div><div class="lbl">Inside Diameter (mm)</div></div>', unsafe_allow_html=True)

        fig = plot_vertical_chart(
            v_pres, v_api, v_flow, diam, v_temp,
            x_lim=(v_x_max, v_x_min),
            y_lim_top=(v_y_min_top, v_y_max_top),
            y_lim_bot=(v_y_min_bot, v_y_max_bot)
        )
        st.pyplot(fig)
        plt.close(fig)

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

    with st.expander("⚙️ Chart Axis Configuration"):
        st.markdown("**X-Axis**")
        c_x1, c_x2, c_x3, c_x4 = st.columns(4)
        with c_x1:
            h_x_max = st.number_input("Area Chart X Max", value=0.0018, format="%.5f", key="h_x_max")
        with c_x2:
            h_x_min = st.number_input("Area Chart X Min", value=-0.0001, format="%.5f", key="h_x_min")
        with c_x3:
            d_x_max = st.number_input("Diam Chart X Max", value=34.0, format="%.1f", key="d_x_max")
        with c_x4:
            d_x_min = st.number_input("Diam Chart X Min", value=-2.0, format="%.1f", key="d_x_min")

        st.markdown("**Y-Axis**")
        c_y1, c_y2, c_y3 = st.columns(3)
        with c_y1:
            h_y_max_top = st.number_input("Area Top Y Max (Pressure)", value=1600.0, step=100.0, key="h_y_max_top")
            h_y_min_top = st.number_input("Area Top Y Min (Pressure)", value=0.0, step=100.0, key="h_y_min_top")
        with c_y2:
            h_y_max_bot = st.number_input("Area Bot Y Max (Area)", value=150.0, step=10.0, key="h_y_max_bot")
            h_y_min_bot = st.number_input("Area Bot Y Min (Area)", value=0.0, step=10.0, key="h_y_min_bot")
        with c_y3:
            d_y_max = st.number_input("Diam Y Max (Diameter)", value=150.0, step=10.0, key="d_y_max")
            d_y_min = st.number_input("Diam Y Min (Diameter)", value=0.0, step=10.0, key="d_y_min")

    if st.button("🔍 Generate Horizontal Analysis", type="primary"):
        area = calc_vapor_area_math(h_pres, h_api, h_flow, h_temp)
        diam = calc_horiz_diam_math(area, h_liq)

        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="result-metric"><div class="val">{round(area, 2)} ft²</div><div class="lbl">Vapor Disengaging Area</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="result-metric"><div class="val">{round(diam, 2)}"</div><div class="lbl">Inside Diameter (inches)</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="result-metric"><div class="val">{round(diam * 25.4, 1)} mm</div><div class="lbl">Inside Diameter (mm)</div></div>', unsafe_allow_html=True)

        fig_area, fig_diam = plot_horizontal_charts(
            h_pres, h_api, h_flow, h_liq, area, diam, h_temp,
            x_lim_param=(h_x_max, h_x_min),
            x_lim_area=(d_x_min, d_x_max),
            y_lim_top=(h_y_min_top, h_y_max_top),
            y_lim_bot=(h_y_min_bot, h_y_max_bot),
            y_lim_diam=(d_y_min, d_y_max)
        )
        st.pyplot(fig_area)
        st.pyplot(fig_diam)
        plt.close(fig_area)
        plt.close(fig_diam)

with tab3:
    st.subheader("Chart Generation Methodology")
    st.markdown("""
    ### 1. Core API 12J Parameter Calculation
    The fundamental parameter $X$ governing separation sizing is derived from phase densities. This defines the horizontal axis connecting the nomograph segments.

    $$X = \\frac{1}{P} \\sqrt{\\frac{\\rho_g}{\\rho_l - \\rho_g}}$$

    Where:
    * $P$ = Operating Pressure (psia)
    * $\\rho_g$ = Gas Density ($lb/ft^3$), calculated via standard ideal gas law with Z-factor correction.
    * $\\rho_l$ = Liquid Density ($lb/ft^3$), derived from API gravity.

    ### 2. Regression Curve Equations
    The visible chart curves are plotted dynamically by evaluating empirical regression equations derived from API 12J over continuous linear data spaces (`np.linspace`).

    **Vertical Separator Diameter ($D_v$)**
    $$D_v = [311.0 + 101,437.0 \\cdot (X - 0.0003673)] \\cdot \\sqrt{Q_g \\cdot X}$$

    **Horizontal Vapor Disengaging Area ($A$)**
    $$A = Q_g \\cdot [315.8 + 1,601,092.0 \\cdot (X - 0.0003673)] \\cdot X$$

    **Horizontal Separator Diameter ($D_h$)**
    $$D_h = 13.54 \\cdot \\sqrt{A + (Vol \\cdot V_{ratio})}$$
    *Note: $V_{ratio}$ is an interpolated empirical ratio based on liquid volume capacity ($Vol$).*

    ### 3. Plotting Engine (Matplotlib)
    Static pixel mapping of scanned images was eliminated. The system utilizes `matplotlib` to render the equations purely mathematically:
    1.  Generates a parameter space for pressure ($50-1600$ psia) and $X$ ($0.0001-0.002$).
    2.  Plots distinct lines for predefined $Q_g$ (gas flow) and $API$ (liquid gravity) constants by evaluating the regression equations.
    3.  Calculates the user's specific target intersection coordinates based on input parameters.
    4.  Overlays point markers and dashed reference lines exactly at calculated $(x, y)$ coordinates.
    """)

st.markdown("---")
st.info("**Methodology:** Calculations are based on API Spec 12J regression curves for standard gas-liquid separation. Standard gas SG=0.65 and Z=0.85 are assumed.")
st.caption("⚠️ Verification against specific vendor pressure vessel drawings and liquid level controls is required for final fabrication.")

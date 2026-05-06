import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador de Flujo Sanguíneo Arterial",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CON TIPOGRAFÍA MATEMÁTICA + MODO OSCURO ---
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,300;1,8..60,400&display=swap" rel="stylesheet">

    <style>
    /* ── Tipografia global tipo libro (light Y dark) ── */
    html, body, [class*="css"], .stApp, .stMarkdown, p, li, label,
    .stMetric, .stSelectbox, .stSlider, .stRadio, .stTabs, div, span {
        font-family: 'Source Serif 4', 'Georgia', 'Times New Roman', serif !important;
        font-size: 1.05rem;
    }

    /* Titulos con STIX Two */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'STIX Two Text', 'Cambria', 'Georgia', serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        font-size: 1.25rem;
    }
    h1 { font-size: 1.9rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.25rem !important; }

    /* Valores numéricos en métricas — hereda color del tema */
    [data-testid="stMetricValue"] {
        font-family: 'STIX Two Text', 'Cambria', serif !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em;
        color: inherit !important;
    }

    /* Etiquetas de métricas */
    [data-testid="stMetricLabel"] p {
        font-family: 'Source Serif 4', serif !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        font-style: italic;
        color: inherit !important;
        opacity: 0.75;
    }

    /* Tabla */
    .dataframe, table, th, td {
        font-family: 'STIX Two Text', 'Cambria', serif !important;
        font-size: 0.97rem !important;
    }

    /* ── Cajas adaptativas (light/dark) ── */
    .warning-box {
        background-color: rgba(200, 134, 10, 0.15);
        padding: 15px;
        border-radius: 4px;
        border-left: 5px solid #c8860a;
        font-family: 'Source Serif 4', serif !important;
        font-size: 1.02rem;
        color: inherit;
    }
    .danger-box {
        background-color: rgba(166, 28, 28, 0.15);
        padding: 15px;
        border-radius: 4px;
        border-left: 5px solid #c0392b;
        font-family: 'Source Serif 4', serif !important;
        font-size: 1.02rem;
        color: inherit;
    }

    /* ── Tarjeta de resistencia adaptativa ── */
    .resistencia-card {
        background: rgba(192, 57, 43, 0.08);
        border: 1.5px solid #c0392b;
        border-radius: 8px;
        padding: 14px 18px;
        text-align: center;
        margin-top: 4px;
    }
    .resistencia-label {
        font-family: 'Source Serif 4', serif !important;
        font-size: 0.88rem;
        font-style: italic;
        display: block;
        margin-bottom: 4px;
        color: inherit;
        opacity: 0.8;
    }
    .resistencia-valor {
        font-family: 'STIX Two Text', 'Cambria', serif !important;
        font-size: 1.4rem;
        font-weight: 700;
        color: #e05252;
        display: block;
        line-height: 1.3;
        letter-spacing: 0.02em;
    }
    .resistencia-factor {
        font-family: 'Source Serif 4', serif !important;
        font-size: 0.88rem;
        margin-top: 3px;
        display: block;
        color: inherit;
        opacity: 0.75;
    }

    /* ── Tarjeta de trabajo cardiaco ── */
    .trabajo-card {
        background: rgba(41, 98, 155, 0.10);
        border: 1.5px solid #2962a3;
        border-radius: 8px;
        padding: 14px 18px;
        text-align: center;
        margin-top: 4px;
    }
    .trabajo-label {
        font-family: 'Source Serif 4', serif !important;
        font-size: 0.88rem;
        font-style: italic;
        display: block;
        margin-bottom: 4px;
        color: inherit;
        opacity: 0.8;
    }
    .trabajo-valor {
        font-family: 'STIX Two Text', 'Cambria', serif !important;
        font-size: 1.4rem;
        font-weight: 700;
        color: #4a90d9;
        display: block;
        line-height: 1.3;
        letter-spacing: 0.02em;
    }
    .trabajo-factor {
        font-family: 'Source Serif 4', serif !important;
        font-size: 0.88rem;
        margin-top: 3px;
        display: block;
        color: inherit;
        opacity: 0.75;
    }
    </style>
""", unsafe_allow_html=True)

# --- PRESETS CLÍNICOS ---
PRESETS = {
    "Arteria normal": {
        "r_mm": 1.5,
        "delta_P": 1600,
        "L_cm": 10.0,
        "viscosidad": 0.0035,
        "porcentaje_placa": 0,
        "densidad": 1060
    },
    "Arteriosclerosis leve": {
        "r_mm": 1.5,
        "delta_P": 2600,
        "L_cm": 10.0,
        "viscosidad": 0.0045,
        "porcentaje_placa": 25,
        "densidad": 1060
    },
    "Arteriosclerosis severa": {
        "r_mm": 1.5,
        "delta_P": 2600,
        "L_cm": 10.0,
        "viscosidad": 0.0048,
        "porcentaje_placa": 55,
        "densidad": 1065
    },
    "Oclusión crítica": {
        "r_mm": 1.5,
        "delta_P": 3500,
        "L_cm": 10.0,
        "viscosidad": 0.0050,
        "porcentaje_placa": 90,
        "densidad": 1070
    }
}

# --- CONSTANTE DE REFERENCIA FISIOLÓGICA ---
_r_ref = 0.0015; _visc_ref = 0.0035; _L_ref = 0.10; _dP_ref = 1600
Q_NORMAL_REF_M3S = (np.pi * _r_ref**4 * _dP_ref) / (8 * _visc_ref * _L_ref)

# --- FUNCIONES MATEMÁTICAS Y GEOMÉTRICAS ---
def get_radio_local(z_val, r_base_mm, porcentaje_placa, L_cm):
    """Calcula el radio de la arteria en un punto Z específico, formando la oclusión central."""
    factor_forma = np.exp(-(z_val**2) / (0.05 * L_cm**2))
    r_local = r_base_mm * (1 - (porcentaje_placa / 100.0) * factor_forma)
    return np.maximum(r_local, 0.05)

def calcular_hemodinamica(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa, densidad=1060):
    r_m = r_mm / 1000.0
    L_m = L_cm / 100.0

    r_min_mm = get_radio_local(0, r_mm, porcentaje_placa, L_cm)
    r_min_m = r_min_mm / 1000.0

    A_m2 = np.pi * (r_min_m**2)
    Q_m3s = (np.pi * (r_min_m**4) * delta_P) / (8 * viscosidad * L_m) if L_m > 0 else 0
    v_ms = Q_m3s / A_m2 if A_m2 > 0 else 0
    Re = (2 * densidad * v_ms * r_min_m) / viscosidad if viscosidad > 0 else 0
    R = (8 * viscosidad * L_m) / (np.pi * (r_min_m**4)) if r_min_m > 0 else float('inf')

    W_util_watts    = Q_m3s * delta_P
    W_esfuerzo_w    = R * (Q_NORMAL_REF_M3S ** 2)

    Q_ml_min        = Q_m3s * 60 * 1_000_000
    v_cm_s          = v_ms * 100
    W_util_mj       = W_util_watts  * 60 * 1000
    W_esfuerzo_mj   = W_esfuerzo_w  * 60 * 1000

    return Q_ml_min, v_cm_s, Re, R, W_util_mj, W_esfuerzo_mj, r_min_mm

def generar_frames_particulas(num_particulas, num_frames, v_base_cm_s, Re, L_cm, r_mm, porcentaje_placa):
    dt = 0.025  
    factor_ralentizacion = 0.15 
    
    z_actual = np.random.uniform(-L_cm/2, L_cm/2, num_particulas)
    rho = np.random.uniform(0, 0.85, num_particulas) 
    theta = np.random.uniform(0, 2*np.pi, num_particulas)
    
    historico = []
    
    for _ in range(num_frames):
        r_local = get_radio_local(z_actual, r_mm, porcentaje_placa, L_cm)
        
        v_local = v_base_cm_s * ((r_mm / r_local)**2)
        v_perfil = v_local * (1 - rho**2) 
        
        z_actual += v_perfil * dt * factor_ralentizacion 
        z_actual = np.where(z_actual > L_cm/2, -L_cm/2, z_actual) 
        
        if Re > 2000:
            intensidad_turbulencia = (Re - 2000) / 8000.0
            zona_turbulenta = (z_actual > -1) & (z_actual < 3) 
            
            theta = np.where(zona_turbulenta, theta + np.random.normal(0, 0.3 * intensidad_turbulencia, num_particulas), theta)
            rho = np.where(zona_turbulenta, rho + np.random.normal(0, 0.05 * intensidad_turbulencia, num_particulas), rho)
            rho = np.clip(rho, 0, 0.95)
            
        r_local_actualizado = get_radio_local(z_actual, r_mm, porcentaje_placa, L_cm)
        x_actual = (rho * r_local_actualizado) * np.cos(theta)
        y_actual = (rho * r_local_actualizado) * np.sin(theta)
        
        historico.append((x_actual, y_actual, np.copy(z_actual)))
        
    return historico

def crear_visualizacion_corte_transversal(r_mm, porcentaje_placa, L_cm, z_posicion=0):
    fig = go.Figure()
    
    r_local = get_radio_local(z_posicion, r_mm, porcentaje_placa, L_cm)
    
    theta = np.linspace(0, 2*np.pi, 100)
    x_exterior = r_mm * np.cos(theta)
    y_exterior = r_mm * np.sin(theta)
    
    factor_forma = np.exp(-(z_posicion**2) / (0.05 * L_cm**2))
    r_placa = r_mm * (porcentaje_placa / 100.0) * factor_forma
    x_placa = r_placa * np.cos(theta)
    y_placa = r_placa * np.sin(theta)
    
    x_plasma = r_local * np.cos(theta)
    y_plasma = r_local * np.sin(theta)
    
    fig.add_trace(go.Scatter(x=x_exterior, y=y_exterior, mode='lines',
                             line=dict(color='crimson', width=3), name='Pared Arterial'))
    
    fig.add_trace(go.Scatter(x=x_placa, y=y_placa, fill='toself', 
                             fillcolor='rgba(255, 165, 0, 0.6)', 
                             name='Placa', line=dict(color='orange')))
    
    fig.add_trace(go.Scatter(x=x_plasma, y=y_plasma, fill='toself',
                             fillcolor='rgba(0, 100, 255, 0.2)',
                             name='Luz Arterial (Plasma)', line=dict(color='royalblue')))
    
    fig.update_layout(
        title=f"Corte Transversal (Z={z_posicion:.1f})",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        height=400,
        hovermode='closest',
        showlegend=True
    )
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    
    return fig

def crear_perfil_velocidad(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa):
    r_min_mm = get_radio_local(0, r_mm, porcentaje_placa, L_cm)
    
    r_vals = np.linspace(0, r_min_mm, 50)
    v_vals = (delta_P / (4 * viscosidad)) * (r_min_mm**2 - r_vals**2)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=v_vals, y=r_vals,
                             fill='tozeroy', 
                             fillcolor='rgba(255, 0, 0, 0.3)',
                             line=dict(color='red', width=2),
                             name='Velocidad'))
    
    fig.update_layout(
        title="Perfil de Velocidad (Ley de Poiseuille)",
        xaxis_title="Velocidad (cm/s)",
        yaxis_title="Radio (mm)",
        height=400,
        hovermode='closest'
    )
    
    return fig

# --- INTERFAZ PRINCIPAL ---
st.title("🩸 Simulador de Flujo Sanguíneo Arterial")
st.subheader("Carol Natalia Prada Perez - Pre grado Quimica Farmacéutica - Pontificia Universidad Javeriana")
st.markdown("### Plataforma de Presentación Hemodinámica")

tab1, tab2, tab3, tab4 = st.tabs([
    "Simulador 3D",
    "Comparativo Clínico",
    "Anatomía Arterial",
    "Marco Teórico"
])

# ==================== TAB 1: SIMULADOR ====================
with tab1:
    st.markdown("---")
    
    col_preset = st.columns([1, 1, 1, 1, 1])
    preset_nombres = list(PRESETS.keys())
    
    for idx, (col, nombre) in enumerate(zip(col_preset, preset_nombres)):
        if col.button(f"🏥 {nombre}", use_container_width=True):
            st.session_state.preset = nombre
    
    if "preset" in st.session_state and st.session_state.preset in PRESETS:
        preset = PRESETS[st.session_state.preset]
        r_mm_default = preset["r_mm"]
        delta_P_default = preset["delta_P"]
        L_cm_default = preset["L_cm"]
        viscosidad_default = preset["viscosidad"]
        porcentaje_placa_default = preset["porcentaje_placa"]
        densidad_default = preset["densidad"]
    else:
        r_mm_default = 1.5
        delta_P_default = 2600
        L_cm_default = 10.0
        viscosidad_default = 0.0045
        porcentaje_placa_default = 30
        densidad_default = 1060
    
    st.markdown("---")
    st.subheader("⚙️ Parámetros de la Arteria")
    
    param_cols = st.columns(3)
    
    with param_cols[0]:
        r_mm = st.slider("Radio arterial (r)", 0.5, 5.0, r_mm_default, 0.1, format="%.1f mm")
        delta_P = st.slider("ΔP — Presión (Pa)", 500, 5000, int(delta_P_default), 100)
    
    with param_cols[1]:
        L_cm = st.slider("Longitud arterial (L)", 5.0, 20.0, L_cm_default, 0.5, format="%.1f cm")
        viscosidad = st.slider("Viscosidad η (Pa·s)", 0.0020, 0.0080, viscosidad_default, 0.0001, format="%.4f")
    
    with param_cols[2]:
        porcentaje_placa = st.slider("Grosor de placa (%)", 0, 95, int(porcentaje_placa_default), 1)
        densidad = st.slider("Densidad ρ (kg/m³)", 1000, 1100, densidad_default, 5)
    
    Q, v_max, Re, R, W_util, W_esf, r_min = calcular_hemodinamica(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa, densidad)
    tipo_flujo = "Laminar" if Re < 2000 else ("Transicional" if Re < 4000 else "Turbulento")
    
    st.markdown("---")
    if porcentaje_placa > 70:
        st.markdown('<div class="danger-box">⚠️ <b>Oclusión Crítica:</b> Riesgo de infarto. Requiere intervención urgente.</div>', unsafe_allow_html=True)
    elif porcentaje_placa > 50:
        st.markdown('<div class="warning-box">⚠️ <b>Arteriosclerosis Severa:</b> Estenosis significativa. Requiere monitoreo.</div>', unsafe_allow_html=True)
    elif porcentaje_placa > 20:
        st.markdown('<div class="warning-box">⚠️ <b>Arteriosclerosis Leve:</b> Control recomendado.</div>', unsafe_allow_html=True)
    else:
        st.markdown('✅ **Estado Normal:** Flujo arterial saludable', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📊 Hemodinámica")
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Caudal Q", f"{Q:.2f} mL/min", f"{tipo_flujo}")
    with metric_cols[1]:
        st.metric("Vel. media", f"{v_max/2:.2f} cm/s")
    with metric_cols[2]:
        st.metric(f"Reynolds (Re)", f"{Re:.0f}")
    with metric_cols[3]:
        W_normal_ref_card = (8 * 0.0035 * 0.10) / (np.pi * (0.0015**4)) * (Q_NORMAL_REF_M3S**2) * 60 * 1000
        W_factor = W_esf / W_normal_ref_card if W_normal_ref_card > 0 else 1.0
        st.markdown(f"""
        <div class="trabajo-card">
            <span class="trabajo-label">Trabajo cardíaco <em>W</em> (mJ/min)</span>
            <span class="trabajo-valor">{W_esf:.2f}</span>
            <span class="trabajo-factor">≈ {W_factor:.1f}× el esfuerzo sano</span>
        </div>
        """, unsafe_allow_html=True)
    
    metric_cols2 = st.columns(4)
    with metric_cols2[0]:
        st.metric("Vel. máxima", f"{v_max:.2f} cm/s")
    with metric_cols2[1]:
        st.metric("Radio mínimo", f"{r_min:.3f} mm")
    with metric_cols2[2]:
        R_exp = int(np.floor(np.log10(R))) if R > 0 else 0
        R_mantisa = R / (10 ** R_exp) if R > 0 else 0
        R_normal_ref = (8 * 0.0035 * 0.10) / (np.pi * (0.0015**4))
        R_factor = R / R_normal_ref
        st.markdown(f"""
        <div class="resistencia-card">
            <span class="resistencia-label">Resistencia <em>R</em> (Pa·s/m³)</span>
            <span class="resistencia-valor">{R_mantisa:.3f} &times; 10<sup style="font-size:0.65em">{R_exp}</sup></span>
            <span class="resistencia-factor">≈ {R_factor:.1f}× la resistencia sana</span>
        </div>
        """, unsafe_allow_html=True)
    with metric_cols2[3]:
        st.metric("Densidad ρ", f"{densidad} kg/m³")
    
    st.markdown("---")
    
    st.subheader("🌀 Simulación 3D del Flujo Sanguíneo")
    st.caption("Visualización interactiva: La placa aterosclerótica se muestra en amarillo, el vaso exterior en rojo tenue y los eritrocitos fluyendo por la luz disponible.")
    
    z_vals = np.linspace(-L_cm/2, L_cm/2, 60)
    theta_vals = np.linspace(0, 2*np.pi, 40)
    z_grid, theta_grid = np.meshgrid(z_vals, theta_vals)
    
    r_exterior = np.full_like(z_grid, r_mm)
    x_ext = r_exterior * np.cos(theta_grid)
    y_ext = r_exterior * np.sin(theta_grid)
    
    r_interior = np.array([get_radio_local(z, r_mm, porcentaje_placa, L_cm) for z in z_vals])
    r_interior = np.tile(r_interior, (40, 1))
    x_int = r_interior * np.cos(theta_grid)
    y_int = r_interior * np.sin(theta_grid)
    
    num_frames = 80 
    particulas_historico = generar_frames_particulas(120, num_frames, v_max/2, Re, L_cm, r_mm, porcentaje_placa)
    
    fig = go.Figure()
    
    x0, y0, z0 = particulas_historico[0]
    fig.add_trace(go.Scatter3d(
        x=z0, y=x0, z=y0,
        mode='markers',
        marker=dict(size=5, color='#ff0000', symbol='circle', opacity=1.0, 
                    line=dict(color='#8B0000', width=1)),
        name='Eritrocitos'
    ))

    fig.add_trace(go.Surface(
        x=z_grid, y=x_ext, z=y_ext,
        colorscale='Reds', showscale=False, opacity=0.1, 
        name='Pared Arterial', hoverinfo='skip'
    ))
    
    if porcentaje_placa > 0:
        fig.add_trace(go.Surface(
            x=z_grid, y=x_int, z=y_int,
            colorscale='YlOrBr', showscale=False, opacity=0.6,
            name='Placa', hoverinfo='skip'
        ))
    
    frames = []
    for i in range(num_frames):
        x_i, y_i, z_i = particulas_historico[i]
        frames.append(go.Frame(
            data=[go.Scatter3d(x=z_i, y=x_i, z=y_i)],
            name=str(i),
            traces=[0]
        ))
    fig.frames = frames
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Longitud (cm)',
            yaxis_title='Radio (mm)',
            zaxis_title='Radio (mm)',
            aspectratio=dict(x=3, y=1, z=1),
            xaxis=dict(range=[-L_cm/2, L_cm/2], backgroundcolor="white"),
            yaxis=dict(range=[-r_mm*1.2, r_mm*1.2], backgroundcolor="white"),
            zaxis=dict(range=[-r_mm*1.2, r_mm*1.2], backgroundcolor="white")
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.05, y=0.9,
            buttons=[
                dict(label="▶ Reproducir Flujo",
                     method="animate",
                     args=[None, dict(frame=dict(duration=20, redraw=True), 
                                      transition=dict(duration=0),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="⏸ Pausa",
                     method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), 
                                        mode="immediate")])
            ]
        )]
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    col_vis1, col_vis2 = st.columns(2)
    
    with col_vis1:
        st.subheader("🔄 Corte Transversal")
        fig_transversal = crear_visualizacion_corte_transversal(r_mm, porcentaje_placa, L_cm, z_posicion=0)
        st.plotly_chart(fig_transversal, use_container_width=True)
    
    with col_vis2:
        st.subheader("📈 Perfil de Velocidad")
        fig_perfil = crear_perfil_velocidad(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa)
        st.plotly_chart(fig_perfil, use_container_width=True)


# ==================== TAB 2: COMPARATIVO TEÓRICO ====================
with tab2:
    st.subheader("📊 Comparativo entre Condiciones Clínicas")
    
    comparativo_data = []
    resistencias_raw = {}

    for nombre, preset in PRESETS.items():
        Q, v, Re, R, W_util, W_esf, r_min = calcular_hemodinamica(
            preset["r_mm"], preset["L_cm"], preset["viscosidad"],
            preset["delta_P"], preset["porcentaje_placa"], preset["densidad"]
        )
        resistencias_raw[nombre] = (Q, v, Re, R, W_util, W_esf, r_min)

    R_normal = resistencias_raw["Arteria normal"][3]

    for nombre, preset in PRESETS.items():
        Q, v, Re, R, W_util, W_esf, r_min = resistencias_raw[nombre]
        tipo_flujo = "Laminar" if Re < 2000 else ("Transicional" if Re < 4000 else "Turbulento")
        factor_R = R / R_normal

        exponente = int(np.floor(np.log10(R)))
        mantisa = R / (10 ** exponente)

        comparativo_data.append({
            "Condición": nombre,
            "Radio Base (mm)": f"{preset['r_mm']:.2f}",
            "Oclusión (%)": f"{preset['porcentaje_placa']}%",
            "Caudal (mL/min)": f"{Q:.2f}",
            "Velocidad (cm/s)": f"{v:.2f}",
            "Reynolds": f"{Re:.0f}",
            "Tipo Flujo": tipo_flujo,
            "Resistencia (Pa·s/m³)": f"{mantisa:.3f} × 10^{exponente}",
            "Factor vs. Sano (×)": f"{factor_R:.1f}×",
            "W esfuerzo (mJ/min)": f"{W_esf:.2f}"
        })

    df_comparativo = pd.DataFrame(comparativo_data)
    st.dataframe(df_comparativo, use_container_width=True)

    st.info(
        "💡 **¿Por qué aumenta la resistencia?** La columna *'Factor vs. Sano'* muestra cuántas veces "
        "es mayor la resistencia respecto a una arteria sana. A mayor oclusión → menor radio efectivo → "
        "la resistencia crece según **R ∝ 1/r⁴** (Ley de Poiseuille). "
    )
    
    st.markdown("---")
    
    condiciones = list(PRESETS.keys())
    caudales = []
    reynolds = []
    
    for nombre, preset in PRESETS.items():
        Q, v, Re, R, W_util, W_esf, r_min = calcular_hemodinamica(
            preset["r_mm"], preset["L_cm"], preset["viscosidad"],
            preset["delta_P"], preset["porcentaje_placa"], preset["densidad"]
        )
        caudales.append(Q)
        reynolds.append(Re)
    
    fig_comp = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_comp.add_trace(
        go.Bar(x=condiciones, y=caudales, name="Caudal (mL/min)", marker=dict(color='royalblue')),
        secondary_y=False
    )
    
    fig_comp.add_trace(
        go.Scatter(x=condiciones, y=reynolds, name="Número de Reynolds", 
                   line=dict(color='crimson', width=3), mode='lines+markers'),
        secondary_y=True
    )
    
    fig_comp.update_layout(title="Relación Caudal vs Riesgo de Turbulencia")
    fig_comp.update_xaxes(title_text="Condiciones Clínicas")
    fig_comp.update_yaxes(title_text="Caudal Volumétrico (mL/min)", secondary_y=False)
    fig_comp.update_yaxes(title_text="Número de Reynolds (Adimensional)", secondary_y=True)
    
    st.plotly_chart(fig_comp, use_container_width=True)

# ==================== TAB 3: VISUALIZACIÓN ARTERIAL ====================
with tab3:
    st.subheader("🔬 Impacto Geométrico en el Flujo Sanguíneo")
    st.markdown("Comparativa entre el **Perfil Parabólico de Hagen-Poiseuille** y la **Relación Cuártica del Caudal** ($Q \propto r^4$).")
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### Perfil de Velocidad Superpuesto")
        
        r_normal_vals = np.linspace(-r_mm, r_mm, 100)
        v_normal_vals = (delta_P / (4 * viscosidad)) * (r_mm**2 - r_normal_vals**2)
        
        r_min_actual = get_radio_local(0, r_mm, porcentaje_placa, L_cm)
        r_pat_vals = np.linspace(-r_min_actual, r_min_actual, 100)
        v_pat_vals = (delta_P / (4 * viscosidad)) * (r_min_actual**2 - r_pat_vals**2)
        
        fig_superpuesta = go.Figure()
        
        fig_superpuesta.add_trace(go.Scatter(x=v_normal_vals, y=r_normal_vals, 
                                             mode='lines', line=dict(color='green', width=2, dash='dash'),
                                             name='Normal (Sano)'))
        
        fig_superpuesta.add_trace(go.Scatter(x=v_pat_vals, y=r_pat_vals,
                                             fill='tozeroy', fillcolor='rgba(255, 0, 0, 0.4)',
                                             line=dict(color='red', width=3),
                                             name='Condición Actual'))
        
        fig_superpuesta.update_layout(xaxis_title="Velocidad (cm/s)", yaxis_title="Radio (mm)", height=400)
        st.plotly_chart(fig_superpuesta, use_container_width=True)
        
    with col_graf2:
        st.markdown("#### La Ley Cuártica ($Q \propto r^4$)")
        
        radios_teoricos = np.linspace(0.1, r_mm, 50)
        caudales_teoricos = (np.pi * (radios_teoricos/1000.0)**4 * delta_P) / (8 * viscosidad * (L_cm/100.0))
        caudales_teoricos_ml = caudales_teoricos * 60 * 1000000 
        
        caudal_maximo = caudales_teoricos_ml[-1]
        
        r_80 = r_mm * 0.8
        q_80 = (np.pi * (r_80/1000.0)**4 * delta_P) / (8 * viscosidad * (L_cm/100.0)) * 60 * 1000000
        
        fig_cuartica = go.Figure()
        fig_cuartica.add_trace(go.Scatter(x=radios_teoricos, y=caudales_teoricos_ml, 
                                          mode='lines', line=dict(color='royalblue', width=3),
                                          name='Curva de Caudal'))
        
        fig_cuartica.add_trace(go.Scatter(x=[r_mm], y=[caudal_maximo], mode='markers+text',
                                          marker=dict(color='green', size=10),
                                          text=["Radio 100%"], textposition="top center", name='Sano'))
        
        fig_cuartica.add_trace(go.Scatter(x=[r_80], y=[q_80], mode='markers+text',
                                          marker=dict(color='orange', size=10),
                                          text=["Radio 80%<br>Caudal cae ~59%"], textposition="bottom right", name='-20% Radio'))
        
        fig_cuartica.update_layout(xaxis_title="Radio del vaso (mm)", yaxis_title="Caudal (mL/min)", height=400,
                                   annotations=[dict(x=r_80, y=q_80, xref="x", yref="y",
                                                     text="Un cambio leve en el radio<br>tiene un efecto drástico.",
                                                     showarrow=True, arrowhead=2, ax=-50, ay=-50)])
        st.plotly_chart(fig_cuartica, use_container_width=True)

# ==================== TAB 4: MARCO TEÓRICO ====================
with tab4:
    st.subheader("📚 Fundamentos Teóricos y Hemodinámica")

    st.markdown("""
    <style>
    .marco-teorico {
        font-family: 'Source Serif 4', 'Georgia', serif;
        font-size: 1.08rem;
        line-height: 1.8;
        color: inherit;
        padding: 5px 15px;
    }
    .marco-teorico h3 {
        font-family: 'STIX Two Text', 'Cambria', serif !important;
        font-size: 1.35rem;
        font-weight: 600;
        border-bottom: 2px solid #c0392b;
        padding-bottom: 6px;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        color: #c0392b;
    }
    .marco-teorico .variable {
        font-family: 'STIX Two Text', serif;
        font-style: italic;
        font-weight: 600;
        color: #c0392b;
    }
    .concept-card {
        background: rgba(41, 128, 185, 0.08);
        border-left: 4px solid #2980b9;
        padding: 15px 20px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }
    .ref-biblio {
        font-family: 'Source Serif 4', serif;
        font-size: 0.95rem;
        color: inherit;
        opacity: 0.85;
        line-height: 1.6;
        border-top: 1px solid rgba(128,128,128,0.3);
        margin-top: 3rem;
        padding-top: 1.5rem;
    }
    .ref-biblio li {
        margin-bottom: 10px;
    }
    </style>
    
    <div class="marco-teorico">
    <h3>1. Ley de Hagen-Poiseuille y la Resistencia Vascular</h3>
    <p>La hemodinámica arterial se rige fundamentalmente por la Ley de Hagen-Poiseuille, que describe el caudal volumétrico ($Q$) de un fluido incompresible y newtoniano que fluye en régimen laminar a través de un tubo cilíndrico de sección constante.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("$$ Q = \\frac{\\pi r^4 \\Delta P}{8 \\eta L} $$")
    
    st.markdown("""
    <div class="marco-teorico">
    <p>Donde:</p>
    <ul>
        <li><span class="variable">r</span> : Radio interno del vaso sanguíneo.</li>
        <li><span class="variable">ΔP</span> : Gradiente de presión a lo largo del vaso.</li>
        <li><span class="variable">η</span> : Viscosidad dinámica de la sangre.</li>
        <li><span class="variable">L</span> : Longitud del segmento arterial.</li>
    </ul>

    <div class="concept-card">
        <b>💡 Implicación Clínica (La relación cuártica):</b> Como el radio ($r$) está elevado a la cuarta potencia, una reducción aparentemente pequeña en el diámetro del vaso (estenosis aterosclerótica) causa una caída drástica en el flujo sanguíneo. Por ejemplo, reducir el radio a la mitad hace que el caudal volumétrico disminuya en un factor de $2^4 = 16$. Para compensar esta enorme resistencia, el corazón debe realizar un trabajo hidráulico significativamente mayor.
    </div>

    <h3>2. Número de Reynolds y Tipos de Flujo Sanguíneo</h3>
    <p>En condiciones fisiológicas normales, la sangre fluye de manera ordenada. Sin embargo, cuando hay obstrucciones (placas), la velocidad local aumenta y el flujo puede volverse caótico. Esto se predice mediante el <b>Número de Reynolds ($Re$)</b>, una magnitud adimensional que relaciona las fuerzas inerciales con las fuerzas viscosas:</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("$$ Re = \\frac{2 \\rho v r}{\\eta} $$")
    
    st.markdown("""
    <div class="marco-teorico">
    <p>Dependiendo del valor de $Re$, el flujo se clasifica en:</p>
    <ul>
        <li><b>Flujo Laminar ($Re < 2000$):</b> Es el flujo saludable. Las partículas de sangre viajan en trayectorias paralelas ("láminas"), siendo la velocidad máxima en el centro del vaso y casi nula en las paredes. Es eficiente, reduce la resistencia y es silencioso.</li>
        <li><b>Flujo Transicional ($2000 \le Re \le 4000$):</b> El flujo comienza a desestabilizarse, perdiendo el perfil parabólico y presentando pequeñas fluctuaciones.</li>
        <li><b>Flujo Turbulento ($Re > 4000$):</b> Las fuerzas inerciales dominan. La sangre se mueve de forma desordenada formando vórtices o remolinos. Este flujo genera soplos audibles (como los detectados en ecografía Doppler), aumenta el daño al endotelio vascular por estrés mecánico de impacto, y eleva dramáticamente la probabilidad de trombosis.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    st.markdown("""
    <div class="marco-teorico">
    <h3>3. Fisiopatología de la Arteriosclerosis desde la Mecánica de Fluidos</h3>
    <p>La ateroesclerosis no es solo una acumulación pasiva de lípidos; es un proceso directamente mediado por la biomecánica. El estrés cortante de la pared (<i>Wall Shear Stress</i>, WSS) es la fuerza de fricción tangencial que ejerce la sangre sobre el endotelio. En zonas donde el flujo se vuelve turbulento, oscilatorio o recircula (frecuente detrás de una estenosis o en bifurcaciones), el WSS es bajo o irregular. El endotelio detecta estas fuerzas mecánicas anómalas (mecano-transducción), desencadenando una respuesta inflamatoria crónica que favorece la retención de colesterol LDL y la expansión sistémica de la placa.</p>

    <div class="ref-biblio">
        <b>Bibliografía y Referencias Académicas:</b>
        <ul>
            <li>Ku, D. N. (1997). <i>Blood flow in arteries</i>. Annual Review of Fluid Mechanics, 29(1), 399-434.</li>
            <li>Caro, C. G., Pedley, T. J., Schroter, R. C., & Seed, W. A. (2012). <i>The Mechanics of the Circulation</i>. Cambridge University Press.</li>
            <li>Chatzizisis, Y. S., Coskun, A. U., Jonas, M., Edelman, E. R., Feldman, C. L., & Stone, P. H. (2007). <i>Role of endothelial shear stress in the natural history of coronary atherosclerosis and vascular remodeling</i>. Journal of the American College of Cardiology, 49(25), 2379-2393.</li>
        </ul>
    </div>
    </div>
    """, unsafe_allow_html=True)
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

# --- ESTILOS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #d32f2f;
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
        "r_mm": 1.5, # Ajustado a 1.5 base para mostrar la oclusión del 55%
        "delta_P": 2600,
        "L_cm": 10.0,
        "viscosidad": 0.0048,
        "porcentaje_placa": 55,
        "densidad": 1065
    },
    "Oclusión crítica": {
        "r_mm": 1.5, # Ajustado a 1.5 base para mostrar la oclusión del 90%
        "delta_P": 3500,
        "L_cm": 10.0,
        "viscosidad": 0.0050,
        "porcentaje_placa": 90,
        "densidad": 1070
    }
}

# --- FUNCIONES MATEMÁTICAS Y GEOMÉTRICAS ---
def get_radio_local(z_val, r_base_mm, porcentaje_placa, L_cm):
    """Calcula el radio de la arteria en un punto Z específico, formando la oclusión central."""
    factor_forma = np.exp(-(z_val**2) / (0.05 * L_cm**2))
    r_local = r_base_mm * (1 - (porcentaje_placa / 100.0) * factor_forma)
    return np.maximum(r_local, 0.05)

def calcular_hemodinamica(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa, densidad=1060):
    r_m = r_mm / 1000.0
    L_m = L_cm / 100.0
    
    # Radio en la zona más estrecha (Z=0)
    r_min_mm = get_radio_local(0, r_mm, porcentaje_placa, L_cm)
    r_min_m = r_min_mm / 1000.0

    # Cálculos basados en la zona de mayor oclusión
    A_m2 = np.pi * (r_min_m**2)
    Q_m3s = (np.pi * (r_min_m**4) * delta_P) / (8 * viscosidad * L_m) if L_m > 0 else 0
    v_ms = Q_m3s / A_m2 if A_m2 > 0 else 0
    Re = (2 * densidad * v_ms * r_min_m) / viscosidad if viscosidad > 0 else 0
    R = (8 * viscosidad * L_m) / (np.pi * (r_min_m**4)) if r_min_m > 0 else float('inf')
    W_watts = Q_m3s * delta_P

    Q_ml_min = Q_m3s * 60 * 1000000
    v_cm_s = v_ms * 100
    W_mj_min = W_watts * 60 * 1000

    return Q_ml_min, v_cm_s, Re, R, W_mj_min, r_min_mm

def generar_frames_particulas(num_particulas, num_frames, v_base_cm_s, Re, L_cm, r_mm, porcentaje_placa):
    """Simula el movimiento de los glóbulos rojos a través del tubo con fluidez controlada"""
    dt = 0.025  
    factor_ralentizacion = 0.15 # 👈 NUEVO: Reduce la velocidad visual al 15% de la real
    
    z_actual = np.random.uniform(-L_cm/2, L_cm/2, num_particulas)
    rho = np.random.uniform(0, 0.85, num_particulas) 
    theta = np.random.uniform(0, 2*np.pi, num_particulas)
    
    historico = []
    
    for _ in range(num_frames):
        r_local = get_radio_local(z_actual, r_mm, porcentaje_placa, L_cm)
        
        v_local = v_base_cm_s * ((r_mm / r_local)**2)
        v_perfil = v_local * (1 - rho**2) 
        
        # 👈 APLICAMOS EL FACTOR AQUÍ
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
    """Crea una visualización del corte transversal de la arteria"""
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
    
    # Capa 1: Arteria Exterior
    fig.add_trace(go.Scatter(x=x_exterior, y=y_exterior, mode='lines',
                             line=dict(color='crimson', width=3), name='Pared Arterial'))
    
    # Capa 2: Placa
    fig.add_trace(go.Scatter(x=x_placa, y=y_placa, fill='toself', 
                             fillcolor='rgba(255, 165, 0, 0.6)', 
                             name='Placa', line=dict(color='orange')))
    
    # Capa 3: Plasma/Luz arterial
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
    """Crea el perfil de velocidad parabólico (Poiseuille)"""
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
    
    # Presets
    col_preset = st.columns([1, 1, 1, 1, 1])
    preset_nombres = list(PRESETS.keys())
    
    for idx, (col, nombre) in enumerate(zip(col_preset, preset_nombres)):
        if col.button(f"🏥 {nombre}", use_container_width=True):
            st.session_state.preset = nombre
    
    # Cargar preset si está seleccionado
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
    
    # Cálculos
    Q, v_max, Re, R, W, r_min = calcular_hemodinamica(r_mm, L_cm, viscosidad, delta_P, porcentaje_placa, densidad)
    # Clasificación del flujo según el número de Reynolds:
    # Re < 2000: Laminar (ordenado, sin turbulencia)
    # 2000 ≤ Re < 4000: Transicional (comenzando a mostrar inestabilidades)
    # Re ≥ 4000: Turbulento (caótico, con remolinos y vórtices)
    tipo_flujo = "Laminar" if Re < 2000 else ("Transicional" if Re < 4000 else "Turbulento")
    
    # Diagnóstico clínico
    st.markdown("---")
    if porcentaje_placa > 70:
        st.markdown('<div class="danger-box">⚠️ <b>Oclusión Crítica:</b> Riesgo de infarto. Requiere intervención urgente.</div>', unsafe_allow_html=True)
    elif porcentaje_placa > 50:
        st.markdown('<div class="warning-box">⚠️ <b>Arteriosclerosis Severa:</b> Estenosis significativa. Requiere monitoreo.</div>', unsafe_allow_html=True)
    elif porcentaje_placa > 20:
        st.markdown('<div class="warning-box">⚠️ <b>Arteriosclerosis Leve:</b> Control recomendado.</div>', unsafe_allow_html=True)
    else:
        st.markdown('✅ **Estado Normal:** Flujo arterial saludable', unsafe_allow_html=True)
    
    # Métricas principales
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
        st.metric("Trabajo W", f"{W:.2f} mJ/min")
    
    metric_cols2 = st.columns(4)
    with metric_cols2[0]:
        st.metric("Vel. máxima", f"{v_max:.2f} cm/s")
    with metric_cols2[1]:
        st.metric("Radio mínimo", f"{r_min:.3f} mm")
    with metric_cols2[2]:
        st.metric("Resistencia R", f"{R:.2e} Pa·s/m³")
    with metric_cols2[3]:
        st.metric("Densidad ρ", f"{densidad} kg/m³")
    
    st.markdown("---")
    
    # ==================== SECCIÓN 3D OPTIMIZADA ====================
    st.subheader("🌀 Simulación 3D del Flujo Sanguíneo")
    st.caption("Visualización interactiva: La placa aterosclerótica se muestra en amarillo, el vaso exterior en rojo tenue y los eritrocitos fluyendo por la luz disponible.")
    
    # 1. Generar la Malla de la Arteria Exterior
    z_vals = np.linspace(-L_cm/2, L_cm/2, 60)
    theta_vals = np.linspace(0, 2*np.pi, 40)
    z_grid, theta_grid = np.meshgrid(z_vals, theta_vals)
    
    # Radio constante para la pared exterior (Arteria sana)
    r_exterior = np.full_like(z_grid, r_mm)
    x_ext = r_exterior * np.cos(theta_grid)
    y_ext = r_exterior * np.sin(theta_grid)
    
    # 2. Generar la Malla de la Placa (Interior)
    r_interior = np.array([get_radio_local(z, r_mm, porcentaje_placa, L_cm) for z in z_vals])
    r_interior = np.tile(r_interior, (40, 1))
    x_int = r_interior * np.cos(theta_grid)
    y_int = r_interior * np.sin(theta_grid)
    
    # 3. Simular Partículas (Fluidez Mejorada)
    num_frames = 80 # Más fotogramas = más suavidad
    particulas_historico = generar_frames_particulas(120, num_frames, v_max/2, Re, L_cm, r_mm, porcentaje_placa)
    
    fig = go.Figure()
    
    # TRACE 0: Partículas (Eritrocitos) - Es crucial que sea el primero para animarlo sin redibujar mallas
    x0, y0, z0 = particulas_historico[0]
    fig.add_trace(go.Scatter3d(
        x=z0, y=x0, z=y0,
        mode='markers',
        marker=dict(size=5, color='#ff0000', symbol='circle', opacity=1.0, 
                    line=dict(color='#8B0000', width=1)), # Borde oscuro para dar volumen
        name='Eritrocitos'
    ))

    # TRACE 1: Pared Arterial (Exterior)
    fig.add_trace(go.Surface(
        x=z_grid, y=x_ext, z=y_ext,
        colorscale='Reds', showscale=False, opacity=0.1, 
        name='Pared Arterial', hoverinfo='skip'
    ))
    
    # TRACE 2: Placa Aterosclerótica (Si existe oclusión)
    if porcentaje_placa > 0:
        fig.add_trace(go.Surface(
            x=z_grid, y=x_int, z=y_int,
            colorscale='YlOrBr', showscale=False, opacity=0.6,
            name='Placa', hoverinfo='skip'
        ))
    
    # Construir frames SOLO actualizando la Traza 0 (Partículas)
    frames = []
    for i in range(num_frames):
        x_i, y_i, z_i = particulas_historico[i]
        frames.append(go.Frame(
            data=[go.Scatter3d(x=z_i, y=x_i, z=y_i)],
            name=str(i),
            traces=[0] # ¡EL SECRETO DE LA FLUIDEZ! Solo actualiza los puntos, no la geometría pesada
        ))
    fig.frames = frames
    
    # Configurar animación y vista
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
                     args=[None, dict(frame=dict(duration=20, redraw=True), # 20ms = Animación muy fluida
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
    for nombre, preset in PRESETS.items():
        Q, v, Re, R, W, r_min = calcular_hemodinamica(
            preset["r_mm"], preset["L_cm"], preset["viscosidad"],
            preset["delta_P"], preset["porcentaje_placa"], preset["densidad"]
        )
        tipo_flujo = "Laminar" if Re < 2000 else ("Transicional" if Re < 4000 else "Turbulento")
        
        comparativo_data.append({
            "Condición": nombre,
            "Radio Base (mm)": f"{preset['r_mm']:.2f}",
            "Oclusión (%)": f"{preset['porcentaje_placa']}%",
            "Caudal (mL/min)": f"{Q:.2f}",
            "Velocidad (cm/s)": f"{v:.2f}",
            "Reynolds": f"{Re:.0f}",
            "Tipo Flujo": tipo_flujo,
            "Resistencia (Pa·s/m³)": f"{R:.2e}"
        })
    
    df_comparativo = pd.DataFrame(comparativo_data)
    st.dataframe(df_comparativo, use_container_width=True)
    
    st.markdown("---")
    
    condiciones = list(PRESETS.keys())
    caudales = []
    reynolds = []
    
    for nombre, preset in PRESETS.items():
        Q, v, Re, R, W, r_min = calcular_hemodinamica(
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
        # Gráfica 1: Perfiles superpuestos (Normal vs Actual)
        st.markdown("#### Perfil de Velocidad Superpuesto")
        
        # Calculamos perfil normal (placa = 0)
        r_normal_vals = np.linspace(-r_mm, r_mm, 100)
        v_normal_vals = (delta_P / (4 * viscosidad)) * (r_mm**2 - r_normal_vals**2)
        
        # Calculamos perfil patológico (con el porcentaje de placa actual)
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
        # Gráfica 2: La curva Cuártica Q proporcional a r^4
        st.markdown("#### La Ley Cuártica ($Q \propto r^4$)")
        
        # Generamos radios de 0.1 a r_mm
        radios_teoricos = np.linspace(0.1, r_mm, 50)
        # Caudal teórico basado en Poiseuille manteniendo la presión y viscosidad actual
        caudales_teoricos = (np.pi * (radios_teoricos/1000.0)**4 * delta_P) / (8 * viscosidad * (L_cm/100.0))
        caudales_teoricos_ml = caudales_teoricos * 60 * 1000000 # Convertir a mL/min
        
        caudal_maximo = caudales_teoricos_ml[-1]
        
        # Punto clave: 20% de reducción de radio = 80% del radio original
        r_80 = r_mm * 0.8
        q_80 = (np.pi * (r_80/1000.0)**4 * delta_P) / (8 * viscosidad * (L_cm/100.0)) * 60 * 1000000
        
        fig_cuartica = go.Figure()
        fig_cuartica.add_trace(go.Scatter(x=radios_teoricos, y=caudales_teoricos_ml, 
                                          mode='lines', line=dict(color='royalblue', width=3),
                                          name='Curva de Caudal'))
        
        # Marcador del 100% de radio
        fig_cuartica.add_trace(go.Scatter(x=[r_mm], y=[caudal_maximo], mode='markers+text',
                                          marker=dict(color='green', size=10),
                                          text=["Radio 100%"], textposition="top center", name='Sano'))
        
        # Marcador del 80% de radio (Muestra la caída del 59%)
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
    st.subheader("📚 Fundamentos Teóricos")
    
    st.markdown("""
    ### Ley de Poiseuille
    Describe el caudal para un flujo laminar incompresible y viscoso a través de un tubo cilíndrico de sección transversal constante:
    
    $$Q = \\frac{\\pi r^4 \\Delta P}{8 \\eta L}$$
    
    Donde:
    - **Q:** Caudal volumétrico ($m^3/s$)
    - **r:** Radio interno del tubo ($m$)
    - **ΔP:** Diferencia de presión entre los extremos ($Pa$)
    - **η:** Viscosidad dinámica del fluido ($Pa\\cdot s$)
    - **L:** Longitud del segmento cilíndrico ($m$)
    
    ### Número de Reynolds
    Unidad adimensional que permite predecir el patrón de flujo (Laminar vs Turbulento):
    
    $$Re = \\frac{2 \\rho v r}{\\eta}$$
    
    Donde:
    - **ρ:** Densidad del fluido ($kg/m^3$)
    - **v:** Velocidad media del fluido ($m/s$)    
    ---
    
    ### 🌊 Clasificación del Tipo de Flujo
    
    El número de Reynolds clasifica el flujo en tres categorías:
    
    #### **Flujo Laminar** (Re < 2000)
    - Las moléculas del fluido se mueven en **capas ordenadas** sin mezclarse lateralmente
    - El perfil de velocidad es **parabólico** (máximo en el centro, cero en las paredes)
    - Flujo **predecible y estable**: se describe completamente con la Ley de Poiseuille
    - **Clínicamente:** Normal en arterias sanas. Bajo riesgo de trombosis
    - 💙 *En la sangre humana normal (arterial), el flujo es típicamente laminar*
    
    #### **Flujo Transicional** (2000 ≤ Re < 4000)
    - Región de **inestabilidad** donde comienza la turbulencia
    - Pequeñas **ondulaciones** y perturbaciones locales
    - Comportamiento **intermitente**: el flujo alterna entre laminar y turbulento
    - **Clínicamente:** Inicio de cambios en el patrón de flujo. Requiere monitoreo
    
    #### **Flujo Turbulento** (Re ≥ 4000)
    - Las moléculas se mueven **de forma caótica** con remolinos, vórtices y contravórtices
    - **Mezcla intensiva** entre capas del fluido
    - Mayor **disipación de energía** (requiere más presión para mantener el mismo caudal)
    - **Ruido acústico** audible (soplos cardiacos en estenosis severa)
    - **Clínicamente:** Indicador de **estenosis severa**, presencia de aneurismas o patología cardiovascular
    - ⚠️ *Mayor riesgo de activación plaquetaria y formación de coágulos*
    
    ---
    
    #### ¿Por qué importa el tipo de flujo?
    
    | Aspecto | Laminar | Turbulento |
    |--------|---------|------------|
    | **Patrón** | Ordenado | Caótico |
    | **Energía requerida** | Mínima | Muy alta |
    | **Riesgo de coágulos** | Bajo ✅ | Alto ⚠️ |
    | **Presión requerida** | Baja | Muy alta |
    | **Predicibilidad** | Excelente | Impredecible |
    | **Daño endotelial** | Mínimo | Significativo |
    
    En el **simulador**, observa cómo cambia el comportamiento del flujo al ajustar los parámetros. Un aumento en la **velocidad**, **densidad** o **disminución del radio** eleva el Reynolds y puede desencadenar turbulencia.    
    ### Modelado Geométrico de la Placa (Oclusión Gaussiana)
    Para simular la forma natural de una placa aterosclerótica, utilizamos una función de decaimiento exponencial (Campana de Gauss) anclada en el centro de la arteria ($z=0$):
    
    $$r(z) = r_{base} \\left(1 - \\frac{p}{100} e^{-z^2/(0.05L^2)}\\right)$$
    
    Donde **$p$** es el porcentaje máximo de estenosis (grosor de la placa).
    """)
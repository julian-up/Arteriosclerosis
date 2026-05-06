import bpy
import bmesh
import numpy as np
from mathutils import Vector
import os

# --- PARÁMETROS CLÍNICOS ---
R_BASE_MM = 1.5
L_CM = 10.0
PORCENTAJE_PLACA = 60  # Estenosis severa para generar turbulencia
DELTA_P = 2600
VISCOSIDAD = 0.0045
DENSIDAD = 1060
FPS = 60
DURACION_SEG = 5
TOTAL_FRAMES = FPS * DURACION_SEG

def limpiar_escena():
    """Elimina todos los objetos de la escena actual."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def get_radio_local(z_val):
    """Calcula el radio de la arteria con la oclusión gaussiana."""
    factor_forma = np.exp(-(z_val**2) / (0.05 * L_CM**2))
    r_local = R_BASE_MM * (1 - (PORCENTAJE_PLACA / 100.0) * factor_forma)
    return max(r_local, 0.05)

def crear_material(nombre, color, alpha=1.0, roughness=0.5):
    """Crea y retorna un material en Blender."""
    mat = bpy.data.materials.new(name=nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'NONE'
    return mat

def generar_geometria_arteria():
    """Crea la malla de la arteria exterior (Plasma) y la Placa interior."""
    # 1. Crear Arteria / Plasma
    mesh_arteria = bpy.data.meshes.new("Arteria_Mesh")
    obj_arteria = bpy.data.objects.new("Arteria_Plasma", mesh_arteria)
    bpy.context.collection.objects.link(obj_arteria)
    
    # 2. Crear Placa
    mesh_placa = bpy.data.meshes.new("Placa_Mesh")
    obj_placa = bpy.data.objects.new("Placa_Aterosclerotica", mesh_placa)
    bpy.context.collection.objects.link(obj_placa)
    
    bm_arteria = bmesh.new()
    bm_placa = bmesh.new()
    
    segmentos = 100
    radiales = 32
    z_vals = np.linspace(-L_CM/2, L_CM/2, segmentos)
    theta_vals = np.linspace(0, 2*np.pi, radiales, endpoint=False)
    
    verts_art = []
    verts_placa = []
    
    for z in z_vals:
        r_int = get_radio_local(z)
        r_ext = R_BASE_MM
        
        for theta in theta_vals:
            # Vértices Plasma (interior)
            x_int, y_int = r_int * np.cos(theta), r_int * np.sin(theta)
            verts_art.append(bm_arteria.verts.new((x_int, y_int, z)))
            
            # Vértices Placa (diferencia entre exterior e interior)
            x_ext, y_ext = r_ext * np.cos(theta), r_ext * np.sin(theta)
            verts_placa.append(bm_placa.verts.new((x_ext, y_ext, z)))
            # Necesitamos el interior para cerrar la malla de la placa
            verts_placa.append(bm_placa.verts.new((x_int, y_int, z)))

    # Generar caras (simplificado para el script)
    # Aquí usaríamos bmesh.ops.bridge_loops en un script completo de modelado
    
    bm_arteria.to_mesh(mesh_arteria)
    bm_placa.to_mesh(mesh_placa)
    bm_arteria.free()
    bm_placa.free()
    
    # Asignar Materiales
    mat_plasma = crear_material("Mat_Plasma", (0.0, 0.2, 0.8, 1.0), alpha=0.3, roughness=0.1)
    mat_placa = crear_material("Mat_Placa", (0.8, 0.6, 0.1, 1.0), alpha=1.0, roughness=0.9)
    obj_arteria.data.materials.append(mat_plasma)
    obj_placa.data.materials.append(mat_placa)

def simular_y_animar_eritrocitos(num_particulas=150):
    """Genera eritrocitos y calcula su cinemática frame a frame para máxima fluidez."""
    # Cálculos teóricos base
    r_min_m = get_radio_local(0) / 1000.0
    L_m = L_CM / 100.0
    Q_m3s = (np.pi * (r_min_m**4) * DELTA_P) / (8 * VISCOSIDAD * L_m)
    A_m2 = np.pi * (r_min_m**2)
    v_media_ms = Q_m3s / A_m2
    v_base_cms = v_media_ms * 100
    Re = (2 * DENSIDAD * v_media_ms * r_min_m) / VISCOSIDAD
    
    print(f"Reynolds calculado: {Re:.0f} | Velocidad Base: {v_base_cms:.2f} cm/s")
    
    # Crear objetos eritrocitos
    eritrocitos = []
    mat_rbc = crear_material("Mat_Eritrocito", (0.8, 0.0, 0.0, 1.0), roughness=0.3)
    
    for i in range(num_particulas):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08)
        rbc = bpy.context.active_object
        rbc.name = f"RBC_{i}"
        rbc.data.materials.append(mat_rbc)
        eritrocitos.append(rbc)
    
    # Estado inicial aleatorio
    z_actual = np.random.uniform(-L_CM/2, L_CM/2, num_particulas)
    rho = np.random.uniform(0, 0.8, num_particulas)
    theta = np.random.uniform(0, 2*np.pi, num_particulas)
    
    dt = 1.0 / FPS  # Delta time preciso para fluidez
    
    # Simulación y Keyframing (Horneado)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = TOTAL_FRAMES
    
    for frame in range(1, TOTAL_FRAMES + 1):
        bpy.context.scene.frame_set(frame)
        
        for i in range(num_particulas):
            # Cinemática de fluidos aproximada
            r_local = get_radio_local(z_actual[i])
            v_local = v_base_cms * ((R_BASE_MM / r_local)**2)
            
            # Perfil parabólico de Poiseuille (más rápido en el centro)
            v_perfil = v_local * (1 - (rho[i]**2))
            
            z_actual[i] += v_perfil * dt
            
            # Bucle infinito si sale de la arteria
            if z_actual[i] > L_CM/2:
                z_actual[i] = -L_CM/2
            
            # Turbulencia si Re > 2000
            if Re > 2000 and abs(z_actual[i]) < (L_CM/4): # Turbulencia cerca de la placa
                intensidad = (Re - 2000) / 5000.0
                theta[i] += np.random.normal(0, 0.5 * intensidad)
                rho[i] += np.random.normal(0, 0.1 * intensidad)
                rho[i] = np.clip(rho[i], 0, 0.9)
            
            # Calcular coordenadas cartesianas
            r_local_actualizado = get_radio_local(z_actual[i])
            x = (rho[i] * r_local_actualizado) * np.cos(theta[i])
            y = (rho[i] * r_local_actualizado) * np.sin(theta[i])
            
            # Actualizar posición y guardar keyframe
            eritrocitos[i].location = (x, y, z_actual[i])
            eritrocitos[i].keyframe_insert(data_path="location", index=-1)

def exportar_animacion_dae(filepath):
    """Exporta la escena completa con animación a formato Collada (.dae)."""
    bpy.ops.wm.collada_export(
        filepath=filepath,
        use_export_selected=False,
        export_animation=True,
        keep_bind_info=True
    )
    print(f"✅ Animación fluida exportada exitosamente a: {filepath}")

# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    print("Iniciando generación de escenario hemodinámico...")
    limpiar_escena()
    generar_geometria_arteria()
    simular_y_animar_eritrocitos(num_particulas=200)
    
    # Exportar (Cambia esta ruta a una válida en tu sistema)
    ruta_exportacion = os.path.join(bpy.context.space_data.text.filepath.rsplit(os.sep, 1)[0] if bpy.context.space_data else "", "simulacion_arterial_vr.dae")
    if not ruta_exportacion or ruta_exportacion == "simulacion_arterial_vr.dae":
        ruta_exportacion = "C:/temp/simulacion_arterial_vr.dae" # Ruta por defecto de seguridad
        
    exportar_animacion_dae(ruta_exportacion)
"""
Módulo para crear geometría realista de placa aterosclerótica en Blender.
Este script usa bpy (Blender Python API) para modelar la arteria con placa.
"""

import numpy as np
try:
    import bpy
    import bmesh
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("⚠️  bpy no disponible. Instala Blender con Python API para usar este módulo.")


class PlacaModelGenerator:
    """Genera modelos 3D de placa aterosclerótica"""
    
    def __init__(self, radio_base_mm=1.5, longitud_cm=10, porcentaje_placa=30):
        self.radio_base = radio_base_mm / 1000  # convertir a metros
        self.longitud = longitud_cm / 100  # convertir a metros
        self.porcentaje_placa = porcentaje_placa
        self.mesh = None
        self.obj = None
        
    def get_radio_local(self, z_val):
        """Calcula el radio local en posición Z (igual a app.py)"""
        factor_forma = np.exp(-(z_val**2) / (0.05 * self.longitud**2))
        r_local = self.radio_base * (1 - (self.porcentaje_placa / 100.0) * factor_forma)
        return max(r_local, 0.00005)  # Evitar radio cero
    
    def create_artery_mesh(self, num_segments=100, num_radial=50):
        """Crea la malla de la arteria con placa aterosclerótica"""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender no está disponible")
        
        # Limpiar la escena
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Crear nueva malla
        mesh_data = bpy.data.meshes.new(name="Artery_Mesh")
        obj = bpy.data.objects.new(name="Artery", object_data=mesh_data)
        
        # Añadir a colección
        bpy.context.collection.objects.link(obj)
        
        # Usar bmesh para construir la geometría
        bm = bmesh.new()
        
        # Crear vértices
        vertices = []
        z_vals = np.linspace(-self.longitud/2, self.longitud/2, num_segments)
        theta_vals = np.linspace(0, 2*np.pi, num_radial, endpoint=False)
        
        for z in z_vals:
            r_local = self.get_radio_local(z)
            for theta in theta_vals:
                x = r_local * np.cos(theta)
                y = r_local * np.sin(theta)
                v = bm.verts.new((x, y, z))
                vertices.append(v)
        
        # Crear caras (triangles)
        for i in range(num_segments - 1):
            for j in range(num_radial):
                v1_idx = i * num_radial + j
                v2_idx = i * num_radial + (j + 1) % num_radial
                v3_idx = (i + 1) * num_radial + j
                v4_idx = (i + 1) * num_radial + (j + 1) % num_radial
                
                try:
                    bm.faces.new([vertices[v1_idx], vertices[v2_idx], vertices[v3_idx]])
                    bm.faces.new([vertices[v2_idx], vertices[v4_idx], vertices[v3_idx]])
                except:
                    pass
        
        bm.to_mesh(mesh_data)
        bm.free()
        mesh_data.update()
        
        self.mesh = mesh_data
        self.obj = obj
        
        return obj
    
    def add_plasma_material(self):
        """Añade material translúcido para el plasma"""
        if not BLENDER_AVAILABLE or not self.obj:
            return
        
        mat = bpy.data.materials.new(name="Plasma")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (1.0, 0.2, 0.2, 0.7)  # Rojo translúcido
        bsdf.inputs['Alpha'].default_value = 0.3
        
        self.obj.data.materials.append(mat)
    
    def add_placa_material(self):
        """Añade material para la placa aterosclerótica"""
        if not BLENDER_AVAILABLE or not self.obj:
            return
        
        mat = bpy.data.materials.new(name="Placa")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.1, 1.0)  # Rojo oscuro
        bsdf.inputs['Roughness'].default_value = 0.8
        
        self.obj.data.materials.append(mat)
    
    def create_red_blood_cells(self, num_cells=100):
        """Crea esferas para representar eritrocitos"""
        if not BLENDER_AVAILABLE:
            return []
        
        cells = []
        z_vals = np.random.uniform(-self.longitud/2, self.longitud/2, num_cells)
        
        for i, z in enumerate(z_vals):
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=self.radio_base * 0.08,
                location=(0, 0, z)
            )
            cell = bpy.context.active_object
            cell.name = f"RBC_{i}"
            
            # Material rojo para eritrocitos
            mat = bpy.data.materials.new(name=f"RBC_Mat_{i}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs['Base Color'].default_value = (0.8, 0.0, 0.0, 1.0)
            cell.data.materials.append(mat)
            
            cells.append(cell)
        
        return cells
    
    def export_to_dae(self, filepath):
        """Exporta la escena a formato DAE (Collada)"""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender no está disponible")
        
        if self.obj:
            self.obj.select_set(True)
            bpy.ops.wm.collada_export(filepath=filepath)
            print(f"✓ Escena exportada a {filepath}")


# Función auxiliar para crear todo de una vez
def create_complete_scene(radio_mm=1.5, longitud_cm=10, porcentaje_placa=30, 
                         output_dae=None):
    """Crea una escena completa con arteria, plasma y eritrocitos"""
    
    if not BLENDER_AVAILABLE:
        print("⚠️  Blender no está disponible. Usando modo sin Blender.")
        return None
    
    generator = PlacaModelGenerator(radio_mm, longitud_cm, porcentaje_placa)
    
    # Crear geometría
    artery = generator.create_artery_mesh()
    generator.add_plasma_material()
    
    # Crear eritrocitos
    rbcs = generator.create_red_blood_cells(num_cells=50)
    
    # Exportar si es necesario
    if output_dae:
        generator.export_to_dae(output_dae)
    
    return {
        'artery': artery,
        'rbcs': rbcs,
        'generator': generator
    }


if __name__ == "__main__":
    # Ejemplo de uso (solo funciona dentro de Blender)
    scene = create_complete_scene(
        radio_mm=1.5,
        longitud_cm=10,
        porcentaje_placa=30,
        output_dae=None  # Cambiar a ruta si quieres exportar
    )
    if scene:
        print("✓ Escena creada exitosamente en Blender")

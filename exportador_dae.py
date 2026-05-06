"""
Exportador de geometría arterial a formato DAE (Collada/Digital Asset Exchange).
Permite crear geometría en Python y exportarla para VR o importación en otros software.
"""

import numpy as np
from pathlib import Path


class GeneradorDAE:
    """Genera archivos DAE con geometría de arterias y flujo sanguíneo"""
    
    def __init__(self, output_path="arteria_3d.dae"):
        """
        Inicializa el generador
        
        Args:
            output_path: Ruta del archivo DAE a generar
        """
        self.output_path = Path(output_path)
        self.vertices = []
        self.faces = []
        self.materials = {}
        self.geometrias = {}
    
    def crear_cilindro_ocluido(self, radio_mm=1.5, longitud_cm=10, 
                               porcentaje_placa=30, num_segments=100, num_radial=50):
        """
        Crea un cilindro con oclusión gaussiana
        
        Args:
            radio_mm: Radio base de la arteria
            longitud_cm: Longitud de la arteria
            porcentaje_placa: Porcentaje de estenosis
            num_segments: Segmentos longitudinales
            num_radial: Segmentos radiales
        """
        vertices = []
        faces = []
        
        z_vals = np.linspace(-longitud_cm/2, longitud_cm/2, num_segments)
        theta_vals = np.linspace(0, 2*np.pi, num_radial, endpoint=False)
        
        def get_radio_local(z):
            """Oclusión gaussiana"""
            factor_forma = np.exp(-(z**2) / (0.05 * (longitud_cm/100)**2))
            r = radio_mm * (1 - (porcentaje_placa / 100.0) * factor_forma)
            return max(r, 0.05)
        
        # Generar vértices
        vertex_indices = {}
        idx = 0
        
        for i, z in enumerate(z_vals):
            r_local = get_radio_local(z / 100)  # convertir a cm
            for j, theta in enumerate(theta_vals):
                x = r_local * np.cos(theta)
                y = r_local * np.sin(theta)
                
                vertices.append([x, y, z])
                vertex_indices[(i, j)] = idx
                idx += 1
        
        # Generar caras (triángulos)
        for i in range(num_segments - 1):
            for j in range(num_radial):
                v1 = vertex_indices[(i, j)]
                v2 = vertex_indices[(i, (j + 1) % num_radial)]
                v3 = vertex_indices[(i + 1, j)]
                v4 = vertex_indices[(i + 1, (j + 1) % num_radial)]
                
                # Dos triángulos por cuadrilátero
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
        
        self.vertices = vertices
        self.faces = faces
        self.geometrias['arteria'] = {
            'vertices': vertices,
            'faces': faces
        }
        
        return vertices, faces
    
    def crear_particulas_sangre(self, num_particulas=100, radio_mm=1.5, 
                                longitud_cm=10, porcentaje_placa=30):
        """
        Crea puntos que representan eritrocitos/partículas de sangre
        
        Args:
            num_particulas: Número de partículas
            radio_mm: Radio de la arteria
            longitud_cm: Longitud de la arteria
            porcentaje_placa: Porcentaje de estenosis
        """
        particulas = []
        
        z_vals = np.random.uniform(-longitud_cm/2, longitud_cm/2, num_particulas)
        
        def get_radio_local(z):
            factor_forma = np.exp(-(z**2) / (0.05 * (longitud_cm/100)**2))
            r = radio_mm * (1 - (porcentaje_placa / 100.0) * factor_forma)
            return max(r, 0.05)
        
        for z in z_vals:
            r_local = get_radio_local(z / 100)
            theta = np.random.uniform(0, 2*np.pi)
            rho = np.random.uniform(0, 0.9)
            
            x = rho * r_local * np.cos(theta)
            y = rho * r_local * np.sin(theta)
            
            particulas.append([x, y, z])
        
        self.geometrias['sangre'] = {'particulas': particulas}
        return particulas
    
    def crear_placa_aterosclerótica(self, radio_mm=1.5, longitud_cm=10,
                                     porcentaje_placa=30, num_segments=100, num_radial=50):
        """
        Crea geometría solo de la placa aterosclerótica
        """
        vertices = []
        faces = []
        
        z_vals = np.linspace(-longitud_cm/2, longitud_cm/2, num_segments)
        theta_vals = np.linspace(0, 2*np.pi, num_radial, endpoint=False)
        
        def get_radios(z):
            factor_forma = np.exp(-(z**2) / (0.05 * (longitud_cm/100)**2))
            r_exterior = radio_mm
            r_placa = radio_mm * (porcentaje_placa / 100.0) * factor_forma
            r_interior = r_exterior - r_placa
            return r_interior, r_exterior
        
        idx = 0
        vertex_indices = {}
        
        for i, z in enumerate(z_vals):
            r_interior, r_exterior = get_radios(z / 100)
            
            for j, theta in enumerate(theta_vals):
                # Vértice exterior (placa)
                x_ext = r_exterior * np.cos(theta)
                y_ext = r_exterior * np.sin(theta)
                vertices.append([x_ext, y_ext, z])
                vertex_indices[(i, j, 'ext')] = idx
                idx += 1
                
                # Vértice interior
                x_int = r_interior * np.cos(theta)
                y_int = r_interior * np.sin(theta)
                vertices.append([x_int, y_int, z])
                vertex_indices[(i, j, 'int')] = idx
                idx += 1
        
        # Caras de la placa (capa anular)
        for i in range(num_segments - 1):
            for j in range(num_radial):
                j_next = (j + 1) % num_radial
                
                # Cara exterior
                v1 = vertex_indices[(i, j, 'ext')]
                v2 = vertex_indices[(i, j_next, 'ext')]
                v3 = vertex_indices[(i+1, j, 'ext')]
                v4 = vertex_indices[(i+1, j_next, 'ext')]
                
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
                
                # Cara interior
                v1 = vertex_indices[(i, j, 'int')]
                v2 = vertex_indices[(i, j_next, 'int')]
                v3 = vertex_indices[(i+1, j, 'int')]
                v4 = vertex_indices[(i+1, j_next, 'int')]
                
                faces.append([v1, v3, v2])  # Invertir orientación
                faces.append([v2, v3, v4])
        
        self.geometrias['placa'] = {
            'vertices': vertices,
            'faces': faces
        }
        
        return vertices, faces
    
    def exportar_dae(self, incluir_arteria=True, incluir_placa=True, 
                     incluir_sangre=True):
        """
        Exporta toda la geometría a formato DAE (Collada XML)
        
        Args:
            incluir_arteria: Incluir malla de la arteria
            incluir_placa: Incluir placa aterosclerótica
            incluir_sangre: Incluir partículas de sangre
        """
        
        # Crear geometría si no existe
        if incluir_arteria and 'arteria' not in self.geometrias:
            self.crear_cilindro_ocluido()
        
        if incluir_placa and 'placa' not in self.geometrias:
            self.crear_placa_aterosclerótica()
        
        if incluir_sangre and 'sangre' not in self.geometrias:
            self.crear_particulas_sangre()
        
        # Encabezado XML de Collada
        dae_content = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2026-05-01T00:00:00</created>
    <modified>2026-05-01T00:00:00</modified>
    <unit meter="0.001" name="millimeter"/>
    <up_axis>Z_UP</up_axis>
  </asset>

  <library_effects>
    <effect id="RedEffect">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse>
              <color>0.8 0.0 0.0 1.0</color>
            </diffuse>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="OrangeEffect">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse>
              <color>1.0 0.65 0.0 1.0</color>
            </diffuse>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="BlueEffect">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse>
              <color>0.0 0.4 1.0 0.3</color>
            </diffuse>
            <transparency>
              <float>0.7</float>
            </transparency>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>

  <library_materials>
    <material id="RedMaterial" name="Red">
      <instance_effect url="#RedEffect"/>
    </material>
    <material id="OrangeMaterial" name="Orange">
      <instance_effect url="#OrangeEffect"/>
    </material>
    <material id="BlueMaterial" name="Blue">
      <instance_effect url="#BlueEffect"/>
    </material>
  </library_materials>

  <library_geometries>
"""
        
        # Agregar geometría de arteria
        if incluir_arteria and 'arteria' in self.geometrias:
            dae_content += self._generar_geometry_xml(
                'arteria', 
                self.geometrias['arteria']['vertices'],
                self.geometrias['arteria']['faces'],
                'BlueMaterial'
            )
        
        # Agregar geometría de placa
        if incluir_placa and 'placa' in self.geometrias:
            dae_content += self._generar_geometry_xml(
                'placa',
                self.geometrias['placa']['vertices'],
                self.geometrias['placa']['faces'],
                'OrangeMaterial'
            )
        
        dae_content += """
  </library_geometries>

  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
"""
        
        # Agregar nodos
        if incluir_arteria:
            dae_content += """      <node id="Arteria" name="Arteria">
        <instance_geometry url="#arteria-geometry"/>
      </node>
"""
        
        if incluir_placa:
            dae_content += """      <node id="Placa" name="Placa">
        <instance_geometry url="#placa-geometry"/>
      </node>
"""
        
        dae_content += """    </visual_scene>
  </library_visual_scenes>

  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>
"""
        
        # Escribir archivo
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(dae_content)
        
        print(f"✓ Archivo DAE exportado: {self.output_path}")
    
    def _generar_geometry_xml(self, name, vertices, faces, material):
        """Genera XML para una geometría"""
        
        # Convertir a string
        vertex_str = ' '.join([f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in vertices])
        indices_str = ' '.join([str(idx) for face in faces for idx in face])
        
        xml = f"""    <geometry id="{name}-geometry" name="{name}">
      <mesh>
        <source id="{name}-positions">
          <float_array id="{name}-positions-array" count="{len(vertices)*3}">
{vertex_str}
          </float_array>
          <technique_common>
            <accessor source="#{name}-positions-array" count="{len(vertices)}" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="{name}-vertices">
          <input semantic="POSITION" source="#{name}-positions"/>
        </vertices>
        <triangles count="{len(faces)}" material="{material}">
          <input semantic="VERTEX" source="#{name}-vertices" offset="0"/>
          <p>
{indices_str}
          </p>
        </triangles>
      </mesh>
    </geometry>
"""
        return xml
    
    def exportar_obj(self, nombre_archivo=None):
        """Exporta a formato OBJ (alternativa a DAE)"""
        if nombre_archivo is None:
            nombre_archivo = self.output_path.with_suffix('.obj')
        
        with open(nombre_archivo, 'w') as f:
            # Vértices
            for v in self.vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            
            # Caras
            for face in self.faces:
                # OBJ usa índices 1-basados
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        
        print(f"✓ Archivo OBJ exportado: {nombre_archivo}")


# Ejemplo de uso
if __name__ == "__main__":
    print("=" * 60)
    print("GENERADOR DE GEOMETRÍA ARTERIAL - FORMATO DAE/OBJ")
    print("=" * 60)
    
    # Crear generador
    generador = GeneradorDAE("arteria_aterosclerótica.dae")
    
    # Crear geometría
    print("\n📐 Creando geometría...")
    generador.crear_cilindro_ocluido(radio_mm=0.09, longitud_cm=10, 
                                     porcentaje_placa=55)
    print("  ✓ Arteria con oclusión gaussiana")
    
    generador.crear_placa_aterosclerótica(radio_mm=0.09, longitud_cm=10,
                                          porcentaje_placa=55)
    print("  ✓ Placa aterosclerótica")
    
    generador.crear_particulas_sangre(num_particulas=200, radio_mm=0.09,
                                     longitud_cm=10, porcentaje_placa=55)
    print("  ✓ Partículas de sangre")
    
    # Exportar
    print("\n💾 Exportando archivos...")
    generador.exportar_dae(incluir_arteria=True, incluir_placa=True, 
                          incluir_sangre=False)
    generador.exportar_obj()
    
    print("\n✅ Proceso completado")
    print("  Archivos generados:")
    print(f"    - {generador.output_path}")
    print(f"    - {generador.output_path.with_suffix('.obj')}")

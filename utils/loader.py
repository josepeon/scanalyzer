# utils/loader.py
import open3d as o3d

def load_3d_model(file_path):
    try:
        mesh = o3d.io.read_triangle_mesh(file_path)
        if not mesh.has_triangles():
            raise ValueError("File loaded but contains no triangles.")
        return mesh
    except Exception as e:
        print(f"Error loading 3D file: {e}")
        return None
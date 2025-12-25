"""3D model loading utilities using Open3D."""

import open3d as o3d


def load_3d_model(file_path):
    """
    Load a 3D mesh from file.
    
    Args:
        file_path: Path to a .ply, .obj, or .stl file.
        
    Returns:
        Open3D TriangleMesh object, or None if loading fails.
    """
    try:
        mesh = o3d.io.read_triangle_mesh(file_path)
        if not mesh.has_triangles():
            raise ValueError("File loaded but contains no triangles.")
        return mesh
    except Exception as e:
        print(f"Error loading 3D file: {e}")
        return None

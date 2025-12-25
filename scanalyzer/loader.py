"""3D model loading utilities."""

from pathlib import Path
from typing import Optional

import open3d as o3d

SUPPORTED_FORMATS = {".ply", ".obj", ".stl", ".off", ".gltf", ".glb"}


def load_3d_model(file_path: str) -> Optional[o3d.geometry.TriangleMesh]:
    """
    Load a 3D mesh from file.

    Args:
        file_path: Path to a supported 3D file (.ply, .obj, .stl, .off, .gltf, .glb).

    Returns:
        Open3D TriangleMesh object, or None if loading fails.

    Raises:
        ValueError: If file format is unsupported or mesh has no triangles.
    """
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return None

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"Error: Unsupported format '{path.suffix}'. Supported: {SUPPORTED_FORMATS}")
        return None

    try:
        mesh = o3d.io.read_triangle_mesh(str(path))

        if not mesh.has_triangles():
            print(f"Error: File contains no triangles: {file_path}")
            return None

        # Ensure normals are computed for downstream operations
        if not mesh.has_vertex_normals():
            mesh.compute_vertex_normals()

        return mesh

    except Exception as e:
        print(f"Error loading 3D file: {e}")
        return None


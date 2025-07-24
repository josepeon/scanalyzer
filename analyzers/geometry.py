# analyzers/geometry.py
import numpy as np
import open3d as o3d

def analyze_mesh(mesh):
    mesh.compute_vertex_normals()
    mesh.compute_triangle_normals()
    bbox = mesh.get_axis_aligned_bounding_box()

    # Check watertight
    is_watertight = mesh.is_watertight()

    # Convex hull volume (always defined)
    hull, _ = mesh.compute_convex_hull()
    convex_hull_volume = hull.get_volume()

    return {
        "vertices": len(np.asarray(mesh.vertices)),
        "triangles": len(np.asarray(mesh.triangles)),
        "surface_area": mesh.get_surface_area(),
        "volume": mesh.get_volume() if is_watertight else None,
        "convex_hull_volume": convex_hull_volume,
        "watertight": is_watertight,
        "bounding_box": {
            "min_bound": bbox.get_min_bound().tolist(),
            "max_bound": bbox.get_max_bound().tolist()
        }
    }
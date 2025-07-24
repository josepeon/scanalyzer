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

    # Get non-manifold edge count BEFORE overriding triangle array
    non_manifold_edges = mesh.get_non_manifold_edges()
    non_manifold_edge_count = len(non_manifold_edges)

    # Compute average edge length
    triangles = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)

    edge_lengths = []
    for t in triangles:
        v0, v1, v2 = vertices[t[0]], vertices[t[1]], vertices[t[2]]
        edge_lengths.append(np.linalg.norm(v0 - v1))
        edge_lengths.append(np.linalg.norm(v1 - v2))
        edge_lengths.append(np.linalg.norm(v2 - v0))

    average_edge_length = float(np.mean(edge_lengths))

    # Compute triangle aspect ratios
    triangles = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)

    def triangle_aspect_ratio(v0, v1, v2):
        a = np.linalg.norm(v0 - v1)
        b = np.linalg.norm(v1 - v2)
        c = np.linalg.norm(v2 - v0)
        s = (a + b + c) / 2
        area = max(np.sqrt(max(s * (s - a) * (s - b) * (s - c), 0)), 1e-12)
        inradius = 2 * area / (a + b + c)
        circumradius = (a * b * c) / (4 * area)
        return circumradius / inradius

    aspect_ratios = [
        triangle_aspect_ratio(vertices[t[0]], vertices[t[1]], vertices[t[2]])
        for t in triangles
    ]
    average_aspect_ratio = float(np.mean(aspect_ratios))

    # Estimate curvature using vertex neighbor distances (approximation)
    curvatures = []
    mesh.compute_adjacency_list()

    if hasattr(mesh, 'adjacency_list') and mesh.adjacency_list is not None:
        adj = mesh.adjacency_list
        vertices = np.asarray(mesh.vertices)

        for vidx, neighbors in enumerate(adj):
            v = vertices[vidx]
            neighbor_pts = np.array([vertices[n] for n in neighbors])
            if len(neighbor_pts) == 0:
                continue
            dists = np.linalg.norm(neighbor_pts - v, axis=1)
            curvatures.append(np.mean(dists))

        curvatures = np.array(curvatures)
        average_curvature = float(np.mean(curvatures)) if len(curvatures) > 0 else 0.0
        max_curvature = float(np.max(curvatures)) if len(curvatures) > 0 else 0.0
        min_curvature = float(np.min(curvatures)) if len(curvatures) > 0 else 0.0
    else:
        average_curvature = max_curvature = min_curvature = 0.0

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
        },
        "average_edge_length": average_edge_length,
        "average_triangle_aspect_ratio": average_aspect_ratio,
        "non_manifold_edge_count": non_manifold_edge_count,
        "average_curvature": average_curvature,
        "max_curvature": max_curvature,
        "min_curvature": min_curvature,
    }
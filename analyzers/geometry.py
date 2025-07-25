# analyzers/geometry.py
import numpy as np
import open3d as o3d
import json
import os
import datetime

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

    # Euler characteristic
    V = len(np.asarray(mesh.vertices))
    # Estimate E (number of unique edges) from triangle indices
    edges_set = set()
    for triangle in triangles:
        i, j, k = triangle
        edges_set.update({tuple(sorted((i, j))), tuple(sorted((j, k))), tuple(sorted((k, i)))})
    E = len(edges_set)
    F = len(np.asarray(mesh.triangles))
    euler_characteristic = V - E + F

    # Genus estimate
    genus_estimate = (2 - euler_characteristic) // 2 if is_watertight else None

    # Connected components
    triangle_clusters, cluster_n_triangles, cluster_area = mesh.cluster_connected_triangles()
    connected_components = len(cluster_n_triangles)

    # Sharp edge count (approximate by angle between adjacent triangle normals)
    triangle_normals = np.asarray(mesh.triangle_normals)
    sharp_edge_count = 0
    angle_threshold = np.deg2rad(30.0)

    edge_to_triangles = {}
    for tidx, tri in enumerate(triangles):
        edges = [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]
        for i, j in edges:
            key = tuple(sorted((i, j)))
            edge_to_triangles.setdefault(key, []).append(tidx)

    for tri_ids in edge_to_triangles.values():
        if len(tri_ids) == 2:
            n1 = triangle_normals[tri_ids[0]]
            n2 = triangle_normals[tri_ids[1]]
            angle = np.arccos(np.clip(np.dot(n1, n2), -1.0, 1.0))
            if angle > angle_threshold:
                sharp_edge_count += 1

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
        "euler_characteristic": euler_characteristic,
        "genus_estimate": genus_estimate,
        "connected_components": connected_components,
        "sharp_edge_count": sharp_edge_count,
    }

def log_analysis_results(analysis, mesh_name="unnamed_mesh", simplification_level=None, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{mesh_name}_analysis_{timestamp}.json"

    log_data = {
        "mesh_name": mesh_name,
        "timestamp": timestamp,
        "simplification_level": simplification_level,
        "analysis": analysis,
    }

    with open(os.path.join(log_dir, filename), "w") as f:
        json.dump(log_data, f, indent=4)
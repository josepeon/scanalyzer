"""Mesh geometry analysis functions."""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import open3d as o3d


def analyze_mesh(
    mesh: o3d.geometry.TriangleMesh,
    skip_watertight_threshold: int = 100000,
) -> Dict[str, Any]:
    """
    Analyze a 3D mesh and compute geometric properties.

    Args:
        mesh: Open3D TriangleMesh object.
        skip_watertight_threshold: Skip slow watertight check for meshes with
            more triangles than this value (default: 100000).

    Returns:
        Dictionary containing mesh analysis metrics including:
        - vertices, triangles: mesh counts
        - surface_area, volume: geometric measurements
        - watertight: topology check (None if skipped)
        - curvature stats: min, average, max
        - quality metrics: edge length, aspect ratio
    """
    mesh.compute_vertex_normals()
    mesh.compute_triangle_normals()

    triangles = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)
    num_vertices = len(vertices)
    num_triangles = len(triangles)

    # Basic properties
    bbox = mesh.get_axis_aligned_bounding_box()
    
    # Watertight check is very slow on large meshes (O(n^2) in Open3D)
    if num_triangles > skip_watertight_threshold:
        is_watertight = None  # Skip for performance
    else:
        is_watertight = mesh.is_watertight()

    # Convex hull
    hull, _ = mesh.compute_convex_hull()
    convex_hull_volume = hull.get_volume()

    # Non-manifold edges
    non_manifold_edge_count = len(mesh.get_non_manifold_edges())

    # Vectorized edge and aspect ratio computation
    v0, v1, v2 = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]

    a = np.linalg.norm(v0 - v1, axis=1)
    b = np.linalg.norm(v1 - v2, axis=1)
    c = np.linalg.norm(v2 - v0, axis=1)

    average_edge_length = float(np.mean(np.concatenate([a, b, c])))

    # Aspect ratio: circumradius / inradius
    s = (a + b + c) / 2
    area = np.sqrt(np.maximum(s * (s - a) * (s - b) * (s - c), 0))
    area = np.maximum(area, 1e-12)
    aspect_ratios = (a * b * c) / (8 * area * area / (a + b + c))
    average_aspect_ratio = float(np.mean(aspect_ratios))

    # Curvature estimation via neighbor distances
    curvature_stats = _compute_curvature(mesh, vertices)

    # Euler characteristic: V - E + F
    edges = set()
    for tri in triangles:
        i, j, k = tri
        edges.update({
            (min(i, j), max(i, j)),
            (min(j, k), max(j, k)),
            (min(k, i), max(k, i))
        })
    euler_characteristic = num_vertices - len(edges) + num_triangles
    genus_estimate = (2 - euler_characteristic) // 2 if is_watertight else None

    # Connected components
    _, cluster_counts, _ = mesh.cluster_connected_triangles()
    connected_components = len(cluster_counts)

    # Sharp edges
    sharp_edge_count = _count_sharp_edges(mesh, triangles)

    # Volume only available for watertight meshes
    volume = None
    if is_watertight is True:
        volume = mesh.get_volume()

    return {
        "vertices": num_vertices,
        "triangles": num_triangles,
        "surface_area": mesh.get_surface_area(),
        "volume": volume,
        "convex_hull_volume": convex_hull_volume,
        "watertight": is_watertight,
        "bounding_box": {
            "min_bound": bbox.get_min_bound().tolist(),
            "max_bound": bbox.get_max_bound().tolist()
        },
        "average_edge_length": average_edge_length,
        "average_triangle_aspect_ratio": average_aspect_ratio,
        "non_manifold_edge_count": non_manifold_edge_count,
        "min_curvature": curvature_stats["min"],
        "average_curvature": curvature_stats["average"],
        "max_curvature": curvature_stats["max"],
        "euler_characteristic": euler_characteristic,
        "genus_estimate": genus_estimate,
        "connected_components": connected_components,
        "sharp_edge_count": sharp_edge_count,
    }


def _compute_curvature(
    mesh: o3d.geometry.TriangleMesh, vertices: np.ndarray
) -> Dict[str, float]:
    """Estimate curvature via mean neighbor distance per vertex."""
    mesh.compute_adjacency_list()

    if not hasattr(mesh, "adjacency_list") or mesh.adjacency_list is None:
        return {"min": 0.0, "average": 0.0, "max": 0.0}

    curvatures = []
    for vidx, neighbors in enumerate(mesh.adjacency_list):
        if not neighbors:
            continue
        neighbor_pts = vertices[list(neighbors)]
        dists = np.linalg.norm(neighbor_pts - vertices[vidx], axis=1)
        curvatures.append(np.mean(dists))

    if not curvatures:
        return {"min": 0.0, "average": 0.0, "max": 0.0}

    curvatures = np.array(curvatures)
    return {
        "min": float(np.min(curvatures)),
        "average": float(np.mean(curvatures)),
        "max": float(np.max(curvatures)),
    }


def _count_sharp_edges(
    mesh: o3d.geometry.TriangleMesh,
    triangles: np.ndarray,
    angle_threshold_deg: float = 30.0,
) -> int:
    """Count edges where adjacent triangle normals differ by more than threshold."""
    triangle_normals = np.asarray(mesh.triangle_normals)
    angle_threshold = np.deg2rad(angle_threshold_deg)

    # Build edge to triangle mapping
    edge_to_tris: Dict[tuple, list] = {}
    for tidx, tri in enumerate(triangles):
        for i, j in [(0, 1), (1, 2), (2, 0)]:
            key = (min(tri[i], tri[j]), max(tri[i], tri[j]))
            edge_to_tris.setdefault(key, []).append(tidx)

    sharp_count = 0
    for tri_ids in edge_to_tris.values():
        if len(tri_ids) == 2:
            dot = np.clip(np.dot(triangle_normals[tri_ids[0]], triangle_normals[tri_ids[1]]), -1.0, 1.0)
            if np.arccos(dot) > angle_threshold:
                sharp_count += 1

    return sharp_count


def log_analysis_results(
    analysis: Dict[str, Any],
    mesh_name: str = "unnamed_mesh",
    simplification_level: Optional[str] = None,
    log_dir: str = "logs",
) -> str:
    """
    Save analysis results to a JSON log file.

    Args:
        analysis: Dictionary of analysis results.
        mesh_name: Name identifier for the mesh.
        simplification_level: Optional simplification level applied.
        log_dir: Directory to save log files.

    Returns:
        Path to the saved log file.
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{mesh_name}_analysis_{timestamp}.json"
    filepath = os.path.join(log_dir, filename)

    log_data = {
        "mesh_name": mesh_name,
        "timestamp": timestamp,
        "simplification_level": simplification_level,
        "analysis": analysis,
    }

    with open(filepath, "w") as f:
        json.dump(log_data, f, indent=2)

    return filepath

"""Scanalyzer - Streamlit Web Application for 3D Mesh Analysis."""

import json
import os
import tempfile
from pathlib import Path

import joblib
import numpy as np
import open3d as o3d
import plotly.graph_objects as go
import streamlit as st
import trimesh

from scanalyzer import analyze_mesh, load_3d_model

# --- Page Configuration ---
st.set_page_config(page_title="Scanalyzer", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #ffffff;
    color: #1d1d1f;
}
.stApp {
    padding: 1rem 2rem;
    max-width: none;
    margin: 0;
}
.st-expander, .stFileUploader, .stDataFrame, .stJson, .stPlotlyChart {
    backdrop-filter: blur(10px);
    background-color: rgba(255, 255, 255, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
}
.stButton>button, .stDownloadButton>button {
    backdrop-filter: blur(6px);
    background-color: rgba(0, 122, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: white;
    border-radius: 8px;
    height: 2.4rem;
    padding: 0 1.5rem;
    font-weight: 500;
}
.stPlotlyChart {
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "mesh": None,
        "analysis": None,
        "file_path": None,
        "file_name": None,
        "suggested_level": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# --- Helper Functions ---
def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temp location and return path."""
    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def compute_approx_thickness(mesh) -> float:
    """Compute approximate thickness from bounding box."""
    try:
        bbox = mesh.get_axis_aligned_bounding_box()
        min_bound = np.asarray(bbox.get_min_bound())
        max_bound = np.asarray(bbox.get_max_bound())
        return float(np.min(max_bound - min_bound))
    except Exception:
        return 0.0


def get_ml_suggestion(analysis: dict) -> str | None:
    """Get ML-based simplification suggestion."""
    model_path = "model/simplification_model.pkl"
    if not os.path.exists(model_path):
        return None

    try:
        model = joblib.load(model_path)
        feature_order = [
            "vertices", "triangles", "surface_area", "volume", "watertight",
            "average_edge_length", "average_triangle_aspect_ratio", "min_curvature",
            "average_curvature", "max_curvature", "connected_components", "approx_thickness"
        ]

        def safe_get(key):
            val = analysis.get(key, 0.0)
            if val is None:
                return 0.0
            if isinstance(val, bool):
                return int(val)
            return val

        features = [[safe_get(k) for k in feature_order]]
        prediction = model.predict(features)[0]
        label_map = {0: "Aggressive", 1: "Mild", 2: "Medium"}
        return label_map.get(prediction, "Mild")
    except Exception:
        return None


def render_mesh_viewer(mesh):
    """Render 3D mesh viewer using Plotly."""
    vertices_np = np.asarray(mesh.vertices)
    triangles_np = np.asarray(mesh.triangles)

    # Simplify for display if too large
    if len(triangles_np) > 100000:
        display_mesh = mesh.simplify_quadric_decimation(50000)
        vertices_np = np.asarray(display_mesh.vertices)
        triangles_np = np.asarray(display_mesh.triangles)

    fig = go.Figure(data=[go.Mesh3d(
        x=vertices_np[:, 0],
        y=vertices_np[:, 1],
        z=vertices_np[:, 2],
        i=triangles_np[:, 0],
        j=triangles_np[:, 1],
        k=triangles_np[:, 2],
        color='gray',
        opacity=1.0,
        lighting=dict(ambient=0.18, diffuse=1, fresnel=0.1, specular=0.3, roughness=0.7),
        lightposition=dict(x=100, y=200, z=0)
    )])
    fig.update_layout(
        scene=dict(aspectmode='data'),
        margin=dict(r=0, l=0, b=0, t=0),
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)


def process_mesh(file_path: str, file_name: str):
    """Load and analyze mesh, update session state."""
    with st.spinner(f"Loading {file_name}..."):
        mesh = load_3d_model(file_path)

    if mesh is None or len(mesh.vertices) == 0:
        st.error("Failed to load mesh. Please try another file.")
        return False

    with st.spinner("Analyzing mesh..."):
        analysis = analyze_mesh(mesh)
        analysis["approx_thickness"] = compute_approx_thickness(mesh)

    # Update session state
    st.session_state.mesh = mesh
    st.session_state.analysis = analysis
    st.session_state.file_path = file_path
    st.session_state.file_name = file_name
    st.session_state.suggested_level = get_ml_suggestion(analysis)

    return True


def display_analysis_summary(analysis: dict):
    """Display mesh analysis summary."""
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**Mesh Structure**")
        st.markdown(f"- **Vertices**: {analysis.get('vertices', 0):,}")
        st.markdown(f"- **Triangles**: {analysis.get('triangles', 0):,}")
        st.markdown(f"- **Surface Area**: {analysis.get('surface_area', 0):.4f}")
        volume = analysis.get('volume')
        st.markdown(f"- **Volume**: {volume:.4f}" if volume else "- **Volume**: N/A")
        st.markdown(f"- **Approx. Thickness**: {analysis.get('approx_thickness', 0):.4f}")

    with cols[1]:
        st.markdown("**Topology & Quality**")
        watertight = analysis.get('watertight')
        wt_str = "Yes" if watertight is True else ("No" if watertight is False else "Skipped")
        st.markdown(f"- **Watertight**: {wt_str}")
        st.markdown(f"- **Avg. Edge Length**: {analysis.get('average_edge_length', 0):.4f}")
        st.markdown(f"- **Aspect Ratio**: {analysis.get('average_triangle_aspect_ratio', 0):.2f}")
        st.markdown(f"- **Connected Components**: {analysis.get('connected_components', 0)}")
        st.markdown(f"- **Curvature (min/avg/max)**: {analysis.get('min_curvature', 0):.4f} / {analysis.get('average_curvature', 0):.4f} / {analysis.get('max_curvature', 0):.4f}")


def display_charts(analysis: dict):
    """Display analysis charts."""
    tabs = st.tabs(["Curvature", "Geometry"])

    with tabs[0]:
        fig = go.Figure(data=[go.Bar(
            x=["Min", "Average", "Max"],
            y=[analysis["min_curvature"], analysis["average_curvature"], analysis["max_curvature"]],
            marker_color=['#4CAF50', '#2196F3', '#FF5722']
        )])
        fig.update_layout(title="Curvature Distribution", height=300)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        fig = go.Figure(data=[go.Bar(
            x=["Vertices", "Triangles", "Sharp Edges"],
            y=[analysis["vertices"], analysis["triangles"], analysis.get("sharp_edge_count", 0)],
            marker_color=['#9C27B0', '#00BCD4', '#FFC107']
        )])
        fig.update_layout(title="Geometry Overview", height=300)
        st.plotly_chart(fig, use_container_width=True)


def simplify_mesh(mesh, level: str):
    """Simplify mesh based on level."""
    factors = {"Mild": 0.75, "Medium": 0.5, "Aggressive": 0.25}
    factor = factors.get(level, 0.5)

    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()

    target = max(100, int(len(mesh.triangles) * factor))
    simplified = mesh.simplify_quadric_decimation(target)
    simplified.compute_vertex_normals()

    return simplified


# --- Main Application ---
st.title("Scanalyzer")
st.caption("Upload, Analyze & Simplify 3D Meshes")

col_left, col_right = st.columns([1, 1])

# --- Left Column: Upload & Analysis ---
with col_left:
    with st.expander("Upload Mesh File", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a 3D file",
            type=["ply", "obj", "stl", "off", "gltf", "glb"],
            help="Supported formats: PLY, OBJ, STL, OFF, GLTF, GLB"
        )

        # Example file
        if Path("examples/bunny.ply").exists():
            if st.button("Try: bunny.ply", use_container_width=True):
                process_mesh("examples/bunny.ply", "bunny.ply")

    # Process uploaded file
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.file_name != uploaded_file.name:
            file_path = save_uploaded_file(uploaded_file)
            process_mesh(file_path, uploaded_file.name)

    # Display analysis if available
    if st.session_state.analysis is not None:
        st.markdown("---")

        with st.expander("Analysis Summary", expanded=True):
            display_analysis_summary(st.session_state.analysis)

        with st.expander("Charts"):
            display_charts(st.session_state.analysis)

        # Simplification controls
        st.markdown("---")
        st.subheader("Mesh Simplification")

        if st.session_state.suggested_level:
            st.info(f"ML Suggestion: **{st.session_state.suggested_level}**")

        options = ["Mild", "Medium", "Aggressive"]
        default_idx = options.index(st.session_state.suggested_level) if st.session_state.suggested_level in options else 0
        level = st.selectbox(
            "Simplification Level",
            options,
            index=default_idx
        )

        if st.button("Simplify Mesh", type="primary"):
            with st.spinner("Simplifying..."):
                simplified = simplify_mesh(st.session_state.mesh, level)
                new_analysis = analyze_mesh(simplified)
                new_analysis["approx_thickness"] = compute_approx_thickness(simplified)

                st.session_state.mesh = simplified
                st.session_state.analysis = new_analysis
                st.session_state.suggested_level = get_ml_suggestion(new_analysis)

            st.success(f"Simplified from {st.session_state.analysis.get('triangles', 0):,} to {new_analysis['triangles']:,} triangles")
            st.rerun()

        # Download
        st.download_button(
            "Download Analysis (JSON)",
            data=json.dumps(st.session_state.analysis, indent=2),
            file_name="scanalyzer_report.json",
            mime="application/json"
        )

# --- Right Column: 3D Viewer ---
with col_right:
    if st.session_state.mesh is not None:
        st.subheader("3D Preview")
        render_mesh_viewer(st.session_state.mesh)
    else:
        st.info("Upload a mesh file to see the 3D preview")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85rem;'>"
    "Built by Jose Peon | <a href='https://github.com/josepeon/scanalyzer'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True
)

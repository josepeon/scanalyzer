import streamlit as st
import tempfile
import os
from pathlib import Path
from io import BytesIO
from utils.loader import load_3d_model
from analyzers.geometry import analyze_mesh
import numpy as np
import plotly.graph_objects as go
import trimesh
import open3d as o3d
import csv
import joblib

# Initialize session state for mesh, tmp_path, and analysis
if 'mesh' not in st.session_state:
    st.session_state.mesh = None
if 'tmp_path' not in st.session_state:
    st.session_state.tmp_path = None
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

# --- Mesh Viewer Rendering Function ---
def render_mesh_viewer():
    mesh = st.session_state.mesh
    MAX_DISPLAY_TRIANGLES = 100000
    vertices_np = np.asarray(mesh.vertices)
    triangles_np = np.asarray(mesh.triangles)

    if len(triangles_np) > MAX_DISPLAY_TRIANGLES:
        simplified_mesh = mesh.simplify_quadric_decimation(MAX_DISPLAY_TRIANGLES)
        vertices_np = np.asarray(simplified_mesh.vertices)
        triangles_np = np.asarray(simplified_mesh.triangles)

    if len(triangles_np) > 100000:
        simplified_mesh = mesh.simplify_quadric_decimation(50000)
        vertices_np = np.asarray(simplified_mesh.vertices)
        triangles_np = np.asarray(simplified_mesh.triangles)

    trimesh_obj = trimesh.Trimesh(vertices=vertices_np, faces=triangles_np)

    extension = st.session_state.tmp_path.split(".")[-1] if st.session_state.tmp_path else "ply"
    glb_path = st.session_state.tmp_path.replace("." + extension, ".glb")
    try:
        trimesh_obj.export(glb_path)
        if not os.path.exists(glb_path):
            st.error("Failed to export mesh to GLB.")
            return
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
            autosize=True,
            width=None,
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred while rendering the 3D preview: {e}")

st.set_page_config(page_title="Scanalyzer", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #ffffff;
        color: #1d1d1f;
    }
    .stApp {
        padding: 1rem 2rem;
        max-width: none;
        margin: 0;
    }
    /* Glassmorphism for main containers */
    .st-expander, .stFileUploader, .stDataFrame, .stJson, .stPlotlyChart {
        backdrop-filter: blur(10px);
        background-color: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        color: #0a0a0a;
    }
    /* Glassmorphism for buttons */
    .stButton>button, .stDownloadButton>button {
        backdrop-filter: blur(6px);
        background-color: rgba(0, 122, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.25);
        color: #0a0a0a;
        border-radius: 8px;
        height: 2.4rem;
        padding: 0 1.5rem;
        font-weight: 500;
    }
    .stPlotlyChart {
        padding: 0 !important;
    }
    .st-expanderHeader {
        font-weight: 600;
        font-size: 17px;
    }
    /* Glassmorphism for 3D preview container */
    .element-container:has(.stPlotlyChart) {
        backdrop-filter: blur(12px);
        background-color: rgba(240, 240, 240, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    /* Prevent I-beam text cursor on feature tooltips */
    span[title] {
        cursor: default;
    }
    /* Custom tooltip icon style */
    span[title]::before {
        content: "?";
        display: inline-block;
        width: 1.1em;
        height: 1.1em;
        line-height: 1.1em;
        font-size: 0.8em;
        text-align: center;
        border-radius: 50%;
        background-color: #e0e0e0;
        color: #000;
        margin-left: 0.3em;
        margin-right: 0.2em;
        font-weight: bold;
    }
    span[title] {
        color: transparent;
    }
    </style>
""", unsafe_allow_html=True)
st.title("Scanalyzer: Upload, Analyze & Simplify 3D Meshes")

col_left, col_right = st.columns([1, 1])

with col_left:
    with st.expander("Upload Mesh File (.ply, .obj, .stl)"):
        col1, col2 = st.columns([3,1])
        with col1:
            uploaded_file = st.file_uploader("Upload a 3D file (.ply, .obj, .stl)", type=["ply", "obj", "stl"])
            # Add example bunny.ply button inside the expander
            if Path("examples/bunny.ply").is_file():
                if st.button("Try with Example: bunny.ply"):
                    with open("examples/bunny.ply", "rb") as f:
                        data = f.read()
                        uploaded_file = BytesIO(data)
                        uploaded_file.name = "bunny.ply"
                        uploaded_file.seek(0)
                    # Simulate saving the file temporarily as in a real upload
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".ply") as tmp:
                        tmp.write(data)
                        st.session_state.tmp_path = tmp.name
        with col2:
            if uploaded_file is not None:
                st.success("File uploaded. Processing...")
            else:
                st.write("")

if 'uploaded_file' not in locals():
    uploaded_file = None

# Accept either uploaded file or example button
if uploaded_file is not None or ('tmp_path' in locals() and tmp_path is not None):
    if uploaded_file is not None and (not hasattr(uploaded_file, "read") or uploaded_file.name == "bunny.ply"):
        # This is the bunny.ply dummy file, use the examples path
        if not ('tmp_path' in locals() and tmp_path is not None):
            tmp_path = "examples/bunny.ply"
    elif uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

    print("Trying to load mesh from:", tmp_path)
    print(f"Mesh loaded from: {tmp_path}")
    print(f"File exists? {os.path.exists(tmp_path)}")
    print(f"File size: {os.path.getsize(tmp_path)} bytes")
    try:
        st.session_state.mesh = load_3d_model(tmp_path)
        st.session_state.tmp_path = tmp_path
    except Exception as e:
        st.warning(f"Mesh failed to load: {e}")
        st.session_state.mesh = None
    print("Mesh loaded?", st.session_state.mesh is not None)
    if st.session_state.mesh:
        print("Vertices:", len(st.session_state.mesh.vertices))
        print("Triangles:", len(st.session_state.mesh.triangles))
    if st.session_state.mesh is None or len(st.session_state.mesh.vertices) == 0 or len(st.session_state.mesh.triangles) == 0:
        st.warning("Model could not be loaded or contains no geometry. Please try another mesh.")
    else:
        with st.spinner("Analyzing mesh..."):
            try:
                st.session_state.analysis = analyze_mesh(st.session_state.mesh)
                from analyzers.geometry import log_analysis_results
                from os.path import basename
                mesh_name = basename(st.session_state.tmp_path).split('.')[0]
                log_analysis_results(st.session_state.analysis, mesh_name)
            except RuntimeError as e:
                st.warning("Analysis warning: " + str(e))
                st.session_state.analysis = {
                    "vertices": len(st.session_state.mesh.vertices),
                    "triangles": len(st.session_state.mesh.triangles),
                    "surface_area": st.session_state.mesh.get_surface_area() if st.session_state.mesh.get_surface_area() is not None else 0.0,
                    "volume": st.session_state.mesh.get_volume() if st.session_state.mesh.is_watertight() else 0.0,
                    "watertight": st.session_state.mesh.is_watertight(),
                    "average_edge_length": 0.0,
                    "average_triangle_aspect_ratio": 0.0,
                    "connected_components": 0,
                    "min_curvature": 0.0,
                    "average_curvature": 0.0,
                    "max_curvature": 0.0
                }

        try:
            bounds = st.session_state.mesh.bounds
            min_dim = np.min(bounds[1] - bounds[0])
            st.session_state.analysis["approx_thickness"] = float(min_dim)
        except:
            st.session_state.analysis["approx_thickness"] = 0.0

        # ML-based suggestion for simplification level
        suggested_level = None
        model_path = "model/simplification_model.pkl"

        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                feature_order = [
                    "average_edge_length", "min_curvature", "average_triangle_aspect_ratio",
                    "average_curvature", "surface_area", "volume", "connected_components",
                    "triangles", "max_curvature", "vertices", "approx_thickness", "watertight"
                ]
                features = [[st.session_state.analysis.get(k, 0.0) for k in feature_order]]
                suggested_level = model.predict(features)[0]
            except Exception as e:
                st.warning(f"Model prediction failed: {e}")

        with col_left:
            st.markdown("---")

            with st.expander("Mesh Analysis Summary"):
                analysis = st.session_state.analysis
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**Mesh Structure**")
                    st.markdown(f"- **Vertices** <span title='Points in 3D space used to define the geometry of the mesh'>❓</span>: {analysis.get('vertices', 0)}", unsafe_allow_html=True)
                    st.markdown(f"- **Triangles** <span title='Mesh faces composed of three vertices each, defining the surface'>❓</span>: {analysis.get('triangles', 0)}", unsafe_allow_html=True)
                    st.markdown(f"- **Surface Area** <span title='Total area covered by all triangles on the mesh surface'>❓</span>: {analysis.get('surface_area') or 0.0:.2f}", unsafe_allow_html=True)
                    st.markdown(f"- **Volume** <span title='3D space enclosed by the mesh; only available if watertight'>❓</span>: {analysis.get('volume') or 0.0:.2f}", unsafe_allow_html=True)
                    st.markdown(f"- **Approx. Thickness** <span title='Smallest bounding box side; useful to gauge wall or part thinness'>❓</span>: {analysis.get('approx_thickness', 0.0):.2f}", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown("**Topology & Quality**")
                    st.markdown(f"- **Watertight** <span title='True if the mesh forms a sealed, manifold shape without holes'>❓</span>: {analysis.get('watertight', False)}", unsafe_allow_html=True)
                    st.markdown(f"- **Avg. Edge Length** <span title='Average distance between connected vertex pairs in the mesh'>❓</span>: {analysis.get('average_edge_length', 0.0):.3f}", unsafe_allow_html=True)
                    st.markdown(f"- **Aspect Ratio** <span title='Quality measure of triangle shapes; ideal triangles have low ratios'>❓</span>: {analysis.get('average_triangle_aspect_ratio', 0.0):.2f}", unsafe_allow_html=True)
                    st.markdown(f"- **Connected Components** <span title='Counts how many isolated pieces the mesh is made of'>❓</span>: {analysis.get('connected_components', 0)}", unsafe_allow_html=True)
                    st.markdown(f"- **Curvature (min/avg/max)** <span title='Statistical description of how curved the surface is'>❓</span>: {analysis.get('min_curvature', 0.0):.3f} / {analysis.get('average_curvature', 0.0):.3f} / {analysis.get('max_curvature', 0.0):.3f}", unsafe_allow_html=True)

        with col_right:
            if st.session_state.mesh:
                render_mesh_viewer()


        with col_left:
            st.markdown("---")

            with st.expander("📊 Mesh Insights"):
                analysis = st.session_state.analysis
                tabs = st.tabs(["Curvature", "Geometry", "Analysis Table"])
                with tabs[0]:
                    fig_curvature = go.Figure(data=[
                        go.Bar(name="Curvature", x=["Min", "Average", "Max"], y=[
                            analysis["min_curvature"],
                            analysis["average_curvature"],
                            analysis["max_curvature"]
                        ])
                    ])
                    fig_curvature.update_layout(title="Curvature Overview", plot_bgcolor='white', paper_bgcolor='white')
                    st.plotly_chart(fig_curvature)

                with tabs[1]:
                    fig_geometry = go.Figure(data=[
                        go.Bar(name="Geometry", x=["Vertices", "Triangles", "Sharp Edges", "Approx. Thickness"], y=[
                            analysis["vertices"],
                            analysis["triangles"],
                            analysis["sharp_edge_count"],
                            analysis.get("approx_thickness", 0.0)
                        ])
                    ])
                    fig_geometry.update_layout(title="Basic Geometry Overview", plot_bgcolor='white', paper_bgcolor='white')
                    st.plotly_chart(fig_geometry)

                with tabs[2]:
                    simplified_table = {
                        "Vertices": analysis["vertices"],
                        "Triangles": analysis["triangles"],
                        "Surface Area": analysis["surface_area"],
                        "Volume": analysis["volume"],
                        "Watertight": analysis["watertight"],
                        "Average Edge Length": analysis["average_edge_length"],
                        "Avg Triangle Aspect Ratio": analysis["average_triangle_aspect_ratio"],
                        "Connected Components": analysis["connected_components"]
                    }
                    st.dataframe(simplified_table, use_container_width=False, width=500, height=300)

            # Mesh simplification controls
            simpl_col1, simpl_col2 = st.columns([3,1])
            with simpl_col1:
                # Updated ML suggestion logic for simplification level
                if suggested_level:
                    st.info(f"Suggested simplification level: **{suggested_level}** (based on mesh features)")
                    use_suggestion = st.checkbox("Use ML suggestion", value=False)
                else:
                    use_suggestion = False

                if use_suggestion and suggested_level:
                    level = suggested_level
                else:
                    level = st.selectbox(
                        "Select Mesh Simplification Level",
                        ["Mild", "Medium", "Aggressive"],
                        key="simplify_level_unique",
                        index=0,
                        disabled=False
                    )
            with simpl_col2:
                pass


            # Move the button after the selectbox for visual hierarchy
            if st.button("Run Mesh Simplification", key="simplify_button_unique", disabled=False):
                # Use session state for mesh, analysis, tmp_path
                mesh = st.session_state.mesh
                analysis = st.session_state.analysis
                tmp_path = st.session_state.tmp_path

                if level == "Mild":
                    factor = 0.75
                elif level == "Medium":
                    factor = 0.5
                else:
                    factor = 0.25

                # Step 1: Remove duplicated vertices and degenerate triangles
                mesh.remove_duplicated_vertices()
                mesh.remove_degenerate_triangles()

                # Step 2: Simplify mesh using quadric decimation
                target_triangles = max(100, int(len(mesh.triangles) * factor))
                mesh = mesh.simplify_quadric_decimation(target_triangles)

                # Step 3: Recompute normals
                mesh.compute_vertex_normals()

                st.success(f"{level} simplification applied.")

                # Store repaired mesh as trimesh for export
                repaired_trimesh_obj = trimesh.Trimesh(
                    vertices=np.asarray(mesh.vertices),
                    faces=np.asarray(mesh.triangles)
                )

                # Re-run analysis
                try:
                    analysis = analyze_mesh(mesh)
                    from analyzers.geometry import log_analysis_results
                    from os.path import basename
                    mesh_name = basename(tmp_path).split('.')[0]
                    log_analysis_results(analysis, mesh_name)
                except RuntimeError as e:
                    st.warning("Analysis warning: " + str(e))
                    analysis = {
                        "vertices": len(mesh.vertices),
                        "triangles": len(mesh.triangles),
                        "surface_area": mesh.get_surface_area() if mesh.get_surface_area() is not None else 0.0,
                        "volume": mesh.get_volume() if mesh.is_watertight() else 0.0,
                        "watertight": mesh.is_watertight(),
                        "average_edge_length": 0.0,
                        "average_triangle_aspect_ratio": 0.0,
                        "connected_components": 0,
                        "min_curvature": 0.0,
                        "average_curvature": 0.0,
                        "max_curvature": 0.0
                    }
                try:
                    bounds = mesh.bounds
                    min_dim = np.min(bounds[1] - bounds[0])
                    analysis["approx_thickness"] = float(min_dim)
                except:
                    analysis["approx_thickness"] = 0.0

                # Save back to session state for persistence
                st.session_state.mesh = mesh
                st.session_state.analysis = analysis

                # --- Render mesh viewer with updated mesh ---
                render_mesh_viewer()

                # Log mesh simplification results to CSV
                csv_path = "data/simplification_logs.csv"
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                fieldnames = [
                    "mesh_name", "vertices", "triangles", "surface_area", "volume", "watertight",
                    "average_edge_length", "average_triangle_aspect_ratio", "min_curvature",
                    "average_curvature", "max_curvature", "connected_components",
                    "approx_thickness", "simplification_level"
                ]
                row = {
                    "mesh_name": mesh_name,
                    "vertices": analysis["vertices"],
                    "triangles": analysis["triangles"],
                    "surface_area": analysis["surface_area"],
                    "volume": analysis["volume"],
                    "watertight": int(analysis["watertight"]),
                    "average_edge_length": analysis["average_edge_length"],
                    "average_triangle_aspect_ratio": analysis["average_triangle_aspect_ratio"],
                    "min_curvature": analysis["min_curvature"],
                    "average_curvature": analysis["average_curvature"],
                    "max_curvature": analysis["max_curvature"],
                    "connected_components": analysis["connected_components"],
                    "approx_thickness": analysis["approx_thickness"],
                    "simplification_level": level
                }
                write_header = not os.path.exists(csv_path)
                with open(csv_path, mode="a", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    if write_header:
                        writer.writeheader()
                    writer.writerow(row)

            # Download button block moved below mesh simplification controls
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.download_button(
                label="Download Report as JSON",
                data=__import__('json').dumps(st.session_state.analysis, indent=2),
                file_name="scanalyzer_report.json",
                mime="application/json"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; font-size: 0.85rem; color: gray;'>"
            "Built by Jose Peon · © 2025<br>"
            "<a href='https://github.com/josepeon' target='_blank' style='color: gray; text-decoration: underline;'>github.com/josepeon</a>"
            "</div>",
            unsafe_allow_html=True
        )

        # Cleanup
        print(f"Temp path: {st.session_state.tmp_path}")
        if 'glb_path' in locals() and os.path.exists(glb_path):
            print(f"GLB path: {glb_path}")
            print(f"GLB exists? {os.path.exists(glb_path)}")
            import shutil
            shutil.copy(glb_path, os.path.expanduser("~/Desktop/debug_model.glb"))
        else:
            print("No GLB file was created; skipping debug export.")

        if st.session_state.tmp_path and os.path.exists(st.session_state.tmp_path) and "examples" not in st.session_state.tmp_path:
            os.remove(st.session_state.tmp_path)
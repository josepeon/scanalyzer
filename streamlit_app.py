import streamlit as st
import tempfile
import os
from utils.loader import load_3d_model
from analyzers.geometry import analyze_mesh
import open3d as o3d
import numpy as np
import plotly.graph_objects as go
import trimesh, base64

# Helper function for analysis explanations
def get_help_text(key):
    explanations = {
        "vertices": "Number of unique points in the mesh.",
        "triangles": "Number of triangular faces formed by vertices.",
        "surface_area": "Total area of the mesh surface.",
        "volume": "Enclosed volume of the mesh if it's watertight.",
        "watertight": "Indicates whether the mesh is completely sealed.",
        "average_edge_length": "Mean length of all edges in the mesh.",
        "average_triangle_aspect_ratio": "Average ratio indicating triangle shape quality.",
        "connected_components": "Number of disconnected mesh parts.",
        "min_curvature": "Smallest curvature value found on the surface.",
        "average_curvature": "Mean curvature of all surface points.",
        "max_curvature": "Largest curvature value found on the surface.",
        "sharp_edge_count": "Number of edges with angles considered sharp."
    }
    return explanations.get(key, "")

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
    .st-expander, .stFileUploader, .stDataFrame, .stJson, .stPlotlyChart {
        border: 1px solid #dcdcdc;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        background-color: #ffffff;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #007aff;
        color: white;
        border-radius: 8px;
        height: 2.4rem;
        padding: 0 1.5rem;
        font-weight: 500;
        border: none;
    }
    .stPlotlyChart {
        padding: 0 !important;
    }
    .st-expanderHeader {
        font-weight: 600;
        font-size: 17px;
    }
    </style>
""", unsafe_allow_html=True)
st.title("Scanalyzer: 3D Mesh Analyzer")

col_left, col_right = st.columns([1, 2])

with col_left:
    with st.expander("📁 Upload 3D File"):
        col1, col2 = st.columns([3,1])
        with col1:
            uploaded_file = st.file_uploader("Upload a 3D file (.ply, .obj, .stl)", type=["ply", "obj", "stl"])
        with col2:
            if uploaded_file is not None:
                st.success("File uploaded. Processing...")
            else:
                st.write("")

if 'uploaded_file' not in locals():
    uploaded_file = None

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    mesh = load_3d_model(tmp_path)
    if mesh is None:
        with col_left:
            st.error("Failed to load the 3D model.")
    else:
        with st.spinner("Analyzing mesh..."):
            analysis = analyze_mesh(mesh)

        with col_left:
            st.markdown("---")

            with st.expander("📝 Analysis Report"):
                for key, value in analysis.items():
                    st.markdown(f"**{key}**: {value}", help=get_help_text(key))

        with col_right:
            st.subheader("Mesh Preview")
            vertices = np.asarray(mesh.vertices)
            triangles = np.asarray(mesh.triangles)

            if len(vertices) == 0 or len(triangles) == 0:
                st.warning("No mesh data to display.")
            else:
                # Export mesh to GLB using trimesh with error handling
                trimesh_obj = trimesh.Trimesh(vertices=vertices, faces=triangles)
                glb_path = tmp_path.replace("." + uploaded_file.name.split(".")[-1], ".glb")
                try:
                    export_result = trimesh_obj.export(glb_path)
                    if not os.path.exists(glb_path):
                        st.error("Failed to export mesh to GLB.")
                    else:
                        # Previous simpler fallback: display mesh using Open3D visualization link or plotly mesh3d
                        # Here we provide a basic Plotly mesh3d visualization as a fallback
                        fig = go.Figure(data=[go.Mesh3d(
                            x=vertices[:,0],
                            y=vertices[:,1],
                            z=vertices[:,2],
                            i=triangles[:,0],
                            j=triangles[:,1],
                            k=triangles[:,2],
                            color='lightblue',
                            opacity=0.50
                        )])
                        fig.update_layout(scene=dict(aspectmode='data'), margin=dict(r=0,l=0,b=0,t=0))
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"An error occurred while rendering the 3D preview: {e}")

        with col_left:
            st.markdown("---")

            with st.expander("📊 Curvature Overview"):
                fig_curvature = go.Figure(data=[
                    go.Bar(name="Curvature", x=["Min", "Average", "Max"], y=[
                        analysis["min_curvature"],
                        analysis["average_curvature"],
                        analysis["max_curvature"]
                    ])
                ])
                fig_curvature.update_layout(title="Curvature Overview", plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig_curvature)

            st.markdown("---")

            with st.expander("📐 Basic Geometry Overview"):
                fig_geometry = go.Figure(data=[
                    go.Bar(name="Geometry", x=["Vertices", "Triangles", "Sharp Edges"], y=[
                        analysis["vertices"],
                        analysis["triangles"],
                        analysis["sharp_edge_count"]
                    ])
                ])
                fig_geometry.update_layout(title="Basic Geometry Overview", plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig_geometry)

            st.markdown("---")

            with st.expander("📋 Analysis Report Table"):
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
                st.dataframe(simplified_table, use_container_width=True)

            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.download_button(
                label="Download Report as JSON",
                data=__import__('json').dumps(analysis, indent=2),
                file_name="scanalyzer_report.json",
                mime="application/json"
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # Cleanup
    print(f"Temp path: {tmp_path}")
    print(f"GLB path: {glb_path}")
    print(f"GLB exists? {os.path.exists(glb_path)}")
    import shutil
    shutil.copy(glb_path, os.path.expanduser("~/Desktop/debug_model.glb"))
    os.remove(tmp_path)
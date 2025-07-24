import streamlit as st
import tempfile
import os
from utils.loader import load_3d_model
from analyzers.geometry import analyze_mesh
import open3d as o3d
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Scanalyzer", layout="wide")
st.title("Scanalyzer: 3D Mesh Analyzer")

uploaded_file = st.file_uploader("Upload a 3D file (.ply, .obj, .stl)", type=["ply", "obj", "stl"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.success("File uploaded. Processing...")

    mesh = load_3d_model(tmp_path)
    if mesh is None:
        st.error("Failed to load the 3D model.")
    else:
        analysis = analyze_mesh(mesh)
        st.subheader("Analysis Report")
        st.json(analysis)

        import json
        st.download_button(
            label="Download Report as JSON",
            data=json.dumps(analysis, indent=2),
            file_name="scanalyzer_report.json",
            mime="application/json"
        )

        # Optional 3D preview using Plotly
        st.subheader("Mesh Preview")
        vertices = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)

        if len(vertices) == 0 or len(triangles) == 0:
            st.warning("No mesh data to display.")
        else:
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            i, j, k = triangles[:, 0], triangles[:, 1], triangles[:, 2]

            fig = go.Figure(data=[
                go.Mesh3d(
                    x=x, y=y, z=z,
                    i=i, j=j, k=k,
                    color='lightgray',
                    opacity=1.0,
                    name='Mesh'
                )
            ])
            fig.update_layout(
                scene=dict(aspectmode="data"),
                margin=dict(l=0, r=0, t=0, b=0)
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Mesh Property Summary Charts")

            # Bar chart for curvature values
            fig_curvature = go.Figure(data=[
                go.Bar(name="Curvature", x=["Min", "Average", "Max"], y=[
                    analysis["min_curvature"],
                    analysis["average_curvature"],
                    analysis["max_curvature"]
                ])
            ])
            fig_curvature.update_layout(title="Curvature Overview")
            st.plotly_chart(fig_curvature)

            # Bar chart for basic geometry metrics
            fig_geometry = go.Figure(data=[
                go.Bar(name="Geometry", x=["Vertices", "Triangles", "Sharp Edges"], y=[
                    analysis["vertices"],
                    analysis["triangles"],
                    analysis["sharp_edge_count"]
                ])
            ])
            fig_geometry.update_layout(title="Basic Geometry Overview")
            st.plotly_chart(fig_geometry)

            # Display mesh properties as a table
            st.markdown("### Analysis Report Table")
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
            st.table(simplified_table)

    # Cleanup
    os.remove(tmp_path)
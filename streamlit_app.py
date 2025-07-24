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

        # Optional 3D preview using Plotly
        st.subheader("Mesh Preview")
        vertices = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)

        if len(vertices) == 0 or len(triangles) == 0:
            st.warning("No mesh data to display.")
        else:
            x, y, z = vertices[:,0], vertices[:,1], vertices[:,2]
            i, j, k = triangles[:,0], triangles[:,1], triangles[:,2]

            fig = go.Figure(data=[
                go.Mesh3d(
                    x=x, y=y, z=z,
                    i=i, j=j, k=k,
                    opacity=1.0,
                    color='gray',
                    name='Mesh'
                )
            ])
            fig.update_layout(
                scene=dict(aspectmode="data"),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    # Cleanup
    os.remove(tmp_path)
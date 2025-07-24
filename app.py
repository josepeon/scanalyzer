# app.py
import sys
from utils.loader import load_3d_model
from analyzers.geometry import analyze_mesh

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <path_to_3d_file>")
        sys.exit(1)

    mesh = load_3d_model(sys.argv[1])
    if mesh is None:
        sys.exit(1)

    analysis = analyze_mesh(mesh)
    print("\n=== Scanalyzer Report ===")
    for key, value in analysis.items():
        print(f"{key}: {value}")
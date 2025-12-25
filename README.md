# Scanalyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://scanalyzer.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A web-based tool for 3D mesh inspection, simplification, and analysis. Upload meshes to analyze geometry features, curvature, thickness, and receive ML-powered simplification recommendations.

**Live demo:** [scanalyzer.streamlit.app](https://scanalyzer.streamlit.app)

## Features

- Interactive 3D mesh viewer
- Geometry analysis: surface area, volume, edge lengths, triangle quality
- Curvature and thickness estimation
- ML-powered simplification level suggestions
- Mesh decimation with Mild, Medium, and Aggressive options
- Example meshes for quick testing

## Installation

### From source

```bash
git clone https://github.com/josepeon/scanalyzer.git
cd scanalyzer
pip install -e ".[web]"
```

### Run locally

```bash
streamlit run streamlit_app.py
```

## Project Structure

```
scanalyzer/
├── app.py                 # Command-line interface
├── streamlit_app.py       # Web application
├── scanalyzer/            # Core library
│   ├── __init__.py
│   ├── analyzer.py        # Mesh analysis functions
│   ├── loader.py          # 3D model loading
│   └── cli.py             # CLI entry point
├── model/
│   └── simplification_model.pkl
├── data/
│   └── simplification_logs.csv
├── notebooks/
│   └── train_model.ipynb
└── examples/
    └── bunny.ply
```

## Deployment

### Docker

```bash
docker build -t scanalyzer .
docker run -p 8501:8501 scanalyzer
```

### Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and deploy from your fork
4. Set main file path to `streamlit_app.py`

### Other platforms

The included `Dockerfile` works with Railway, Render, Fly.io, and similar platforms.

## ML Pipeline

The simplification suggester uses an XGBoost classifier trained on mesh features. To retrain:

1. Run simplifications through the web app to generate training data
2. Open `notebooks/train_model.ipynb`
3. Run all cells to train and export a new model

## Tech Stack

- Streamlit - Web interface
- Open3D - Mesh processing
- Trimesh - Mesh export
- XGBoost - ML predictions
- Plotly - 3D visualization

## License

MIT License - see [LICENSE](LICENSE) for details.
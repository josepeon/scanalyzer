# Scanalyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://scanalyzer.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**🚀 [Try it live → scanalyzer.streamlit.app](https://scanalyzer.streamlit.app)**

Scanalyzer is a web-based tool for 3D mesh inspection, simplification, and analysis. Upload meshes to analyze geometry features, curvature, thickness, and receive ML-powered simplification recommendations.

![Scanalyzer Demo](./assets/demo.gif)

---

## Features

- Interactive 3D mesh viewer
- Geometry analysis: surface area, volume, edge lengths, triangle quality
- Curvature and thickness estimation
- ML-powered simplification level suggestions
- Mesh decimation with Mild, Medium, and Aggressive options
- Example meshes for quick testing

---

## Quickstart

```bash
# Clone the repository
git clone https://github.com/josepeon/scanalyzer.git
cd scanalyzer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run streamlit_app.py
```

---

## Project Structure

```
scanalyzer/
├── app.py                 # Command-line interface
├── streamlit_app.py       # Web application (Streamlit)
├── requirements.txt       # Python dependencies
├── scanalyzer/            # Core library
│   ├── __init__.py
│   ├── analyzer.py        # Mesh analysis functions
│   └── loader.py          # 3D model loading
├── model/
│   └── simplification_model.pkl
├── data/
│   └── simplification_logs.csv
├── notebooks/
│   └── train_model.ipynb  # ML model training
├── examples/
│   ├── bunny.ply
│   └── armadillo.ply
└── assets/
    └── demo.gif
```

---

## ML Pipeline

The simplification suggester uses an XGBoost classifier trained on mesh features. To retrain:

1. Run simplifications through the web app to generate training data in `data/simplification_logs.csv`
2. Open `notebooks/train_model.ipynb`
3. Run all cells to train and export a new model

---

## Installation

### From PyPI (when published)

```bash
pip install scanalyzer

# With web UI support
pip install scanalyzer[web]

# With development tools
pip install scanalyzer[all]
```

### From source

```bash
git clone https://github.com/josepeon/scanalyzer.git
cd scanalyzer
pip install -e ".[all]"
```

---

## Deployment

### 🐳 Docker

```bash
# Build image
docker build -t scanalyzer .

# Run container
docker run -p 8501:8501 scanalyzer

# Open http://localhost:8501
```

### ☁️ Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy from your fork
5. Set main file path to `streamlit_app.py`

### 🚀 Railway / Render / Fly.io

Use the included `Dockerfile` for one-click deployment:

```bash
# Railway
railway up

# Render - connect repo, select Docker environment

# Fly.io
fly launch
fly deploy
```

---

## Tech Stack

- Streamlit - Web interface
- Open3D - Mesh processing
- Trimesh - Mesh export and utilities
- XGBoost / scikit-learn - ML predictions
- Plotly - 3D visualization

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built by Jose Peon
https://github.com/josepeon
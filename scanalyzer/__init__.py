"""
Scanalyzer - 3D mesh analysis and simplification toolkit.

A Python library for analyzing 3D mesh geometry, computing quality metrics,
and providing ML-powered simplification recommendations.
"""

from .analyzer import analyze_mesh, log_analysis_results
from .loader import load_3d_model, SUPPORTED_FORMATS

__all__ = [
    "load_3d_model",
    "analyze_mesh",
    "log_analysis_results",
    "SUPPORTED_FORMATS",
]
__version__ = "1.0.0"

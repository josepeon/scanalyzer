"""
CLI entry point for scanalyzer package.

This module provides the main() function for the `scanalyzer` console script
defined in pyproject.toml.
"""

import sys
from pathlib import Path


def main() -> int:
    """Run the scanalyzer CLI."""
    # Add parent directory to path if running as package
    app_path = Path(__file__).parent.parent / "app.py"
    
    if app_path.exists():
        # Import and run the app module
        import runpy
        sys.argv[0] = str(app_path)
        runpy.run_path(str(app_path), run_name="__main__")
        return 0
    else:
        # Fallback: run analysis directly
        import argparse
        from . import load_3d_model, analyze_mesh
        
        parser = argparse.ArgumentParser(
            description="Scanalyzer - 3D mesh analysis toolkit"
        )
        parser.add_argument("file", help="Path to 3D model file")
        parser.add_argument("--json", action="store_true", help="Output as JSON")
        args = parser.parse_args()
        
        mesh = load_3d_model(args.file)
        results = analyze_mesh(mesh)
        
        if args.json:
            import json
            print(json.dumps(results, indent=2))
        else:
            for key, value in results.items():
                print(f"{key}: {value}")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())

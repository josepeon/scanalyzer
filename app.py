#!/usr/bin/env python3
"""Command-line interface for Scanalyzer mesh analysis."""

import argparse
import json
import sys

from scanalyzer import __version__, analyze_mesh, load_3d_model, SUPPORTED_FORMATS


def main():
    parser = argparse.ArgumentParser(
        description="Analyze 3D mesh files and compute geometry metrics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Supported formats: {', '.join(SUPPORTED_FORMATS)}",
    )
    parser.add_argument("file", help="Path to the 3D mesh file")
    parser.add_argument(
        "-o", "--output",
        help="Save analysis to JSON file instead of printing",
        metavar="FILE",
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Scanalyzer {__version__}",
    )

    args = parser.parse_args()

    mesh = load_3d_model(args.file)
    if mesh is None:
        sys.exit(1)

    analysis = analyze_mesh(mesh)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis saved to {args.output}")
    elif args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print("\n=== Scanalyzer Report ===")
        print(f"File: {args.file}\n")
        for key, value in analysis.items():
            if isinstance(value, float):
                print(f"{key}: {value:.6f}")
            elif isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.main import collect_candidates, create_segments, initialize_folders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice fatigue dataset pipeline CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-folders", help="Create dataset folders and metadata files.")
    subparsers.add_parser("collect", help="Collect candidate videos and download audio.")

    segment_parser = subparsers.add_parser("segment", help="Generate fixed-length speech segments.")
    segment_parser.add_argument(
        "--input",
        type=str,
        default="data/candidates/keyword_only",
        help="Input folder containing candidate WAV files.",
    )
    segment_parser.add_argument(
        "--output",
        type=str,
        default="data/segments/unlabelled",
        help="Folder for extracted segment WAV files.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "init-folders":
        initialize_folders()
    elif args.command == "collect":
        collect_candidates()
    elif args.command == "segment":
        create_segments(Path(args.input), Path(args.output))
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()

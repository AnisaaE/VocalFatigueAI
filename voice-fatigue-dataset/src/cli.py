from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.augmentation import generate_augmented_dataset
from src.config import load_config
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

    augment_parser = subparsers.add_parser("augment-tired", help="Create augmented tired WAV files for selected speakers.")
    augment_parser.add_argument(
        "--input",
        type=str,
        default="data/candidates/labels/tired",
        help="Input folder containing tired WAV files grouped by speaker.",
    )
    augment_parser.add_argument(
        "--output",
        type=str,
        default="data/candidates/labels/tired_augmented",
        help="Output folder for generated augmented WAV files.",
    )
    augment_parser.add_argument(
        "--anisa-count",
        type=int,
        default=50,
        help="How many original files to sample from anisa.",
    )
    augment_parser.add_argument(
        "--nalan-count",
        type=int,
        default=50,
        help="How many original files to sample from nalan.",
    )
    augment_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible file selection and augmentation.",
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
    elif args.command == "augment-tired":
        config = load_config()
        total_saved = generate_augmented_dataset(
            input_root=Path(args.input),
            output_root=Path(args.output),
            speaker_counts={"anisa": args.anisa_count, "nalan": args.nalan_count},
            sample_rate=config.get("audio_sample_rate", 16000),
            seed=args.seed,
        )
        logging.getLogger(__name__).info("Created %s augmented tired files", total_saved)
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()

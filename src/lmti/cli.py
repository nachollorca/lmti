"""CLI entry point for lmti."""

import argparse

from lmti.config import Config
from lmti.repl import run


def main():
    """Launch the lmti interactive REPL."""
    config = Config.load()

    parser = argparse.ArgumentParser(
        prog="lmti",
        description="Language Models, from the terminal.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=config.settings.model,
        help=f"provider:model identifier (default: {config.settings.model})",
    )
    args = parser.parse_args()

    # Override config with CLI argument if provided
    if args.model:
        config.settings.model = args.model

    run(config=config)

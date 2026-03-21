"""CLI entry point for lmti."""

import argparse
import os

from lmti.secrets import load_env
from lmti.tui import run


def main():
    """Launch the lmti interactive REPL."""
    load_env()
    default_model = os.environ.get("DEFAULT_MODEL", "mistral:mistral-small-2603")

    parser = argparse.ArgumentParser(
        prog="lmti",
        description="Language Models, from the terminal.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=default_model,
        help=f"provider:model identifier (default: {default_model})",
    )
    args = parser.parse_args()
    run(model=args.model)

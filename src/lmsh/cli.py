"""CLI entry point for lmsh."""

import argparse
import os

from lmsh.secrets import load_env
from lmsh.tui import run


def main():
    """Launch the lmsh interactive REPL."""
    load_env()
    default_model = os.environ.get("DEFAULT_MODEL", "mistral:mistral-small-2603")

    parser = argparse.ArgumentParser(
        prog="lmsh",
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

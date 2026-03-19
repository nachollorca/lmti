"""CLI entry point for lmsh."""

import argparse

from lmsh.tui import run

DEFAULT_MODEL = "mistral:mistral-small-2603"


def main():
    """Launch the lmsh interactive REPL."""
    parser = argparse.ArgumentParser(
        prog="lmsh",
        description="Language Models, from the terminal.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"provider:model identifier (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()
    run(model=args.model)

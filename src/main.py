"""Project entry point; delegates to the `mid` command-line interface."""

import sys

from mid.cli import main

if __name__ == "__main__":
    sys.exit(main())

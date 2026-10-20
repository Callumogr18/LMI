"""Allow `python -m mid` to run the CLI."""

import sys

from mid.cli import main

sys.exit(main())

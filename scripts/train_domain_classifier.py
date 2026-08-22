from __future__ import annotations

import sys

from train_classifier import main

if __name__ == "__main__":
    if "--task" not in sys.argv:
        sys.argv.extend(["--task", "domain"])
    main()

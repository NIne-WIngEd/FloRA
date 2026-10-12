"""Observe the original connected setup; this is never qualification."""
from __future__ import annotations

import faulthandler
import sys


def observe(action, *, interval_seconds=120):
    # Keep the timer's stderr descriptor open for its entire lifetime.
    trace_output = sys.stderr
    faulthandler.dump_traceback_later(
        interval_seconds, repeat=True, file=trace_output, exit=False)
    try:
        return action()
    finally:
        faulthandler.cancel_dump_traceback_later()


def main():
    from run_connected_functional_comparison import main as strict_main

    print("Diagnostic setup observation only: repeated stacks every 120 seconds; "
          "no functional or latency qualification.", file=sys.stderr, flush=True)
    return observe(strict_main)


if __name__ == "__main__":
    sys.exit(main())

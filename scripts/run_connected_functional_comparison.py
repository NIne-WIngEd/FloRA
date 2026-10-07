"""Run only the reviewed connected case, with strict discovery and verdicts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
import unittest

from run_selected_integration_shard import LiveIntegrationResult, cases


def validate_discovery(discovered, expected):
    identities = tuple(test.id() for test in discovered)
    if not expected or len(set(expected)) != len(expected):
        raise ValueError('reviewed test identities must be nonempty and unique')
    if not identities or len(set(identities)) != len(identities):
        raise ValueError('connected discovery must be nonempty and unique')
    if set(identities) != set(expected):
        raise ValueError('connected discovery differs from reviewed test identities')
    if any(isinstance(test, unittest.loader._FailedTest) for test in discovered):
        raise ValueError('connected test import failed')
    return identities


def qualified_result(result, expected):
    return (result.testsRun == len(expected) and result.wasSuccessful()
            and not result.skipped and not result.expectedFailures
            and not result.unexpectedSuccesses)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-test-id', action='append', required=True)
    parser.add_argument('--select-test-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'tests'))
    sys.path.insert(0, str(root / 'tests/integration'))
    started = time.monotonic()
    receipt = {'schema': 'flora-connected-functional-test-result-v1',
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'expected_test_ids': arguments.expected_test_id,
        'selected_test_id': arguments.select_test_id,
        'latency_qualification': False, 'physical_functional_pass': False}
    try:
        loader = unittest.TestLoader()
        discovered = list(cases(loader.discover(
            str(root / 'tests/integration'), pattern='test_selected_connected_functional_comparison.py')))
        receipt['discovered_test_ids'] = [test.id() for test in discovered]
        for original_error in loader.errors:
            print(original_error, file=sys.stderr, flush=True)
        receipt['import_errors'] = len(loader.errors)
        validate_discovery(discovered, arguments.expected_test_id)
        selected = [test for test in discovered if test.id() == arguments.select_test_id]
        if len(selected) != 1:
            raise ValueError('selected job must match exactly one reviewed test')
        result = unittest.TextTestRunner(verbosity=2, resultclass=LiveIntegrationResult).run(
            unittest.TestSuite(selected))
        receipt.update(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
            skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
            unexpected_successes=len(result.unexpectedSuccesses),
            physical_functional_pass=qualified_result(result, [arguments.select_test_id]))
    except Exception as error:
        receipt['runner_failure_type'] = type(error).__name__
        receipt['runner_failure_reason'] = 'discovery_or_runner_failure'
        print('Connected case discovery/runner failed; no functional qualification.', file=sys.stderr)
        traceback.print_exc()
    finally:
        receipt['elapsed_seconds'] = time.monotonic() - started
        arguments.output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return 0 if receipt['physical_functional_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())

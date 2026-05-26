"""
regression_framework/run_regression.py
Full Automotive Regression Test Runner

Usage:
    python run_regression.py --suite all --report html
    python run_regression.py --suite bms --parallel

Structure:
    - Discovers tests from test_suites/
    - Runs pytest with HTML report
    - Generates Excel summary per ECU
    - Emails report if configured
    - Exits with non-zero code on failures (for CI/CD integration)
"""
import argparse
import pytest
import sys
import os
import yaml
import subprocess
from datetime import datetime
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / 'config' / 'regression_config.yaml'


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {
        'suites': {
            'bms': ['test_suites/bms_suite.py'],
            'charging': ['test_suites/charging_suite.py'],
            'network': ['test_suites/network_suite.py'],
            'uds': ['test_suites/uds_suite.py'],
            'all': ['test_suites/'],
        },
        'report_dir': 'reports/',
        'markers': {
            'smoke': '-m smoke',
            'regression': '-m regression',
            'safety': '-m safety',
        }
    }


def build_pytest_args(suite: str, config: dict, report_path: str,
                      verbose: bool = False, parallel: bool = False,
                      markers: str = None) -> list:
    """Build pytest argument list."""
    suite_paths = config['suites'].get(suite, ['test_suites/'])

    args = list(suite_paths)
    args += [
        f'--html={report_path}',
        '--self-contained-html',
        '--tb=short',
    ]

    if verbose:
        args.append('-v')
    else:
        args.append('-q')

    if parallel:
        # pytest-xdist for parallel execution
        args += ['-n', 'auto']

    if markers:
        args += ['-m', markers]

    # Show test summary
    args += ['-r', 'a']  # Show all test results

    return args


def print_banner(suite: str):
    print("=" * 70)
    print("  EV POWERTRAIN REGRESSION TEST FRAMEWORK")
    print(f"  Suite: {suite.upper()}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='EV Powertrain Regression Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_regression.py --suite all
  python run_regression.py --suite bms --verbose
  python run_regression.py --suite charging --markers smoke
  python run_regression.py --suite all --parallel
        """
    )
    parser.add_argument('--suite',
                        choices=['bms', 'charging', 'network', 'uds', 'all'],
                        default='all',
                        help='Test suite to run')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose test output')
    parser.add_argument('--parallel', '-p', action='store_true',
                        help='Run tests in parallel (requires pytest-xdist)')
    parser.add_argument('--markers', '-m',
                        choices=['smoke', 'regression', 'safety'],
                        help='Run only tests with specific marker')
    parser.add_argument('--report-dir', default=None,
                        help='Override report output directory')
    parser.add_argument('--fail-fast', '-x', action='store_true',
                        help='Stop after first failure')
    args = parser.parse_args()

    config = load_config()
    report_dir = Path(args.report_dir or config.get('report_dir', 'reports/'))
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = report_dir / f"regression_{args.suite}_{timestamp}.html"

    print_banner(args.suite)
    print(f"  Report: {report_path}")
    print()

    pytest_args = build_pytest_args(
        args.suite, config, str(report_path),
        verbose=args.verbose,
        parallel=args.parallel,
        markers=args.markers
    )

    if args.fail_fast:
        pytest_args.append('-x')

    # Print what we're about to run
    print(f"  Command: pytest {' '.join(pytest_args)}")
    print()

    # Run pytest
    exit_code = pytest.main(pytest_args)

    # Print result
    print()
    print("=" * 70)
    if exit_code == 0:
        print("  RESULT: ALL TESTS PASSED")
    elif exit_code == 1:
        print("  RESULT: SOME TESTS FAILED")
    elif exit_code == 2:
        print("  RESULT: TEST EXECUTION ERROR")
    elif exit_code == 5:
        print("  RESULT: NO TESTS COLLECTED (check suite path)")
    print(f"  Report: {report_path}")
    print("=" * 70)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

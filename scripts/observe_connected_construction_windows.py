"""Localize the original connected action with nine bounded journal windows.

The unchanged strict runner remains on its original calling thread. Its raw
result is authoritative. This carrier reuses the original GIL-held frame
sampler and adds only fixed code selectors, window coordination and receipts.
Residency cannot establish call counts, exclusive CPU, learning or causation.
The original external 2700-second process cap remains required.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import threading
import time
from types import FunctionType

from observe_connected_setup_journal import SELECTORS, SetupJournal


ADDITIONAL_SELECTORS = (
    ('lineage.native', 'flora.selected.judgment_lineage', ('NativeJudgmentLineageVerifier', 'context_lineage'), ()),
    ('lineage.preregistered', 'flora.selected.phase_snapshots', ('PreregisteredPhaseCaptureLineageVerifier', 'context_lineage'), ()),
    ('route.construct', 'flora.selected.phase_routes', ('SelectedPhaseRoute', '__init__'), ()),
    ('route.observed_binding', 'flora.selected.phase_routes', ('SelectedPhaseRoute', 'observed_binding'), ()),
    ('context.revalidate', 'flora.selected.context_guard', ('PreparedCurrentContext', 'revalidate'), ()),
    ('prereg.current', 'flora.selected.experiment_preregistration', ('XTDBExperimentPreregistrationCustody', '_current'), ()),
    ('history.metadata', 'flora.selected.history_fence', ('_verify_current_history_metadata',), ()),
)
CONSTRUCTION_SELECTORS = SELECTORS + ADDITIONAL_SELECTORS


class ObservationInfrastructureError(RuntimeError):
    """Observer failure; never a verdict on the original connected action."""


class _WindowJournal(SetupJournal):
    # Nine unchanged samplers together cannot exceed the original byte limit.
    MAXIMUM_JOURNAL_BYTES = SetupJournal.MAXIMUM_JOURNAL_BYTES // 9


def _clean_owner():
    # Inherited __enter__ also checks its coordinator thread. Check the actual
    # action owner here, before its code starts; never install an observer hook.
    monitoring = getattr(sys, 'monitoring', None)
    if (sys.getprofile() is not None or sys.gettrace() is not None
            or threading.getprofile() is not None or threading.gettrace() is not None
            or monitoring is not None and any(monitoring.get_tool(tool) is not None
                for tool in (monitoring.PROFILER_ID, monitoring.DEBUGGER_ID))):
        raise ObservationInfrastructureError('existing observer prevents clean construction measurement')
    gil_enabled = getattr(sys, '_is_gil_enabled', None)
    if gil_enabled is not None and gil_enabled() is not True:
        raise ObservationInfrastructureError('construction journal requires the original GIL-held sampler')


class ConstructionWindows:
    MAXIMUM_MANIFEST_BYTES = 65536
    STARTUP_TIMEOUT_SECONDS = 5
    JOIN_TIMEOUT_SECONDS = 3

    def __init__(self, action, directory, *, window_seconds=300, total_seconds=2700,
                 maximum_windows=9, interval_seconds=1):
        if (type(action) is not FunctionType
                or type(maximum_windows) is not int or not 1 <= maximum_windows <= 9
                or not math.isfinite(window_seconds) or not 0 < window_seconds <= 300
                or not math.isfinite(total_seconds) or not 0 < total_seconds <= 2700
                or not math.isfinite(interval_seconds) or not 0.01 <= interval_seconds <= 1):
            raise ValueError('bounded construction limits and original action required')
        self.action, self.directory = action, Path(directory)
        self.owner_thread = threading.get_ident()
        self.window_seconds, self.total_seconds = window_seconds, total_seconds
        self.maximum_windows, self.interval_seconds = maximum_windows, interval_seconds
        self.manifest_path = self.directory / 'construction-windows.jsonl'
        self._stop, self._ready = threading.Event(), threading.Event()
        self._thread = self._manifest = None
        self._started = None
        self._outcome = 'pending'
        self._errors = self._manifest_bytes = 0
        self.windows = []

    def _write(self, record):
        record.update(schema='flora-connected-construction-windows-v1',
            diagnostic_only=True, functional_qualification=False, latency_qualification=False)
        data = (json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
        if self._manifest_bytes + len(data) > self.MAXIMUM_MANIFEST_BYTES:
            raise ObservationInfrastructureError('bounded construction manifest exhausted')
        self._manifest.write(data)
        self._manifest.flush()
        self._manifest_bytes += len(data)

    def _summary(self, kind):
        elapsed = time.monotonic() - self._started
        time_cap = elapsed >= self.total_seconds
        window_cap = len(self.windows) >= self.maximum_windows
        return dict(kind=kind, outcome=self._outcome, elapsed_seconds=round(elapsed, 6),
            windows=len(self.windows), samples=sum(window.samples for window in self.windows),
            journal_bytes=sum(window.bytes_written for window in self.windows),
            observer_errors=self._errors, time_cap_reached=time_cap,
            window_count_cap_reached=window_cap, observation_cap_reached=time_cap or window_cap,
            coordinator_stopped=kind == 'action_close',
            all_samplers_stopped=all(window._thread is None or not window._thread.is_alive()
                for window in self.windows))

    def start(self):
        _clean_owner()
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            targets = [self.manifest_path, *(self.directory / f'construction-window-{index:02d}.jsonl'
                for index in range(1, self.maximum_windows + 1))]
            if any(path.exists() or path.is_symlink() for path in targets):
                raise ObservationInfrastructureError('construction evidence already exists')
        except OSError:
            raise ObservationInfrastructureError('construction evidence directory unavailable') from None
        self._started = time.monotonic()
        self._thread = threading.Thread(target=self._run, name='flora-construction-windows', daemon=True)
        self._thread.start()
        if not self._ready.wait(self.STARTUP_TIMEOUT_SECONDS):
            self._errors += 1
            self.close('observer_start_failure')
            raise ObservationInfrastructureError('construction observer did not start')
        if self._errors:
            self.close('observer_start_failure')
            raise ObservationInfrastructureError('construction observer startup failed')

    def _run(self):
        try:
            self._manifest = self.manifest_path.open('xb')
            self._write(dict(kind='start', maximum_windows=self.maximum_windows,
                window_cap_seconds=self.window_seconds, global_cap_seconds=self.total_seconds,
                maximum_samples=9 * SetupJournal.MAXIMUM_SAMPLES,
                maximum_journal_bytes=SetupJournal.MAXIMUM_JOURNAL_BYTES,
                maximum_manifest_bytes=self.MAXIMUM_MANIFEST_BYTES,
                selector_count=len(CONSTRUCTION_SELECTORS), inspected_threads=1,
                interpretation='wall_residency_localization_only'))
            for number in range(1, self.maximum_windows + 1):
                remaining = self.total_seconds - (time.monotonic() - self._started)
                if self._stop.is_set() or remaining <= 0:
                    break
                window = _WindowJournal(self.directory / f'construction-window-{number:02d}.jsonl',
                    owner_code=self.action.__code__, owner_thread=self.owner_thread,
                    interval_seconds=self.interval_seconds,
                    cap_seconds=min(self.window_seconds, remaining), selectors=CONSTRUCTION_SELECTORS)
                self.windows.append(window)
                try:
                    window.__enter__()
                    if window.byte_cap_reached or window.observer_errors:
                        raise ObservationInfrastructureError('construction window startup failed')
                    self._write(dict(kind='window_start', window=number,
                        elapsed_seconds=round(time.monotonic() - self._started, 6),
                        cap_seconds=window.cap_seconds))
                    self._ready.set()
                    while window._thread.is_alive() and not self._stop.is_set():
                        remaining = self.total_seconds - (time.monotonic() - self._started)
                        if remaining <= 0:
                            break
                        window._thread.join(timeout=min(0.05, remaining))
                finally:
                    # Existing close owns the sample lock, file flush and join.
                    # Its lock/I/O bound remains the external process cap.
                    window.close(self._outcome if self._stop.is_set() else 'window_limit')
                    self._write(dict(kind='window_close', window=number,
                        elapsed_seconds=round(time.monotonic() - self._started, 6),
                        samples=window.samples, journal_bytes=window.bytes_written,
                        observer_errors=window.observer_errors, byte_cap_reached=window.byte_cap_reached,
                        cap_reached=window.cap_reached, sampler_stopped=not window._thread
                            or not window._thread.is_alive()))
                if window.observer_errors or window.byte_cap_reached or window._thread.is_alive():
                    raise ObservationInfrastructureError('construction window incomplete')
        except BaseException:
            # Fixed counters only: never serialize payloads or exception text.
            self._errors += 1
            self._stop.set()
        finally:
            if self._manifest is not None:
                try:
                    self._write(self._summary('coordinator_close'))
                except BaseException:
                    self._errors += 1
                finally:
                    try:
                        self._manifest.close()
                    except BaseException:
                        self._errors += 1
                    self._manifest = None
            self._ready.set()

    def close(self, outcome):
        self._outcome = outcome
        self._stop.set()
        if self._thread is None:
            return
        self._thread.join(timeout=self.JOIN_TIMEOUT_SECONDS)
        if self._thread.is_alive():
            self._errors += 1
            return
        # Append only after the coordinator has closed its own file. A process
        # timeout still retains its earlier flushed window records.
        if self.manifest_path.exists():
            try:
                with self.manifest_path.open('ab') as stream:
                    self._manifest = stream
                    self._write(self._summary('action_close'))
            except BaseException:
                self._errors += 1
            finally:
                self._manifest = None


def observe(action, *, journal_directory, window_seconds=300, total_seconds=2700,
            maximum_windows=9, interval_seconds=1):
    windows = ConstructionWindows(action, journal_directory, window_seconds=window_seconds,
        total_seconds=total_seconds, maximum_windows=maximum_windows,
        interval_seconds=interval_seconds)
    windows.start()
    try:
        value = action()
    except BaseException as error:
        windows.close('cancel' if isinstance(error, (KeyboardInterrupt, SystemExit)) else 'exception')
        raise
    else:
        windows.close('return')
        if windows._errors:
            raise ObservationInfrastructureError('construction observation infrastructure failed')
        return value


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--journal-directory', type=Path, required=True)
    arguments, original_arguments = parser.parse_known_args()
    from run_connected_functional_comparison import main as strict_main
    sys.argv[:] = [sys.argv[0], *original_arguments]
    print('Diagnostic construction journal windows only; original action and raw verdict remain authoritative; '
          'no functional or latency qualification.', file=sys.stderr, flush=True)
    return observe(strict_main, journal_directory=arguments.journal_directory)


if __name__ == '__main__':
    sys.exit(main())

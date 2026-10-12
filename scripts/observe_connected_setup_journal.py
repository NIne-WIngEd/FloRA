"""Bounded fixed-code setup residency journal; diagnostic evidence only.

A daemon Python thread holds ordinary frame references from sys._current_frames.
Only the original strict runner thread is inspected, and only fixed tags and
numeric line/depth data are persisted. No locals, payloads, permission values,
profile/trace hooks, factory replacements or runtime changes are used. Samples
are wall residency observations, never call counts, exclusive CPU or authority.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import threading
import time
from types import CodeType, FunctionType, ModuleType


# Resolve only already loaded namespaces; the observer never imports FloRA.
# The first observed original code object for each selector is retained.
SELECTORS = (
    ('context.assemble', 'flora.selected.context', ('assemble_context',), ()),
    ('phase.capture', 'flora.selected.phase_snapshots', ('XTDBPhaseSnapshotCustody', 'capture'), ()),
    ('phase.capture_guard', 'flora.selected.phase_snapshots', ('XTDBPhaseSnapshotCustody', 'capture'), ('capture_guard',)),
    ('phase.personal_gate', 'flora.selected.phase_snapshots', ('XTDBPhaseSnapshotCustody', 'capture'), ('personal_gate',)),
    ('phase.slot_capture', 'flora.selected.phase_snapshots', ('XTDBPhaseSnapshotCustody', '_slot_capture'), ()),
    ('phaseprep.enter', 'flora.selected._phase_preparation', ('_PhasePreparation', '_enter'), ()),
    ('phaseprep.owner_map', 'flora.selected._phase_preparation', ('_owner_map',), ()),
    ('phaseprep.port_dictionary', 'flora.selected._phase_preparation', ('_port_dictionary',), ()),
    ('slot.capture', 'flora.selected.experiment_preregistration', ('RegisteredExperimentPreregistration', 'authorize_slot_capture'), ()),
    ('slot.authorize', 'flora.selected.experiment_preregistration', ('XTDBExperimentPreregistrationCustody', '_authorize_slot'), ()),
    ('slot.authorize_body', 'flora.selected.experiment_preregistration', ('XTDBExperimentPreregistrationCustody', '_authorize_slot_body'), ()),
    ('slot.bindings', 'flora.selected.experiment_preregistration', ('_SlotMetadataFrame', 'bindings'), ()),
    ('slot.execute', 'flora.selected.experiment_preregistration', ('_SlotMetadataFrame', 'execute'), ()),
    ('slot.native_readers', 'flora.selected.experiment_preregistration', ('_slot_native_readers',), ()),
    ('kurrent.replay_committed', 'flora.selected.experience', ('KurrentExperienceLog', 'replay_committed'), ()),
    ('kurrent.replay', 'flora.selected.experience', ('KurrentExperienceLog', 'replay'), ()),
    ('kurrent.lookup_committed', 'flora.selected.experience', ('KurrentExperienceLog', 'lookup_committed'), ()),
    ('kurrent.codec_gateway', 'flora.selected.experience', ('_native_codec_gateway',), ()),
    ('context.log_replay', 'flora.selected.selected_context', ('SelectedContextLogView', 'replay'), ()),
    ('xtdb.native_execute', 'flora.selected.native_reads', ('ReadOnlyNativeSQLConnection', 'execute'), ()),
    ('xtdb.bounded_execute', 'flora.selected.bounded_xtdb_reads', ('_BoundedXTDBReadConnection', 'execute'), ()),
    ('xtdb.driver_execute', 'psycopg.connection', ('Connection', 'execute'), ()),
    ('xtdb.cursor_execute', 'psycopg.cursor', ('Cursor', 'execute'), ()),
    ('owner.build', 'registered_functional_case_fixture', ('RegisteredFunctionalCase', 'build'), ()),
)


def loaded_code(module_name, names, nested=()):
    """Read module/class dictionaries, never descriptors or architecture imports."""
    value = sys.modules.get(module_name)
    if type(value) is not ModuleType:
        return None
    for name in names:
        if type(value) is not ModuleType and not isinstance(value, type):
            return None
        value = vars(value).get(name)
    if type(value) in (classmethod, staticmethod):
        value = value.__func__
    if type(value) is not FunctionType:
        return None
    code = value.__code__
    for name in nested:
        matches = [child for child in code.co_consts
                   if type(child) is CodeType and child.co_name == name]
        if len(matches) != 1:
            return None
        code = matches[0]
    return code


class SetupJournal:
    """Finite, flushed records with transient frame references and fixed labels."""

    MAXIMUM_THREADS = 32
    MAXIMUM_DEPTH = 256
    MAXIMUM_SAMPLES = 301
    MAXIMUM_RECORD_BYTES = 65536
    MAXIMUM_JOURNAL_BYTES = 8 * 1024 * 1024

    def __init__(self, path, *, owner_code, owner_thread=None, interval_seconds=1,
                 cap_seconds=300, selectors=SELECTORS):
        if (type(owner_code) is not CodeType
                or not math.isfinite(interval_seconds) or not 0.01 <= interval_seconds <= 1
                or not math.isfinite(cap_seconds) or not 0 < cap_seconds <= 300
                or len(selectors) > 32):
            raise ValueError('bounded journal limits and original owner code required')
        self.path = Path(path)
        self.owner_thread = threading.get_ident() if owner_thread is None else owner_thread
        self.interval_seconds, self.cap_seconds = interval_seconds, cap_seconds
        self._selectors = tuple(selectors)
        self._codes = {'owner.strict_main': owner_code}
        self._stop = threading.Event()
        self._thread = self._file = None
        self._lock = threading.Lock()
        self._closed = False
        self._started = None
        self.records = self.samples = self.bytes_written = self.observer_errors = 0
        self.depth_truncations = self.thread_count_caps = self.unowned_samples = 0
        self.cap_reached = self.byte_cap_reached = False

    def _write(self, value):
        value.update(diagnostic_only=True, functional_qualification=False,
                     latency_qualification=False)
        data = (json.dumps(value, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')
        if (len(data) > self.MAXIMUM_RECORD_BYTES
                or self.bytes_written + len(data) > self.MAXIMUM_JOURNAL_BYTES):
            self.byte_cap_reached = True
            self._stop.set()
            return False
        self._file.write(data)
        self._file.flush()
        self.bytes_written += len(data)
        self.records += 1
        return True

    def __enter__(self):
        if self._closed or self._thread is not None:
            raise RuntimeError('journal is single use')
        monitoring = getattr(sys, 'monitoring', None)
        if (sys.getprofile() is not None or sys.gettrace() is not None
                or threading.getprofile() is not None or threading.gettrace() is not None
                or monitoring is not None and any(monitoring.get_tool(tool) is not None
                    for tool in (monitoring.PROFILER_ID, monitoring.DEBUGGER_ID))):
            raise RuntimeError('existing observer prevents clean setup measurement')
        self._file = self.path.open('xb')
        self._started = time.monotonic()
        self._write(dict(schema='flora-connected-setup-journal-v1', kind='start',
            interval_seconds=self.interval_seconds, cap_seconds=self.cap_seconds,
            maximum_samples=self.MAXIMUM_SAMPLES, maximum_threads=self.MAXIMUM_THREADS,
            inspected_threads=1, maximum_stack_depth=self.MAXIMUM_DEPTH,
            maximum_journal_bytes=self.MAXIMUM_JOURNAL_BYTES,
            interpretation='wall_residency_not_call_counts_exclusive_cpu_or_authority'))
        self._thread = threading.Thread(target=self._run, name='flora-setup-journal', daemon=True)
        self._thread.start()
        return self

    def _resolve(self):
        for tag, module, names, nested in self._selectors:
            if tag not in self._codes:
                code = loaded_code(module, names, nested)
                if code is not None:
                    self._codes[tag] = code

    def _sample(self):
        snapshots = frame = current = None
        try:
            self._resolve()
            snapshots = sys._current_frames()
            frame = snapshots.get(self.owner_thread)
            current = frame
            tags = {code: tag for tag, code in self._codes.items()}
            matches, owned, depth = [], False, 0
            while current is not None and depth < self.MAXIMUM_DEPTH:
                code = current.f_code
                tag = tags.get(code)
                if tag is not None:
                    matches.append(dict(tag=tag, line=current.f_lineno, depth=depth))
                    owned = owned or tag in ('owner.strict_main', 'owner.build')
                current = current.f_back
                depth += 1
            truncated = current is not None
            self.depth_truncations += int(truncated)
            count_capped = len(snapshots) > self.MAXIMUM_THREADS
            self.thread_count_caps += int(count_capped)
            self.unowned_samples += int(not owned)
            return dict(kind='sample', sample=self.samples,
                elapsed_seconds=round(time.monotonic() - self._started, 6),
                owned_stack=owned, frames=matches if owned else [],
                stack_depth=depth, stack_depth_truncated=truncated,
                available_threads=min(len(snapshots), self.MAXIMUM_THREADS),
                thread_count_capped=count_capped,
                resolved_fixed_tags=sorted(self._codes))
        finally:
            # Do not retain live frames or their local/payload/permission values.
            current = frame = snapshots = None

    def _run(self):
        try:
            while not self._stop.is_set():
                with self._lock:
                    if self._closed:
                        break
                    if (time.monotonic() - self._started >= self.cap_seconds
                            or self.samples >= self.MAXIMUM_SAMPLES):
                        self.cap_reached = True
                        break
                    self._write(self._sample())
                    self.samples += 1
                if self._stop.wait(self.interval_seconds):
                    break
        except BaseException:
            # Never serialize exception messages or disturb the original action.
            self.observer_errors += 1

    def close(self, outcome='closed'):
        self._stop.set()
        with self._lock:
            if self._closed:
                return
            self._closed = True
        if self._thread is not None:
            self._thread.join(timeout=1)
        with self._lock:
            if self._file is not None:
                try:
                    self._write(dict(kind='close', outcome=outcome,
                        elapsed_seconds=round(time.monotonic() - self._started, 6),
                        samples=self.samples, observer_errors=self.observer_errors,
                        depth_truncations=self.depth_truncations,
                        thread_count_caps=self.thread_count_caps,
                        unowned_samples=self.unowned_samples, cap_reached=self.cap_reached,
                        byte_cap_reached=self.byte_cap_reached,
                        sampler_stopped=self._thread is None or not self._thread.is_alive()))
                finally:
                    self._file.close()
                    self._file = None

    def __exit__(self, exc_type, exc, traceback):
        self.close('return' if exc_type is None else
                   'cancel' if issubclass(exc_type, (KeyboardInterrupt, SystemExit)) else 'exception')
        return False


def observe(action, *, journal, interval_seconds=1, cap_seconds=300):
    with SetupJournal(journal, owner_code=action.__code__, interval_seconds=interval_seconds,
                      cap_seconds=cap_seconds):
        return action()


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--journal-cap-seconds', type=float, default=300)
    parser.add_argument('--journal-interval-seconds', type=float, default=1)
    arguments, original_arguments = parser.parse_known_args()
    from run_connected_functional_comparison import main as strict_main

    sys.argv[:] = [sys.argv[0], *original_arguments]
    print('Diagnostic setup journal only; fixed code tags and numeric lines every second; '
          'no functional or latency qualification.', file=sys.stderr, flush=True)
    return observe(strict_main, journal=arguments.journal,
        interval_seconds=arguments.journal_interval_seconds,
        cap_seconds=arguments.journal_cap_seconds)


if __name__ == '__main__':
    sys.exit(main())

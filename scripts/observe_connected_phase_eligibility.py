"""One original preparation admission; diagnostic evidence, never eligibility.

Current-thread profiling ends at the first owned owner-map return or initializer
native=False. Only fixed tags, role enums, return lines and allowlisted booleans
are written. The original strict main, runtime objects and code are unchanged.
"""
from __future__ import annotations

import argparse
import dis
import json
import math
from pathlib import Path
import sys
import threading
import time
from types import CodeType, FunctionType, ModuleType


MODULE = 'flora.selected._phase_preparation'
SELECTORS = (
    ('phaseprep.init', '_PhasePreparation', '__init__'),
    ('phaseprep.owner_map', None, '_owner_map'),
    ('phaseprep.callback_specs', None, '_native_callback_specs'),
    ('phaseprep.port_dictionary', None, '_port_dictionary'),
    ('phaseprep.bound_callback', None, '_bound_callback_role'),
)
ROLES = frozenset(('route', 'archive', 'runtime', 'lineage', 'history', 'anchor',
    'control', 'manifests', 'source_authority', 'comparison', 'raw_custody',
    'policy', 'permissions', 'claims', 'state', 'episodes', 'development_guard',
    'episode_verifier', 'sources', 'artifacts', 'references', 'private',
    'personal', 'approval', 'proofs', 'log', 'log_wrapper', 'events', 'objects',
    'object_wrapper', 'backend', 'backend_wrapper', 'sql', 'binding', 'qualifier',
    'codec', 'adapter', 'execution', 'prepared', 'callback'))
RETURN_OPS = frozenset(dis.opmap[name] for name in ('RETURN_VALUE', 'RETURN_CONST')
                       if name in dis.opmap)


class AdmissionObserver:
    """Observe one admission without invoking owners or granting permissions."""

    def __init__(self, path, *, strict_code, deadline_seconds=180,
                 maximum_records=128, maximum_bytes=65536):
        if (type(strict_code) is not CodeType or not math.isfinite(deadline_seconds)
                or not 0 < deadline_seconds <= 180
                or type(maximum_records) is not int or not 3 <= maximum_records <= 128
                or type(maximum_bytes) is not int or not 512 <= maximum_bytes <= 65536):
            raise ValueError('fixed original owner and bounded observation required')
        self.path, self.strict_code = Path(path), strict_code
        self.deadline_seconds = deadline_seconds
        self.maximum_records, self.maximum_bytes = maximum_records, maximum_bytes
        self._hook = self._profile
        self._file = self._started = None
        self._installed = self._done = self._resolved = self._closed = False
        self._build_code = self._preparation_class = None
        self._codes, self._functions, self._namespaces, self._original_codes = {}, {}, {}, {}
        self.records = self.bytes_written = 0

    def _write(self, row, *, terminal=False):
        if self._file is None:
            return False
        row.update(diagnostic_only=True, functional_qualification=False,
                   latency_qualification=False)
        data = (json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
        # Reserve one short terminal record. Never exceed either hard bound.
        reserve = 0 if terminal else 256
        if (self.records >= self.maximum_records - int(not terminal)
                or self.bytes_written + len(data) + reserve > self.maximum_bytes):
            return False
        try:
            self._file.write(data)
            self._file.flush()
            self.records += 1
            self.bytes_written += len(data)
            return True
        except Exception:
            return False

    def _disable(self):
        self._done = True
        if self._installed and sys.getprofile() is self._hook:
            sys.setprofile(None)
        self._installed = False

    def _unsupported(self, reason, line=0):
        self._disable()
        self._write(dict(tag='observer.unsupported', role=reason, return_line=line), terminal=True)

    def __enter__(self):
        if self._started is not None:
            raise RuntimeError('observer is single use')
        self._started = time.monotonic()
        try:
            self._file = self.path.open('xb')
        except Exception:
            self._done = True
            return self
        if not self._write(dict(tag='observer.start', role='observer', return_line=0,
                deadline_seconds=self.deadline_seconds, maximum_stack_depth=128,
                maximum_records=self.maximum_records, maximum_bytes=self.maximum_bytes)):
            self._unsupported('byte_cap')
            return self
        monitoring = getattr(sys, 'monitoring', None)
        if (sys.getprofile() is not None or sys.gettrace() is not None
                or threading.getprofile() is not None or threading.gettrace() is not None
                or monitoring is not None and any(monitoring.get_tool(tool) is not None
                    for tool in (monitoring.PROFILER_ID, monitoring.DEBUGGER_ID))):
            self._unsupported('existing_hook')
            return self
        self._installed = True
        sys.setprofile(self._hook)
        return self

    def _owned(self, frame):
        if self._build_code is None:
            module = sys.modules.get('registered_functional_case_fixture')
            cls = vars(module).get('RegisteredFunctionalCase') if type(module) is ModuleType else None
            function = vars(cls).get('build') if type(cls) is type else None
            if type(function) is not FunctionType:
                self._unsupported('missing_owner')
                return False
            self._build_code = function.__code__
        current, strict, build = frame, False, False
        try:
            for _ in range(128):
                if current is None:
                    return strict and build
                strict = strict or current.f_code is self.strict_code
                build = build or current.f_code is self._build_code
                if strict and build:
                    return True
                current = current.f_back
            self._unsupported('depth_cap', frame.f_lineno)
            return False
        finally:
            current = frame = None

    def _resolve(self, frame):
        module = sys.modules.get(MODULE)
        namespace = vars(module) if type(module) is ModuleType else None
        if namespace is None:
            self._unsupported('missing_selector', frame.f_lineno)
            return False
        seals, helpers, shapes = (namespace.get(name) for name in ('_CODES', '_HELPERS', '_SHAPES'))
        if any(type(value) is not tuple or len(value) > 4096 for value in (seals, helpers, shapes)):
            self._unsupported('missing_original_seal', frame.f_lineno)
            return False
        cls = namespace.get('_PhasePreparation')
        if type(cls) is not type:
            self._unsupported('changed_selector', frame.f_lineno)
            return False
        for tag, class_name, name in SELECTORS:
            owner = cls if class_name else module
            original_namespace = vars(owner)
            function = original_namespace.get(name)
            if (type(function) is not FunctionType or function.__globals__ is not namespace
                    or function.__code__.co_filename != frame.f_code.co_filename
                    or function.__code__.co_flags & (0x20 | 0x80 | 0x200)
                    or not any(type(pair) is tuple and len(pair) == 2
                        and pair[0] is function and pair[1] is function.__code__ for pair in seals)):
                self._unsupported('changed_selector', frame.f_lineno)
                return False
            if class_name:
                original = any(type(pair) is tuple and len(pair) == 2 and pair[0] is cls
                    and type(pair[1]) is tuple and any(type(entry) is tuple and len(entry) == 2
                        and entry[0] == name and entry[1] is function for entry in pair[1]) for pair in shapes)
            else:
                original = any(type(pair) is tuple and len(pair) == 2
                    and pair[0] == name and pair[1] is function for pair in helpers)
            if not original:
                self._unsupported('changed_selector', frame.f_lineno)
                return False
            self._codes[function.__code__] = tag
            self._original_codes[tag] = function.__code__
            self._functions[tag] = function
            self._namespaces[tag] = (original_namespace, name, function)
        self._preparation_class = cls
        self._resolved = True
        return True

    def _profile(self, frame, event, argument):
        if self._done or event not in ('call', 'return'):
            return
        try:
            if time.monotonic() - self._started >= self.deadline_seconds:
                self._unsupported('deadline')
                return
            code = frame.f_code
            tag = self._codes.get(code)
            if tag is not None and code is not self._original_codes[tag]:
                self._unsupported('changed_code', frame.f_lineno)
                return
            if tag is None:
                # The hot path performs no module walk. Resolve once when an
                # original loaded target is first encountered in the owned tree.
                if (not code.co_filename.replace('\\', '/').endswith('/flora/selected/_phase_preparation.py')
                        or code.co_qualname not in ('_PhasePreparation.__init__',
                            '_owner_map', '_native_callback_specs', '_port_dictionary', '_bound_callback_role')):
                    return
                if not self._owned(frame):
                    return
                if self._resolved:
                    self._unsupported('changed_code', frame.f_lineno)
                    return
                if not self._resolve(frame):
                    return
                tag = self._codes.get(code)
                if tag is None:
                    self._unsupported('changed_code', frame.f_lineno)
                    return
            if event != 'return' or not self._owned(frame):
                return
            if any(namespace.get(name) is not function or function.__code__ is not self._original_codes[tag]
                   for tag, (namespace, name, function) in self._namespaces.items()):
                self._unsupported('changed_selector', frame.f_lineno)
                return
            # Profile return(None) also occurs during exception unwinding. It
            # must never be mistaken for an admission's ordinary refusal.
            if (not 0 <= frame.f_lasti < len(code.co_code)
                    or code.co_code[frame.f_lasti] not in RETURN_OPS):
                self._unsupported('exception_return', frame.f_lineno)
                return
            row = dict(tag=tag, role='preparation' if tag == 'phaseprep.init' else 'callback',
                       return_line=frame.f_lineno, returned_none=argument is None)
            if tag == 'phaseprep.init':
                owner = frame.f_locals.get('self')
                if type(owner) is not self._preparation_class:
                    self._unsupported('changed_owner', frame.f_lineno)
                    return
                native = object.__getattribute__(owner, '__dict__').get('native')
                if type(native) is not bool:
                    self._unsupported('missing_native_boolean', frame.f_lineno)
                    return
                row.update(native=native, exact_metaclass_type=type(type(owner)) is type)
                if not native:
                    self._disable()
            else:
                caller = frame.f_back
                role = frame.f_locals.get('role') if tag == 'phaseprep.owner_map' else (
                    caller.f_locals.get('role') if caller is not None
                    and self._codes.get(caller.f_code) == 'phaseprep.owner_map' else None)
                row['role'] = role if type(role) is str and role in ROLES else 'unknown'
                if tag == 'phaseprep.port_dictionary':
                    row['exact_metaclass_type'] = type(type(frame.f_locals.get('owner'))) is type
                if tag == 'phaseprep.bound_callback' and argument is False:
                    row['native'] = False
                if tag == 'phaseprep.owner_map':
                    self._disable()
            if not self._write(row):
                self._unsupported('record_or_byte_cap', frame.f_lineno)
        except Exception:
            # Observer failures are never raised into the action or serialized.
            self._unsupported('observer_error')

    def close(self, outcome='return'):
        if self._closed:
            return
        self._closed = True
        replaced = self._installed and sys.getprofile() is not self._hook
        self._disable()
        self._write(dict(tag='observer.close', role='hook_replaced' if replaced else outcome,
                         return_line=0), terminal=True)
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None

    def __exit__(self, exc_type, exc, traceback):
        self.close('return' if exc_type is None else
                   'cancel' if issubclass(exc_type, (KeyboardInterrupt, SystemExit)) else 'exception')
        return False


def observe(action, *, journal, deadline_seconds=180):
    with AdmissionObserver(journal, strict_code=action.__code__, deadline_seconds=deadline_seconds):
        return action()


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--eligibility-journal', type=Path, required=True)
    parser.add_argument('--eligibility-deadline-seconds', type=float, default=180)
    arguments, original_arguments = parser.parse_known_args()
    from run_connected_functional_comparison import main as strict_main

    sys.argv[:] = [sys.argv[0], *original_arguments]
    print('Diagnostic first preparation admission only; no eligibility grant, '
          'functional or latency qualification.', file=sys.stderr, flush=True)
    return observe(strict_main, journal=arguments.eligibility_journal,
                   deadline_seconds=arguments.eligibility_deadline_seconds)


if __name__ == '__main__':
    sys.exit(main())

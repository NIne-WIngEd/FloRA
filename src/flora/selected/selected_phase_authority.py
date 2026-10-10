"""Private identity for an actual selected-history phase producer.

An issued descriptor recognizes bindings only. It stores no successful allow,
head, qualification, private-read lease or metadata observation. Existing gates
still run their phase and member predicates on every invocation.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import CodeType, FunctionType, MethodType
from weakref import ref

from .comparison_custody import SelectedRunEvidencePolicy, XTDBComparisonCustody
from .experience import KurrentExperienceLog
from .formation_policy import XTDBFormationPermissionPolicy
from .formation_registry import XTDBFormationSourceRegistry
from .judgment_context import RegisteredJudgmentContextPolicy
from .native_phase_gate import _CREATED_GATES, _ORIGINAL_GATE_CODE, transfer_native_phase_gate
from .native_reads import SelectedNativeReadServices
from .selected_history_fence import (
    DOMAIN, _held_snapshot, _require_held_contracts, selected_phase_member,
)
from .source_closure import _ReaderBinding, _native_snapshot, _require_native_contracts


_ABSENT = object()
_ISSUED = {}
_TOKEN = object()
_HOLD = "_selected_phase_authority_hold"
_INSTALL = SelectedNativeReadServices._install_phase_source_gate
_INSTALL_CODE = _INSTALL.__code__
_CALLBACK_CODES = {code.co_name: code for code in _INSTALL_CODE.co_consts
                   if type(code) is CodeType and code.co_name in {
                       "phase_binding", "phase_now", "phase_member"}}
# There are selected and legacy phase_member bodies. Select the one which
# actually resolves bounded original membership, rather than whole replay.
_CALLBACK_CODES["phase_member"] = next(code for code in _INSTALL_CODE.co_consts
    if type(code) is CodeType and code.co_name == "phase_member"
    and "selected_phase_member" in code.co_freevars)
_CANONICAL = {
    SelectedRunEvidencePolicy: ("authorize_history", "authorize_history_metadata"),
    XTDBComparisonCustody: ("_key", "metadata", "metadata_selected"),
    XTDBFormationSourceRegistry: ("_key", "_fetch", "_decode", "lookup",
        "lookup_commitment", "raw_metadata", "raw_reference"),
    XTDBFormationPermissionPolicy: ("_key", "_fetch", "_decode", "_head",
        "_stored_action", "current_action", "permits"),
    KurrentExperienceLog: ("lookup_committed", "replay", "replay_committed"),
}
_METHODS = tuple((cls, name, getattr(cls, name), getattr(cls, name).__code__)
    for cls, names in _CANONICAL.items() for name in names)
_SELECTED_MEMBER = selected_phase_member
_SELECTED_MEMBER_CODE = selected_phase_member.__code__
_TRANSFER_CODE = next(code for code in transfer_native_phase_gate.__code__.co_consts
    if type(code) is CodeType and code.co_name == "gate")


def _fields(owner):
    values = object.__getattribute__(owner, "__dict__")
    if type(values) is not dict or any(type(key) is not str for key in values):
        raise PermissionError("selected phase needs ordinary native owner fields")
    return values


def _native_owner_class(owner):
    owner_class = type(owner)
    if type(owner_class) is not type:
        raise PermissionError("selected phase recognition needs a native owner metaclass")
    if any(type(base) is not type for base in type.__getattribute__(owner_class, "__mro__")):
        raise PermissionError("selected phase recognition needs native base metaclasses")
    return owner_class


def _plain_descriptor(owner_class, name):
    for base in type.__getattribute__(owner_class, "__mro__"):
        if type(base) is not type:
            raise PermissionError("selected phase recognition needs native base metaclasses")
        fields = type.__getattribute__(base, "__dict__")
        if name in fields:
            return fields[name]
    return _ABSENT


def _capture_reader(owner, name):
    _native_owner_class(owner)
    return _ReaderBinding.capture(owner, name)


def _ordinary_port(owner, name):
    """Only the fixed scope and installed-gate ports enter a pure native pass."""
    if name not in ("scope", "permits", "allow_event"):
        raise TypeError("selected phase recognition has an unsupported ordinary port")
    owner_class = _native_owner_class(owner)
    if (_plain_descriptor(owner_class, "__getattribute__") is not object.__getattribute__
            or _plain_descriptor(owner_class, "__getattr__") is not _ABSENT):
        raise TypeError("selected phase recognition needs ordinary scope and gate lookup")
    descriptor = _plain_descriptor(owner_class, name)
    if descriptor is not _ABSENT and (name == "scope" or type(descriptor) is not FunctionType):
        raise TypeError("selected phase recognition cannot execute a scope or gate descriptor")
    reader = _capture_reader(owner, name)
    if reader.dictionary is None or name not in reader.dictionary:
        raise TypeError("selected phase recognition needs an ordinary instance port")
    if name != "scope" and (type(reader.instance_value) is not MethodType
            or reader.instance_value.__self__ is not owner):
        raise TypeError("selected phase recognition needs its installed instance gate")
    return reader


@dataclass(frozen=True)
class _FunctionBinding:
    function: object
    code: object
    closure: tuple
    globals: tuple
    nested: tuple

    @classmethod
    def capture(cls, function):
        if type(function) is not FunctionType:
            raise TypeError("selected phase callback must be an actual native function")
        return cls(function, function.__code__,
            tuple((cell, cell.cell_contents) for cell in function.__closure__ or ()),
            tuple((name, function.__globals__.get(name, _ABSENT))
                  for name in set(function.__code__.co_names)),
            tuple(cls.capture(cell.cell_contents) for cell in function.__closure__ or ()
                  if type(cell.cell_contents) is FunctionType and cell.cell_contents is not function))

    def _verify_shallow(self):
        """Check this capture; traversal belongs to the current verifier."""
        if (self.function.__code__ is not self.code
                or tuple(self.function.__closure__ or ()) != tuple(cell for cell, _ in self.closure)
                or any(cell.cell_contents is not value for cell, value in self.closure)
                or any(self.function.__globals__.get(name, _ABSENT) is not value
                       for name, value in self.globals)):
            raise PermissionError("selected phase actual callback binding changed")

    def verify(self):
        self._verify_shallow()
        for nested in self.nested:
            nested.verify()


def _native_method(owner, name, expected):
    method = getattr(owner, name)
    if (type(method) is not MethodType or method.__self__ is not owner
            or method.__func__ is not expected):
        raise TypeError("selected phase has a custom native reader")


def _gate_binding(owner, name, *, original=True):
    method = getattr(owner, name)
    if (type(method) is not MethodType or method.__self__ is not owner
            or method.__func__ not in _CREATED_GATES
            or original and method.__func__.__code__ is not _ORIGINAL_GATE_CODE):
        raise TypeError("selected phase needs its privately created actual gate")
    binding = _FunctionBinding.capture(method.__func__)
    return method, binding, dict(zip(method.__func__.__code__.co_freevars,
                                   (cell.cell_contents for cell in method.__func__.__closure__)))


class _Origin:
    def __init__(self, *, runtime, lineage, entry, history, initial_authority,
                 original_permissions, phase_now, phase_member):
        _require_native_contracts()
        _require_held_contracts()
        _ordinary_port(runtime, "scope")
        _capture_reader(lineage, "history_authority")
        self.runtime, self.lineage, self.entry, self.history = runtime, lineage, entry, history
        self.authority = authority = _fields(lineage)["history_authority"]
        self.initial_authority, self.original_permissions = initial_authority, original_permissions
        self.registry, self.log = registry, log = _fields(runtime)["sources"], _fields(runtime)["log"]
        self.permissions = permissions = _fields(authority)["permissions"]
        self.custody = custody = _fields(authority)["custody"]
        if (type(authority) is not SelectedRunEvidencePolicy
                or type(initial_authority) is not SelectedRunEvidencePolicy
                or type(custody) is not XTDBComparisonCustody
                or any(type(policy) is not XTDBFormationPermissionPolicy
                       for policy in (permissions, original_permissions))
                or type(registry) is not XTDBFormationSourceRegistry
                or type(log) is not KurrentExperienceLog):
            raise TypeError("selected phase origin has custom or unknown physical owners")
        for owner in (registry, log, permissions, custody, initial_authority.custody):
            _ordinary_port(owner, "scope")
        for owner, name in ((_fields(runtime)["source_policy"], "permits"),
                (_fields(runtime)["context_policy"], "allow_event")):
            _ordinary_port(owner, name)
        self.cap = _fields(authority)["maximum_history_sources"]
        if (type(self.cap) is not int or self.cap < 2
                or type(authority.history_metadata_domain) is not str
                or authority.history_metadata_domain != DOMAIN
                or initial_authority.history_metadata_domain != DOMAIN
                or initial_authority.maximum_history_sources != self.cap):
            raise TypeError("selected phase origin lacks the exact selected domain and cap")
        self.connection = registry.connection
        self.scope = _native_snapshot(registry.scope)
        self.namespace = registry.authority_namespace_id
        if (permissions.registry is not registry or permissions.connection is not self.connection
                or custody.registry is not registry or custody.log is not log
                or custody.connection is not self.connection
                or any(_native_snapshot(value.scope) != self.scope
                       for value in (runtime, log, custody, permissions, initial_authority.custody))
                or any(value.authority_namespace_id != self.namespace
                       for value in (runtime, custody, permissions))):
            raise TypeError("selected phase actual origins do not share their physical scope")
        self.held = _held_snapshot(history)
        self.history_sha256 = history.digest()
        self.event_ids = history.event_ids
        self.case_id, self.phase = entry.case_id, entry.phase
        self.callbacks = phase_now, phase_member
        now_cells = dict(zip(phase_now.__code__.co_freevars,
                            (cell.cell_contents for cell in phase_now.__closure__ or ())))
        member_cells = dict(zip(phase_member.__code__.co_freevars,
                               (cell.cell_contents for cell in phase_member.__closure__ or ())))
        phase_binding = now_cells.get("phase_binding")
        if (phase_now.__code__ is not _CALLBACK_CODES["phase_now"]
                or phase_member.__code__ is not _CALLBACK_CODES["phase_member"]
                or type(phase_binding) is not FunctionType
                or phase_binding.__code__ is not _CALLBACK_CODES["phase_binding"]
                or member_cells.get("phase_binding") is not phase_binding
                or any(now_cells.get(key) is not value for key, value in (
                    ("authority", authority), ("entry", entry), ("history", history)))
                or any(member_cells.get(key) is not value for key, value in (
                    ("phase_registry", registry), ("phase_log", log),
                    ("phase_permissions", permissions), ("selected_phase_member", _SELECTED_MEMBER)))):
            raise TypeError("selected phase needs callbacks from its actual native installer")
        self.originals = member_cells["originals"]
        self.original_snapshot = self._original_snapshot()
        self.function_bindings = tuple(_FunctionBinding.capture(value)
            for value in (phase_now, phase_member, phase_binding))
        bindings = []
        for owner in (authority, initial_authority, custody, registry, permissions,
                      original_permissions, log):
            for name in _CANONICAL[type(owner)]:
                expected = next(function for cls, port, function, _ in _METHODS
                    if cls is type(owner) and port == name)
                _native_method(owner, name, expected)
                bindings.append(_capture_reader(owner, name))
        for owner, names in (
            (runtime, ("sources", "log", "source_policy", "context_policy", "scope", "authority_namespace_id")),
            (lineage, ("history_authority",)), (entry, ("case_id", "phase")),
            (authority, ("custody", "permissions", "run_id", "history_metadata_domain", "maximum_history_sources")),
            (initial_authority, ("custody", "permissions", "run_id", "history_metadata_domain", "maximum_history_sources")),
            (custody, ("connection", "registry", "log", "objects", "raw_custody", "scope", "scope_digest", "authority_namespace_id")),
            (registry, ("connection", "scope", "scope_digest", "authority_namespace_id")),
            (permissions, ("connection", "registry", "scope", "scope_digest", "authority_namespace_id")),
            (original_permissions, ("connection", "registry", "scope", "scope_digest", "authority_namespace_id")),
            (log, ("client", "stream", "scope")),
            (registry.connection, ("execute",)), (log.client, ("get_stream",)),
            (custody.objects, ("scope", "namespace")),
        ):
            bindings.extend(_capture_reader(owner, name) for name in names)
        self.readers = tuple(bindings)

    def _original_snapshot(self):
        if (type(self.originals) is not dict or any(type(key) is not str for key in self.originals)
                or tuple(self.originals) != self.event_ids):
            raise PermissionError("selected phase original membership changed")
        return tuple((key, _held_snapshot(value)) for key, value in self.originals.items())

    def _verify_contracts(self):
        _require_descriptor_contracts()
        _require_native_contracts()
        _require_held_contracts()
        if (SelectedNativeReadServices._install_phase_source_gate is not _INSTALL
                or _INSTALL.__code__ is not _INSTALL_CODE
                or selected_phase_member is not _SELECTED_MEMBER
                or _SELECTED_MEMBER.__code__ is not _SELECTED_MEMBER_CODE
                or any(type(cls) is not type or any(type(base) is not type
                           for base in type.__getattribute__(cls, "__mro__"))
                       or getattr(cls, name) is not function or function.__code__ is not code
                       for cls, name, function, code in _METHODS)):
            raise PermissionError("selected phase canonical producer code changed")

    def _verify_basis(self):
        if (any(_native_snapshot(owner.scope) != self.scope
                for owner in (self.runtime, self.registry, self.permissions, self.log, self.custody))
                or _held_snapshot(self.history) != self.held
                or self._original_snapshot() != self.original_snapshot):
            raise PermissionError("selected phase held material or scope changed")

    def verify(self):
        self._verify_contracts()
        for binding in self.readers + self.function_bindings:
            if type(binding) is _ReaderBinding:
                _native_owner_class(binding.owner)
            binding.verify()
        self._verify_basis()


@dataclass(frozen=True)
class SelectedPhaseAuthorityDescriptor:
    """Private-issued producer identity; verification performs no live IO."""
    _token: object
    _origin: object
    _owner: object
    _name: str
    _method: object
    _gate: object
    _parents: tuple
    _reader: object

    @property
    def case_id(self):
        return self._origin.case_id

    @property
    def phase(self):
        return self._origin.phase

    @property
    def history_sha256(self):
        return self._origin.history_sha256

    @property
    def original_event_ids(self):
        return self._origin.event_ids

    def verify(self):
        _require_descriptor_contracts()
        _verify_selected_phase_tree((self,))
        return self


@dataclass(frozen=True)
class _Registration:
    owner: object
    descriptor: object
    descriptor_seal: tuple
    origin_seal: tuple


def _identity_seal(value):
    """Independent field identities; no strong owner references are retained."""
    fields = _fields(value)
    return type(value), id(fields), tuple((name, type(item), id(item))
        for name, item in fields.items())


def _function_seal(binding):
    return _identity_seal(binding), tuple(_function_seal(value) for value in binding.nested)


def _verify_identity(value, expected, native_class):
    if type(value) is not native_class or _identity_seal(value) != expected:
        raise PermissionError("selected phase issued descriptor or origin fields changed")


def _verify_function_seal(binding, expected):
    _verify_identity(binding, expected[0], _FunctionBinding)
    for value, nested in zip(binding.nested, expected[1]):
        _verify_function_seal(value, nested)


def _origin_seal(origin):
    return (_identity_seal(origin), tuple(_identity_seal(value) for value in origin.readers),
            tuple(_function_seal(value) for value in origin.function_bindings))


def _verify_origin_seal(origin, expected):
    _verify_identity(origin, expected[0], _Origin)
    for value, snapshot in zip(origin.readers, expected[1]):
        _verify_identity(value, snapshot, _ReaderBinding)
    for value, snapshot in zip(origin.function_bindings, expected[2]):
        _verify_function_seal(value, snapshot)


def _descriptor_seal(descriptor):
    return (_identity_seal(descriptor), _function_seal(descriptor._gate),
            _identity_seal(descriptor._reader))


def _verify_selected_phase_tree(descriptors):
    """Observe the finite native graph once; compare every issued expectation."""
    _require_descriptor_contracts()
    if type(descriptors) is not tuple or len(descriptors) not in (1, 2):
        raise PermissionError("selected phase verification needs native descriptor roots")
    # Hold exact objects, keyed by native identity, until this pure pass ends.
    # This collection is never supplied by a caller or retained across a gate,
    # reader, authority callback or later public verification invocation.
    identities, functions = {}, {}
    checked_origins, checked_readers, checked_bindings = {}, {}, {}

    def require_identity(value, expected, native_class):
        if type(value) is not native_class:
            raise PermissionError("selected phase issued descriptor or origin fields changed")
        observed = identities.get(id(value))
        if observed is None or observed[0] is not value:
            observed = value, _identity_seal(value)
            identities[id(value)] = observed
        actual = observed[1]
        if (actual[0] is not expected[0] or actual[1] != expected[1]
                or len(actual[2]) != len(expected[2])
                or any(name != saved_name or cls is not saved_cls or identity != saved_identity
                       for (name, cls, identity), (saved_name, saved_cls, saved_identity)
                       in zip(actual[2], expected[2]))):
            raise PermissionError("selected phase issued descriptor or origin fields changed")

    def verify_function_seal(binding, expected):
        require_identity(binding, expected[0], _FunctionBinding)
        for value, nested in zip(binding.nested, expected[1]):
            verify_function_seal(value, nested)

    def verify_origin_seal(origin, expected):
        require_identity(origin, expected[0], _Origin)
        for value, snapshot in zip(origin.readers, expected[1]):
            require_identity(value, snapshot, _ReaderBinding)
        for value, snapshot in zip(origin.function_bindings, expected[2]):
            verify_function_seal(value, snapshot)

    def observe_function(function):
        code = function.__code__
        cells = tuple(function.__closure__ or ())
        return (function, code, cells, tuple(cell.cell_contents for cell in cells),
                {name: function.__globals__.get(name, _ABSENT) for name in set(code.co_names)})

    def verify_binding(binding):
        if checked_bindings.get(id(binding)) is binding:
            return
        # Independent issuance seals have already rejected a replaced capture.
        function = binding.function
        if type(function) is not FunctionType:
            raise PermissionError("selected phase actual callback binding changed")
        observed = functions.get(id(function))
        if observed is None or observed[0] is not function:
            observed = observe_function(function)
            functions[id(function)] = observed
        _, code, cells, values, globals_now = observed
        if (code is not binding.code or len(cells) != len(binding.closure)
                or any(cell is not saved_cell or value is not saved_value
                       for cell, value, (saved_cell, saved_value)
                       in zip(cells, values, binding.closure))
                or any(globals_now.get(name, _ABSENT) is not value
                       for name, value in binding.globals)):
            raise PermissionError("selected phase actual callback binding changed")
        for nested in binding.nested:
            verify_binding(nested)
        checked_bindings[id(binding)] = binding

    def verify_reader(reader):
        if checked_readers.get(id(reader)) is not reader:
            _native_owner_class(reader.owner)
            reader.verify()
            checked_readers[id(reader)] = reader

    def verify_origin(origin):
        if checked_origins.get(id(origin)) is not origin:
            origin._verify_contracts()
            for reader in origin.readers:
                verify_reader(reader)
            for binding in origin.function_bindings:
                verify_binding(binding)
            origin._verify_basis()
            checked_origins[id(origin)] = origin

    def verify(descriptor):
        if type(descriptor) is not SelectedPhaseAuthorityDescriptor:
            raise PermissionError("selected phase descriptor native class changed")
        if type(descriptor._name) is not str or descriptor._token is not _TOKEN:
            raise PermissionError("selected phase descriptor native identity changed")
        registered = _ISSUED.get((id(descriptor._owner), descriptor._name))
        if (registered is None or registered.owner() is not descriptor._owner
                or registered.descriptor() is not descriptor):
            raise PermissionError("selected phase descriptor was not privately issued")
        # Every descriptor and parent keeps its independent issuance seals.
        # Reject replacements before inspecting any supplied replacement.
        require_identity(descriptor, registered.descriptor_seal[0], SelectedPhaseAuthorityDescriptor)
        verify_function_seal(descriptor._gate, registered.descriptor_seal[1])
        require_identity(descriptor._reader, registered.descriptor_seal[2], _ReaderBinding)
        verify_origin_seal(descriptor._origin, registered.origin_seal)
        origin = descriptor._origin
        verify_origin(origin)
        for parent in descriptor._parents:
            verify(parent)
        verify_reader(descriptor._reader)
        verify_binding(descriptor._gate)
        method = getattr(descriptor._owner, descriptor._name)
        if (type(method) is not MethodType or method.__self__ is not descriptor._owner
                or method.__func__ is not descriptor._method.__func__):
            raise PermissionError("selected phase installed gate owner changed")

    for descriptor in descriptors:
        verify(descriptor)


def _verify_selected_phase_pair(permission_descriptor, event_descriptor):
    """Check two issued trees without producing or retaining authority proof."""
    _require_descriptor_contracts()
    _verify_selected_phase_tree((permission_descriptor, event_descriptor))


def _register(owner, name, origin, parents=()):
    reader = _ordinary_port(owner, name)
    method, gate, _ = _gate_binding(owner, name, original=False)
    descriptor = SelectedPhaseAuthorityDescriptor(_TOKEN, origin, owner, name, method,
        gate, parents, reader)
    # Weak issuance references do not keep closed sessions alive. Owner-held
    # descriptors and gate/origin cycles are collected together normally.
    key = id(owner), name
    def discard(weak_owner):
        registered = _ISSUED.get(key)
        if registered is not None and registered.owner is weak_owner:
            del _ISSUED[key]
    _ISSUED[key] = _Registration(ref(owner, discard), ref(descriptor),
        _descriptor_seal(descriptor), _origin_seal(origin))
    held = dict(_fields(owner).get(_HOLD, {}))
    held[name] = descriptor
    setattr(owner, _HOLD, held)
    descriptor.verify()
    return descriptor


def _issue_selected_phase_authority(*, runtime, lineage, entry, history,
        initial_authority, original_permissions, phase_now, phase_member):
    """Optional recognition only: unsupported existing gates keep running."""
    try:
        origin = _Origin(runtime=runtime, lineage=lineage, entry=entry, history=history,
            initial_authority=initial_authority, original_permissions=original_permissions,
            phase_now=phase_now, phase_member=phase_member)
        if (type(runtime.source_policy) is not XTDBFormationPermissionPolicy
                or type(runtime.context_policy) is not RegisteredJudgmentContextPolicy):
            raise TypeError("selected phase installation has custom gate owners")
        for owner, name, predicate in ((runtime.source_policy, "permits", XTDBFormationPermissionPolicy.permits),
                (runtime.context_policy, "allow_event", RegisteredJudgmentContextPolicy.allow_event)):
            method, _, cells = _gate_binding(owner, name)
            original = cells.get("original")
            if (cells.get("owner") is not owner or cells.get("name") != name
                    or cells.get("canonical") is not True
                    or type(original) is not MethodType or original.__self__ is not owner
                    or original.__func__ is not predicate or cells.get("installed") != method
                    or cells.get("phase_now") is not phase_now or cells.get("phase_member") is not phase_member):
                raise TypeError("selected phase installed callbacks are custom or detached")
        origin.verify()
    except (AttributeError, KeyError, PermissionError, TypeError, ValueError):
        return False
    _register(runtime.source_policy, "permits", origin)
    _register(runtime.context_policy, "allow_event", origin)
    return True


def selected_phase_authority(owner, name):
    """Return a current privately issued identity, or None for unknown gates."""
    _require_descriptor_contracts()
    if type(name) is not str:
        return None
    registered = _ISSUED.get((id(owner), name))
    if registered is None or registered.owner() is not owner:
        return None
    descriptor = registered.descriptor()
    return None if descriptor is None else _DESCRIPTOR_VERIFY(descriptor)


def _inherit_selected_phase_authority(source_owner, name, target_owner):
    descriptor = selected_phase_authority(source_owner, name)
    if descriptor is None:
        return False
    from .selected_context import SelectedJudgmentContextPolicy
    if type(target_owner) not in (type(source_owner), SelectedJudgmentContextPolicy):
        return False
    try:
        _ordinary_port(target_owner, name)
    except (AttributeError, KeyError, PermissionError, TypeError, ValueError):
        return False
    method, _, cells = _gate_binding(target_owner, name, original=False)
    if method.__func__ is not descriptor._method.__func__:
        checker = cells.get("binding_current")
        binding_cells = ({} if type(checker) is not FunctionType else
            dict(zip(checker.__code__.co_freevars,
                     (cell.cell_contents for cell in checker.__closure__ or ()))))
        if (type(target_owner) is not SelectedJudgmentContextPolicy
                or method.__func__.__code__ is not _TRANSFER_CODE
                or binding_cells.get("source_owner") is not source_owner or cells.get("name") != name
                or binding_cells.get("source_gate") is not descriptor._method.__func__
                or binding_cells.get("source_installed") != descriptor._method
                or cells.get("phase_now") is not descriptor._origin.callbacks[0]
                or cells.get("phase_member") is not descriptor._origin.callbacks[1]
                or cells.get("selected_predicate") is not SelectedJudgmentContextPolicy.allow_event):
            return False
    _register(target_owner, name, descriptor._origin, (descriptor,))
    return True


def _require_descriptor_contracts():
    for name, function, code in _HELPERS:
        if globals().get(name) is not function or function.__code__ is not code:
            raise PermissionError("selected phase descriptor verifier binding changed")
    for cls, shape in _CLASS_SHAPES:
        current = vars(cls)
        extra = "__slotnames__" not in dict(shape) and "__slotnames__" in current
        if (len(current) != len(shape) + int(extra)
                or any(current.get(name) is not value for name, value in shape)
                or extra and (type(current["__slotnames__"]) is not list or current["__slotnames__"])):
            raise PermissionError("selected phase descriptor verifier class changed")
    if any(function.__code__ is not code for function, code in _CLASS_CODES):
        raise PermissionError("selected phase descriptor verifier code changed")
    if any(globals().get(name) is not value or type(value) is FunctionType and value.__code__ is not code
           for name, value, code in _EXTERNAL_HELPERS):
        raise PermissionError("selected phase descriptor native helper changed")


_DESCRIPTOR_VERIFY = SelectedPhaseAuthorityDescriptor.verify
_HELPERS = tuple((function.__name__, function, function.__code__) for function in (
    _fields, _native_owner_class, _plain_descriptor, _capture_reader, _ordinary_port,
    _native_method, _gate_binding, _identity_seal, _origin_seal,
    _function_seal, _verify_identity, _verify_function_seal, _verify_origin_seal,
    _descriptor_seal, _verify_selected_phase_tree, _verify_selected_phase_pair,
    _register, _issue_selected_phase_authority, selected_phase_authority,
    _inherit_selected_phase_authority, _require_descriptor_contracts))
_CLASS_SHAPES = tuple((cls, tuple(vars(cls).items())) for cls in (
    _FunctionBinding, _Origin, SelectedPhaseAuthorityDescriptor, _Registration))
_CLASS_CODES = tuple((function, function.__code__) for _, shape in _CLASS_SHAPES
    for _, value in shape for function in (
        (value.fget, value.fset, value.fdel) if type(value) is property else
        (value.__func__ if isinstance(value, (classmethod, staticmethod)) else value,))
    if type(function) is FunctionType)
_EXTERNAL_HELPERS = tuple((name, value, value.__code__ if type(value) is FunctionType else None)
    for name, value in (("_ReaderBinding", _ReaderBinding), ("_native_snapshot", _native_snapshot),
        ("_held_snapshot", _held_snapshot), ("_require_native_contracts", _require_native_contracts),
        ("_require_held_contracts", _require_held_contracts), ("_DESCRIPTOR_VERIFY", _DESCRIPTOR_VERIFY)))

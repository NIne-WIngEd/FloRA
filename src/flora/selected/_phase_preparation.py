"""Private material lifetime for the three actual phase preparation owners.

The dynamic binding admits only the actual issuer and its exact consumer. It
contains no permission or producer result. Every borrowed private read executes
independent lineage authority followed by the original owner metadata barrier.
"""
from contextvars import ContextVar
from threading import get_ident
from types import FunctionType, MethodType, SimpleNamespace, GetSetDescriptorType, MemberDescriptorType
import sys

from cognitive_kernel.experience import ExperienceEvent
from cognitive_kernel.contracts import ProductHostScope, ProvenanceReference

from ..comparison_run import HistorySnapshot, SourceMaterial
from .context_guard import (_native_context_snapshot, _context_snapshot_value,
    _revalidate_prepared, PreparedCurrentContext, CapturedClaimAuthority, CapturedStateAuthority,
    CapturedSourceAuthority, CapturedEpisodeAuthority, _require_shared_context_contracts)
from .context import StateRoute
from .source_closure import _ReaderBinding, _descriptor, _ABSENT
from .experiment_runtime import FloRAExperimentRuntime
from .judgment_lineage import NativeJudgmentLineageVerifier
from .phase_snapshots import XTDBPhaseSnapshotCustody, PreregisteredPhaseCaptureLineageVerifier
from .phase_routes import (SelectedPhaseRoute, SelectedBeforeProbeRoute,
    PhaseJudgmentRuntime, PhaseCaptureRuntime, FinalizedPhaseJudgmentRuntime,
    PreregisteredBeforeProbeRuntime, _QualifiedPhaseLineage, _QualifiedCapturePhaseLineage)


_ACTIVE = ContextVar("flora_actual_phase_preparation", default=None)
_ISSUED = {}
_VIEWS = {}
_ISSUERS = {"capture": XTDBPhaseSnapshotCustody.capture,
            "restore": SelectedPhaseRoute.__init__, "observe": SelectedPhaseRoute.observed_binding}
_ENTRY_POINTS = ((XTDBPhaseSnapshotCustody, "capture", _ISSUERS["capture"]),
    (SelectedPhaseRoute, "__init__", _ISSUERS["restore"]),
    (SelectedPhaseRoute, "observed_binding", _ISSUERS["observe"]),
    (SelectedBeforeProbeRoute, "__init__", SelectedBeforeProbeRoute.__init__))
_RUNTIMES = (FloRAExperimentRuntime, PhaseJudgmentRuntime, PhaseCaptureRuntime,
             FinalizedPhaseJudgmentRuntime, PreregisteredBeforeProbeRuntime)
_CONSUMERS = (NativeJudgmentLineageVerifier, PreregisteredPhaseCaptureLineageVerifier,
              _QualifiedPhaseLineage, _QualifiedCapturePhaseLineage)
_PREPARE = FloRAExperimentRuntime._prepare_current_context
_CONTEXT = FloRAExperimentRuntime._context
_RUNTIME_METHODS = {name: getattr(FloRAExperimentRuntime, name) for name in
                    ("_prepare_current_context", "_context", "_resolve", "_guarded_state_verifier")}
_LINEAGE_METHODS = {cls: {name: getattr(cls, name) for name in
                    ("context_lineage", "_claim", "_phase_request")} for cls in _CONSUMERS}
_HISTORY_LAYOUTS = {cls: tuple(cls.__dataclass_fields__) for cls in
    (HistorySnapshot, SourceMaterial, ExperienceEvent, ProductHostScope, ProvenanceReference,
     CapturedClaimAuthority, CapturedStateAuthority, CapturedSourceAuthority, CapturedEpisodeAuthority, StateRoute)}
# Named read ports and ownership edges exercised by capture, restoration and
# observation. This is a finite service graph, not recursive object inspection.
# Opaque ports retain their own mutable state; no permission answer is captured.
_OWNER_ROLES = (
    ("route", "snapshot history _captured_metadata _source_gate check_live guard_live observed_binding",
        (("custody", "archive"), ("runtime", "runtime"), ("lineage", "lineage"),
         ("history_authority", "history"), ("final_authority", "anchor"))),
    ("archive", "scope authority_namespace_id scope_digest run_id run_plan_sha256 preregistration_sha256 clock allow_unregistered_fixture_route capture identity_record _schema _slot_use _slot_capture _key _immutable intent _event_for_intent _insert _custody_record _verify_metadata metadata recover _sources_now _checked_history_authority _authorize_history _phase_metadata_gate authorize",
        (("runtime", "runtime"), ("connection", "sql"), ("preregistration", "anchor"),
         ("artifact_permissions", "permissions"), ("artifact_source_policy", "policy"))),
    ("runtime", "scope authority_namespace_id bindings clock vector graph context_integrity_domain maximum_context_sources _prepare_current_context _context _resolve _guarded_state_verifier",
        (("claims", "claims"), ("state", "state"), ("sources", "sources"), ("source_policy", "permissions"),
         ("log", "log"), ("objects", "objects"), ("references", "references"),
         ("original_references", "references"), ("private", "private"),
         ("context_policy", "policy"), ("state_approval_verifier", "approval"), ("artifacts", "artifacts"))),
    ("lineage", "run_plan_sha256 preregistration_sha256 snapshot_id case_id phase arm history_for invocation_id_for phase_receipt_for _phase_record _phase_update_receipt _phase_source_gate _preregistered_capture context_lineage _claim _phase_request",
        (("runtime", "runtime"), ("history_authority", "history"), ("preregistration", "anchor"))),
    ("history", "run_id history_metadata_domain maximum_history_sources authorize_history authorize_history_metadata bind_private_guard",
        (("custody", "comparison"), ("permissions", "permissions"), ("anchor", "anchor"), ("final_authority", "anchor"))),
    ("anchor", "spec plan native_plans _record scope authority_namespace_id run_id preregistration_sha256 final_plan_sha256 history_authority history_for authorize_slot_capture authorize_slot_use authorize_plan",
        (("store", "control"),)),
    ("control", "scope namespace run_id cohort_id recipe_id spec dependencies histories questions _spec_record _histories_record _questions_record _source_gates _controllers _metadata _active_slot_frame _committed_controls _stage _current _current_observations _check_current _guarded_comparison _canonical artifact_id control_kind _authorize_slot _authorize_slot_body _deny_evaluation_attempts _observation _verify_slot_table _final_payload _verify_update recover_control _repair_target _slot_metadata_frame historical_bindings",
        (("comparison", "comparison"), ("permissions", "permissions"), ("manifests", "manifests"),
         ("phase_custody", "archive"), ("anchor", "anchor"))),
    ("manifests", "scope namespace scope_digest experiment_id authorities lineage_key qualification_key lineage_key_sha256 qualification_key_sha256 anchor _id metadata _dependency _check_dependencies _check_gates _gate",
        (("connection", "sql"), ("local", "source_authority"))),
    ("source_authority", "authority_id binding gate read",
        (("registry", "sources"), ("permissions", "permissions"), ("log", "log"), ("objects", "objects"))),
    ("comparison", "scope authority_namespace_id scope_digest _key metadata metadata_selected preregistration_metadata require_final_authority _authority_fenced_copy read _read_authorized recover_history load_recorded",
        (("connection", "sql"), ("registry", "sources"), ("log", "log"), ("objects", "objects"),
         ("raw_custody", "raw_custody"), ("_physical_custody", "comparison"))),
    ("raw_custody", "read", (("registry", "sources"), ("objects", "objects"))),
    ("policy", "purpose allow_event allow_claim allow_state",
        (("claims", "claims"), ("state", "state"), ("registry", "sources"), ("permissions", "permissions"), ("log", "log"))),
    ("permissions", "scope authority_namespace_id scope_digest permits current_action _key _fetch _decode _stored_action _head",
        (("connection", "sql"), ("registry", "sources"))),
    ("claims", "scope authority_namespace_id scope_digest _pins _row_id _fetch_record _check_claim load_current current_history load_version load_evidence_relation",
        (("connection", "sql"), ("_live", "claims"))),
    ("state", "scope authority_namespace_id scope_digest _pins _version_id _head_id _fetch _check_sources _check_episode_sources _read_version _check_approval read_active _history _history_key _immutable _rollback_id_key _rollback_key",
        (("connection", "sql"), ("registry", "sources"), ("policy", "permissions"), ("episodes", "episodes"), ("_live", "state"))),
    ("episodes", "scope authority_namespace_id scope_digest _pins _head _fetch _immutable _candidate_metadata _artifact_metadata _source_lineage _accept_snapshot _verify_external _check_sources _candidate_read_gate current_lineage read_accepted _key _receipt _request_event",
        (("connection", "sql"), ("registry", "sources"), ("policy", "permissions"), ("custody", "personal"), ("verifier", "episode_verifier"), ("guard", "development_guard"), ("_live", "episodes"))),
    ("development_guard", "scope authority_namespace_id check", (("registry", "sources"), ("policy", "permissions"))),
    ("episode_verifier", "qualified_formation authenticated_adjudication", ()),
    ("sources", "scope authority_namespace_id scope_digest _key _fetch _decode lookup lookup_commitment raw_metadata raw_reference get", (("connection", "sql"),)),
    ("artifacts", "scope authority_namespace_id scope_digest _pins _key _fetch _seal resolve_current_for_runtime",
        (("connection", "sql"), ("objects", "objects"), ("_live", "artifacts"))),
    ("references", "get", (("durable", "references"), ("runtime_custody", "private"),
        ("custody", "personal"), ("originals", "sources"))),
    ("private", "scope_digest records raw_refs _key _seal _fetch raw_reference read",
        (("runtime", "runtime"), ("connection", "sql"))),
    ("personal", "scope authority_namespace_id scope_digest _key _fetch _scope _artifact metadata raw_reference read _validate_contract",
        (("connection", "sql"),)),
    ("approval", "scope key owner_public_key authenticated_approval _verify", (("proofs", "proofs"),)),
    ("proofs", "get owner_public_key", (("custody", "personal"), ("log", "log"), ("objects", "objects"))),
    ("log", "scope stream replay replay_committed lookup_committed append _codec_owner _remember_envelope", (("client", "events"),)),
    ("log_wrapper", "append check", (("log", "log"),)),
    ("events", "get_stream read_stream append_to_stream", ()),
    ("objects", "scope namespace _key get put recover_reference _identity", (("backend", "backend"),)),
    ("object_wrapper", "get put recover_reference __copy__ backend _check source_authorizer _phase_source_authorizer check _installed_check revalidate",
        (("objects", "objects"),)),
    ("backend", "get_object put_if_absent", ()),
    ("backend_wrapper", "get_object put_if_absent check revalidate", (("backend", "backend"),)),
    ("sql", "execute owner_thread_id read_timeout_ms", (("_ReadOnlyNativeSQLConnection__connection", "sql"),)),
    ("binding", "checkpoint_path", (("codec", "codec"), ("adapter", "adapter"),
        ("qualification_verifier", "qualifier"), ("execution_verifier", "execution"))),
    ("qualifier", "verify verify_phase_snapshot", ()),
    ("codec", "input_contract_id input_contract_sha256 output_contract_id output_contract_sha256 formation_input decode_formation encode_formation_output judgment_frame validate_identity_decision", ()),
    ("adapter", "adapter_id execution_location invoke", ()),
    ("execution", "verified_execution", ()),
    ("prepared", "context claims state log objects references policy approval_verifier_factory authority_guard claim_authorities state_authorities source_authorities episode_authorities _context_record _selected_context_snapshot _bindings_current _phase metadata_current _verify_authorities _metadata_fence _source_fence revalidate", ()),
)


# Only these actual factories retain native controllers in callbacks. Each
# edge names a lexical variable in that exact factory's nested code; opaque
# callbacks are never traversed or treated as evidence of an owner's rights.
_CALLBACK_FACTORIES = (
    ("phase_snapshots", "XTDBPhaseSnapshotCustody", "capture", (
        ("personal_gate", (("self", "archive"),)),
        ("capture_guard", (("self", "archive"), ("history_authority", "history"), ("personal_gate", "callback"))),
        ("combined_capture_guard", (("self", "archive"), ("before_authority", "history"), ("current_capture_guard", "callback"))),
        ("receipt_for", (("lineage", "lineage"),)),
        ("write_gate", (("self", "archive"), ("capture_guard", "callback"))),
    )),
    ("phase_snapshots", "XTDBPhaseSnapshotCustody", "authorize", (
        ("metadata_gate", (("self", "archive"),)),
    )),
    ("phase_routes", "SelectedPhaseRoute", "__init__", (
        ("source_gate", (("custody", "archive"), ("history_authority", "history"), ("final_authority", "anchor"))),
        ("<lambda>", (("custody", "archive"),)),
        ("receipt_for", ()), ("history_for", ()),
    )),
    ("phase_routes", None, "derive_preregistered_ablation_runtime", (
        ("<lambda>", (("authority_guard", "callback"),)),
    )),
    ("experiment_preregistration", "PreregisteredHistoryAuthority", "bind_private_guard", (
        ("check", (("self", "history"), ("source_gate", "callback"))),
    )),
    ("experiment_preregistration", "XTDBExperimentPreregistrationCustody", "recover_control", (
        ("check", (("self", "control"),)),
    )),
    ("experiment_preregistration", "XTDBExperimentPreregistrationCustody", "register_original_inputs", (
        ("check", (("self", "control"),)),
    )),
    ("comparison_custody", "XTDBComparisonCustody", "_read_authorized", (
        ("current", (("self", "comparison"), ("permissions", "permissions"))),
    )),
)
_BOUND_CALLBACK_OWNERS = (
    ("phase_snapshots", "XTDBPhaseSnapshotCustody", "archive", ()),
    ("phase_routes", "SelectedPhaseRoute", "route", ("guard_live", "check_live")),
    ("experiment_preregistration", "XTDBExperimentPreregistrationCustody", "control", ("_current",)),
    ("experiment_preregistration", "RegisteredExperimentPreregistration", "anchor", ()),
    ("experiment_preregistration", "RegisteredExperimentFinalBinding", "anchor", ()),
    ("experiment_preregistration", "PreregisteredHistoryAuthority", "history", ()),
    ("personal_artifact_custody", "_SourceAuthorizedObjectReads", "objects", ("_check",)),
)


def _native_origin(module, class_name, name):
    for owner, original_name, function, code in vars(module).get("_PHASE_NATIVE_ORIGINS", ()):
        if original_name != name or (None if owner is None else owner.__name__) != class_name:
            continue
        if owner is not None and vars(module).get(class_name) is not owner:
            return None
        namespace = module if owner is None else owner
        if vars(namespace).get(name) is function and function.__code__ is code:
            return namespace, function, code
    return None


def _native_callback_specs():
    from types import CodeType
    specifications = {}
    for module_name, class_name, method_name, children in _CALLBACK_FACTORIES:
        module = sys.modules.get(__package__ + "." + module_name)
        if module is None:
            continue  # No instance from this platform-owned factory is loaded.
        origin = _native_origin(module, class_name, method_name)
        if origin is None:
            return None
        factory_owner, factory, code = origin
        for child_name, edges in children:
            codes = tuple(value for value in code.co_consts
                          if type(value) is CodeType and value.co_name == child_name)
            if len(codes) != 1 or any(name not in codes[0].co_freevars for name, _ in edges):
                return None
            specifications[id(codes[0])] = (factory_owner, method_name, factory, code, codes[0], edges)
    return specifications


def _bound_callback_role(callback):
    for module_name, class_name, role, names in _BOUND_CALLBACK_OWNERS:
        module = sys.modules.get(__package__ + "." + module_name)
        cls = None if module is None else vars(module).get(class_name)
        if cls is not None and cls in type(callback.__self__).__mro__:
            for name in names:
                origin = _native_origin(module, class_name, name)
                if origin is not None and callback.__func__ is origin[1]:
                    return role, name, origin
            return False  # A known native owner does not bless an arbitrary method.
    return None


class _NamespaceBinding:
    """Exact SimpleNamespace port; its member-descriptor dictionary is native.

    Only the named port identity is sealed. Other state (e.g. a callback's call
    counter) remains opaque and live. This does not change source_closure rules.
    """
    def __init__(self, owner, name):
        self.owner, self.name = owner, name
        self.dictionary = object.__getattribute__(owner, "__dict__")
        self.instance_value = self.dictionary.get(name, _ABSENT)
        self.descriptor = None

    def verify(self):
        if (type(self.owner) is not SimpleNamespace
                or object.__getattribute__(self.owner, "__dict__") is not self.dictionary
                or self.dictionary.get(self.name, _ABSENT) is not self.instance_value):
            raise PermissionError("phase opaque port binding changed")


def _port_dictionary(owner, names):
    # Admission is completed without invoking any owner or descriptor. An
    # unsupported representation takes the original path before preparation.
    cls = type(owner)
    if type(cls) is not type:
        return None
    if cls is not SimpleNamespace and _descriptor(cls, "__getattribute__") is not object.__getattribute__:
        return None
    descriptor = _descriptor(cls, "__dict__")
    if cls is not SimpleNamespace and type(descriptor) is not GetSetDescriptorType:
        return None
    dictionary = object.__getattribute__(owner, "__dict__")
    if type(dictionary) is not dict or any(type(key) is not str for key in dictionary):
        return None
    if any(type(_descriptor(cls, name)) is MemberDescriptorType for name in names):
        return None
    return dictionary


def _port_readers(owner, names):
    binding = _NamespaceBinding if type(owner) is SimpleNamespace else _ReaderBinding.capture
    return tuple(binding(owner, name) for name in dict.fromkeys((*names, "__getattribute__", "__getattr__")))


def _owner_map(issuer, kind, runtime, consumer, guard):
    from .experiment_runtime import _AuthorizedRuntimeReads, _AuthorizedRuntimeBackend, _RuntimeReferences
    from .personal_artifact_custody import DurablePersonalReferences
    from .personal_artifact_custody import _SourceAuthorizedObjectReads, _SourceAuthorizedBackend
    from .phase_snapshots import PhaseAuthorizedObjectReads
    from .experiment_manifests import _GuardedObjects, _GuardedBackend
    object_wrappers = (_AuthorizedRuntimeReads, _SourceAuthorizedObjectReads, PhaseAuthorizedObjectReads, _GuardedObjects)
    backend_wrappers = (_AuthorizedRuntimeBackend, _SourceAuthorizedBackend, _GuardedBackend)
    # The coordinator module owns the real preregistered log facade. Do not
    # import its worker/platform dependencies just to inspect an absent owner.
    coordinator = sys.modules.get(__package__ + ".experiment_coordinator")
    log_wrapper = None if coordinator is None else vars(coordinator).get("_GuardedLog")
    callback_specs = _native_callback_specs()
    if callback_specs is None:
        return None
    roles = {role: (names.split(), edges) for role, names, edges in _OWNER_ROLES}
    pending = [(issuer, "archive" if kind == "capture" else "route"), (runtime, "runtime"), (consumer, "lineage"), (guard, "callback")]
    owners, readers, maps, implementations, seen = [], [], [], {}, set()
    native_callbacks, callback_factories = [], {}
    while pending:
        owner, role = pending.pop()
        if owner is None or (id(owner), role) in seen:
            continue
        seen.add((id(owner), role))
        if role == "callback":
            function = owner.__func__ if type(owner) is MethodType else owner
            if type(owner) is MethodType:
                bound_role = _bound_callback_role(owner)
                if bound_role is False:
                    return None
                if bound_role is not None:
                    bound_role, name, (factory_owner, factory, code) = bound_role
                    pending.append((owner.__self__, bound_role))
                    native_callbacks.append((owner, _callback_state(owner, seal_contents=True)))
                    callback_factories[(factory_owner, name)] = (factory, code)
                    continue
            if type(function) is FunctionType and id(function.__code__) in callback_specs:
                factory_owner, name, factory, code, child_code, edges = callback_specs[id(function.__code__)]
                if function.__code__ is not child_code or function.__globals__ is not factory.__globals__:
                    return None
                cells = dict(zip(function.__code__.co_freevars, function.__closure__ or ()))
                if len(cells) != len(function.__code__.co_freevars):
                    return None
                native_callbacks.append((function, _callback_state(function, seal_contents=True)))
                callback_factories[(factory_owner, name)] = (factory, code)
                pending.extend((cells[name].cell_contents, child_role) for name, child_role in edges)
                continue
            # New native controller closures require their own named edges.
            # External/user callbacks keep their original opaque live state.
            module_name = function.__module__ if type(function) is FunctionType else type(function).__module__
            if type(module_name) is not str or module_name.startswith(__package__ + "."):
                return None
            continue
        # Proof dictionaries are live proof data, not a service graph. The
        # parent lookup identity is sealed and authentication still runs.
        if role == "proofs" and type(owner) is dict:
            continue
        if role == "references" and type(owner) not in (_RuntimeReferences, DurablePersonalReferences):
            return None
        if role == "log" and type(owner) is log_wrapper:
            role = "log_wrapper"
        elif role == "objects" and type(owner) in object_wrappers:
            role = "object_wrapper"
        elif role == "backend" and type(owner) in backend_wrappers:
            role = "backend_wrapper"
        elif role in ("objects", "backend", "log") and _descriptor(type(owner), "__getattr__") is not _ABSENT:
            return None  # An unknown facade needs its original construction.
        names, edges = roles[role]
        names = tuple(dict.fromkeys((*names, *(name for name, _ in edges))))
        dictionary = _port_dictionary(owner, names)
        if dictionary is None:
            return None
        owners.append(owner)
        readers.extend(_port_readers(owner, names))
        # Explicit ports may dispatch through super(); seal each implementation
        # of those named ports, including a hidden native base implementation.
        for name in (*names, "__getattribute__", "__getattr__"):
            for cls in type(owner).__mro__:
                if name in vars(cls):
                    value = vars(cls)[name]
                    implementations[(cls, name)] = (value, _callback_state(value))
        for name, child_role in edges:
            # Ownership edges are native stored references, never properties.
            if name not in dictionary and _descriptor(type(owner), name) is not _ABSENT:
                return None
            pending.append((dictionary.get(name), child_role))
        callback_ports = ("phase_receipt_for", "history_for", "_phase_source_gate") if role == "lineage" else (
            ("_source_gate",) if role == "route" else
            ("source_authorizer", "_phase_source_authorizer", "check", "_installed_check", "revalidate")
            if role in ("object_wrapper", "backend_wrapper", "log_wrapper") else ())
        pending.extend((dictionary.get(name), "callback") for name in callback_ports)
        collection = "bindings" if role == "runtime" else "authorities" if role == "manifests" else None
        if collection is not None:
            values = dictionary[collection]
            if type(values) is not dict or any(type(key) is not str for key in values):
                return None
            maps.append((values, tuple(values.items())))
            pending.extend((value, "binding" if role == "runtime" else "source_authority") for value in values.values())
    return tuple(owners), tuple(readers), tuple(maps), tuple((cls, name, value, state)
        for (cls, name), (value, state) in implementations.items()), tuple(native_callbacks), tuple(
            (owner, name, factory, code) for (owner, name), (factory, code) in callback_factories.items())


def _history_snapshot(value):
    cls = type(value)
    if type(cls) is not type:
        raise PermissionError("phase held history contains a custom metadata class")
    if value is None or cls in (str, bytes, int, bool, float):
        return cls, value
    if cls is tuple:
        return cls, tuple(_history_snapshot(item) for item in value)
    if cls not in _HISTORY_LAYOUTS:
        raise PermissionError("phase held history is not native material")
    fields = object.__getattribute__(value, "__dict__")
    if set(fields) != set(_HISTORY_LAYOUTS[cls]):
        raise PermissionError("phase held history shape changed")
    return cls, tuple((name, _history_snapshot(fields[name])) for name in _HISTORY_LAYOUTS[cls])


def _callback_state(value, *, seal_contents=False):
    if type(value) is MethodType:
        return id(value.__self__), _callback_state(value.__func__, seal_contents=seal_contents)
    if type(value) is FunctionType:
        return (id(value.__code__), id(value.__defaults__), id(value.__kwdefaults__),
                tuple((id(cell), id(cell.cell_contents) if seal_contents else None)
                      for cell in value.__closure__ or ()))
    if type(value) in (staticmethod, classmethod):
        return _callback_state(value.__func__)
    if type(value) is property:
        return tuple(_callback_state(function) for function in (value.fget, value.fset, value.fdel))
    return id(value)


class _PhasePreparation:
    def __init__(self, *, issuer, kind, runtime, consumer, plan, history, case_id, phase, identity, guard):
        self.issuer, self.kind, self.runtime, self.consumer = issuer, kind, runtime, consumer
        self.plan, self.history, self.case_id, self.phase = plan, history, case_id, phase
        self.identity, self.guard, self.thread = identity, guard, get_ident()
        self.prepared, self.context, self.token = None, None, None
        self.views = {}
        self.live = False
        self.native = (type(runtime) in _RUNTIMES and type(consumer) in _CONSUMERS
            and type(history) is HistorySnapshot
            and all(getattr(getattr(runtime, name), "__func__", None) is method
                    for name, method in _RUNTIME_METHODS.items())
            and all(getattr(getattr(consumer, name), "__func__", None) is method
                    for name, method in _LINEAGE_METHODS[type(consumer)].items()))

    def __enter__(self):
        _check_caller(self.issuer, self.kind, sys._getframe(1))
        _issued(self)
        try:
            return self._enter()
        except BaseException:
            self.live = False
            _ISSUED.pop(id(self), None)
            raise

    def _enter(self):
        _issued(self)
        caller = sys._getframe(1)
        if caller.f_code is not _PhasePreparation.__enter__.__code__ or caller.f_locals.get("self") is not self:
            raise PermissionError("phase preparation lacks its actual owner entry")
        if self.thread != get_ident() or self.live or self.token is not None:
            raise PermissionError("phase preparation lifetime cannot be reused")
        mapped = _owner_map(self.issuer, self.kind, self.runtime, self.consumer, self.guard) if self.native else None
        if mapped is None:
            self.native = False
            self.context = self.runtime._context(self.plan, authority_guard=self.guard)
            return self
        runtime = self.runtime
        owners, self.readers, self.service_maps, self.implementations, native_callbacks, self.callback_factories = mapped
        self.material = _history_snapshot(self.history)
        self.plan_material = _context_snapshot_value(self.plan, set())
        self.pins = tuple((owner, name, _context_snapshot_value(vars(owner)[name], set()))
            for owner in owners if owner is not None for name in ("_pins", "_phase_record", "_captured_metadata")
            if name in getattr(owner, "__dict__", {}))
        self.role_bindings = tuple(runtime.bindings.items())
        self.callback = _ReaderBinding.capture(self, "guard")
        self.callbacks = tuple((value, _callback_state(value)) for value in
            (self.guard, *(reader.instance_value for reader in self.readers),
             *(reader.descriptor for reader in self.readers)))
        # Opaque authority callbacks may keep counters or live permission state
        # in their own closures. Seal identities/code, never those decisions.
        # Native owner/preparer closures additionally retain exact controllers.
        self.bound_callbacks = native_callbacks + ((self.guard, _callback_state(self.guard, seal_contents=True)),)
        self._check_material()
        self.prepared = runtime._prepare_current_context(self.plan, authority_guard=self.guard)
        if type(self.prepared) is not PreparedCurrentContext:
            raise PermissionError("phase preparation lost native prepared material")
        self._check_material()
        self.context = self.prepared.context
        self.content = _native_context_snapshot(self.context)
        self.authorities = _history_snapshot(tuple(getattr(self.prepared, name) for name in
            ("claim_authorities", "state_authorities", "source_authorities", "episode_authorities")))
        prepared_readers = _port_readers(self.prepared, next(names.split() for role, names, _ in _OWNER_ROLES if role == "prepared"))
        self.readers += prepared_readers
        self.callbacks += tuple((value, _callback_state(value)) for reader in prepared_readers
            for value in (reader.instance_value, reader.descriptor))
        self.bound_callbacks += tuple((value, _callback_state(value, seal_contents=True)) for value in
            (self.prepared.approval_verifier_factory, self.prepared.authority_guard, self.prepared._bindings_current))
        self.live = True
        self.token = _ACTIVE.set(self)
        _ISSUED[id(self)] = (self, tuple(vars(self).items()))
        return self

    def _check_material(self):
        for reader in self.readers:
            reader.verify()
        self.callback.verify()
        if any(vars(owner).get(name) is not factory or factory.__code__ is not code
               for owner, name, factory, code in self.callback_factories):
            raise PermissionError("phase native callback factory changed")
        if any(vars(cls).get(name, _ABSENT) is not value or _callback_state(value) != state
               for cls, name, value, state in self.implementations):
            raise PermissionError("phase mapped port implementation changed")
        if (self.thread != get_ident() or _history_snapshot(self.history) != self.material
                or any(_callback_state(value) != state for value, state in self.callbacks)
                or any(_callback_state(value, seal_contents=True) != state for value, state in self.bound_callbacks)
                or _context_snapshot_value(self.plan, set()) != self.plan_material
                or any(len(values) != len(items) or any(values.get(key) is not value for key, value in items)
                       for values, items in self.service_maps)
                or len(self.runtime.bindings) != len(self.role_bindings)
                or any(self.runtime.bindings.get(role) is not value for role, value in self.role_bindings)
                or any(_context_snapshot_value(vars(owner).get(name), set()) != value
                       for owner, name, value in self.pins)):
            raise PermissionError("phase preparation sealed material or services changed")

    def check(self):
        _issued(self)
        if not self.live or _ACTIVE.get() is not self:
            raise PermissionError("phase preparation is expired, copied or outside its owner")
        self._check_material()
        if self.prepared.context is not self.context or _native_context_snapshot(self.context) != self.content:
            raise PermissionError("phase prepared context changed")
        if _history_snapshot(tuple(getattr(self.prepared, name) for name in
                ("claim_authorities", "state_authorities", "source_authorities", "episode_authorities"))) != self.authorities:
            raise PermissionError("phase prepared authority material changed")

    def __exit__(self, *exception):
        try:
            if self.native and not exception[0]:
                self.check()
        finally:
            self.live = False
            for identity in self.views:
                _VIEWS.pop(identity, None)
            self.views.clear()
            _ISSUED.pop(id(self), None)
            if self.token is not None:
                _ACTIVE.reset(self.token)
        return False


def _check_caller(issuer, kind, frame):
    _contracts()
    expected = _ISSUERS.get(kind)
    method_name = {"capture": "capture", "restore": "__init__", "observe": "observed_binding"}.get(kind)
    allowed = ((XTDBPhaseSnapshotCustody,) if kind == "capture"
               else (SelectedPhaseRoute, SelectedBeforeProbeRoute))
    if (type(issuer) not in allowed or expected is None or frame.f_code is not expected.__code__
            or frame.f_locals.get("self") is not issuer
            or getattr(getattr(issuer, method_name), "__func__", None) is not (
                SelectedBeforeProbeRoute.__init__ if kind == "restore" and type(issuer) is SelectedBeforeProbeRoute
                else expected)):
        raise PermissionError("phase material was not issued by its actual operation owner")


def _phase_preparation(**kwargs):
    _check_caller(kwargs["issuer"], kwargs["kind"], sys._getframe(1))
    operation = _PhasePreparation(**kwargs)
    _ISSUED[id(operation)] = (operation, tuple(vars(operation).items()))
    return operation


def _issued(operation):
    _contracts()
    record = _ISSUED.get(id(operation))
    if (record is None or record[0] is not operation or len(vars(operation)) != len(record[1])
            or any(vars(operation).get(name) is not value for name, value in record[1])):
        raise PermissionError("phase preparation holder is forged, copied, expired or changed")


class _LineageUse:
    def __init__(self, operation, guard):
        self.operation, self.guard = operation, guard

    def _check(self):
        _contracts()
        record = _VIEWS.get(id(self))
        if (record is None or record[0] is not self or self.operation is not record[1]
                or self.guard is not record[2] or _callback_state(self.guard, seal_contents=True) != record[3]
                or set(vars(self)) != {"operation", "guard"}):
            raise PermissionError("phase lineage use is forged or changed")
        self.operation.check()

    @property
    def context(self):
        self._check()
        return self.operation.context

    def metadata_current(self):
        self._check()
        self.guard()
        self._check()
        self.operation.prepared.metadata_current()
        # The owner terminal observation is last; only pure bindings follow.
        self._check()

    def revalidate(self):
        self._check()
        _revalidate_prepared(self.operation.prepared, self)
        self._check()


def _borrow_lineage(consumer, *, case_id, phase, history, context, guard):
    operation = _ACTIVE.get()
    if operation is None:
        return None
    operation.check()
    caller = sys._getframe(1)
    if (caller.f_code is not NativeJudgmentLineageVerifier.context_lineage.__code__
            or caller.f_locals.get("self") is not consumer or caller.f_locals.get("guard") is not guard):
        raise PermissionError("phase use was not requested by its actual native lineage consumer")
    if consumer is not operation.consumer:
        # An unrelated standalone call has no handoff admission. It retains
        # its original independent preparation, even inside an opaque callback.
        return None
    if (consumer.runtime is not operation.runtime
            or history is not operation.history or (case_id, phase) != (operation.case_id, operation.phase)
            or context is not operation.context):
        raise PermissionError("phase lineage use crosses its exact owner or material")
    use = _LineageUse(operation, guard)
    operation.views[id(use)] = (use, guard)
    _VIEWS[id(use)] = (use, operation, guard, _callback_state(guard, seal_contents=True))
    use.metadata_current()
    return use


def _validated_phase_barrier(prepared, use):
    if type(use) is not _LineageUse:
        raise PermissionError("owner revalidation needs an issued lineage use")
    use._check()
    if use.operation.prepared is not prepared:
        raise PermissionError("owner revalidation crosses prepared material")
    return use.metadata_current


def _current_lineage_use(consumer):
    operation = _ACTIVE.get()
    if operation is None:
        return None
    operation.check()
    if operation.consumer is not consumer:
        return None
    return next(reversed(operation.views.values()))[0] if operation.views else None


def _finish_lineage_use(consumer):
    use = _current_lineage_use(consumer)
    if use is not None:
        use.revalidate()


def _contracts():
    _require_shared_context_contracts()
    if (_OWNER_ROLES is not _SEALED_OWNER_ROLES or _CALLBACK_FACTORIES is not _SEALED_CALLBACK_FACTORIES
            or _BOUND_CALLBACK_OWNERS is not _SEALED_BOUND_CALLBACK_OWNERS):
        raise PermissionError("phase owner mapping changed")
    for cls, name, function in _ENTRY_POINTS:
        if vars(cls).get(name) is not function:
            raise PermissionError("phase preparation issuer implementation changed")
    for function, code in _CODES:
        if function.__code__ is not code:
            raise PermissionError("phase preparation implementation changed")
    for cls, shape in _SHAPES:
        current = vars(cls)
        if any(current.get(name) is not value for name, value in shape):
            raise PermissionError("phase preparation implementation binding changed")
    for name, value in _HELPERS:
        if globals().get(name) is not value:
            raise PermissionError("phase preparation helper changed")


_SEALED_OWNER_ROLES = _OWNER_ROLES
_SEALED_CALLBACK_FACTORIES = _CALLBACK_FACTORIES
_SEALED_BOUND_CALLBACK_OWNERS = _BOUND_CALLBACK_OWNERS
_SHAPES = tuple((cls, tuple(vars(cls).items())) for cls in
    (_PhasePreparation, _LineageUse, _NamespaceBinding, _ReaderBinding, PreparedCurrentContext, *_HISTORY_LAYOUTS, *_CONSUMERS))
_CODES = tuple((function, function.__code__) for _, shape in _SHAPES for _, value in shape
    for function in ((value.__func__,) if type(value) in (classmethod, staticmethod)
                     else (value.fget, value.fset, value.fdel) if type(value) is property else (value,))
    if type(function) is FunctionType)
_HELPERS = tuple((name, value) for name, value in tuple(globals().items())
                 if type(value) is FunctionType)
_CODES += tuple((value, value.__code__) for _, value in _HELPERS)
_CODES += tuple((value, value.__code__) for value in (_PREPARE, _CONTEXT))
_CODES += tuple((value, value.__code__) for value in _RUNTIME_METHODS.values())
_CODES += tuple((value, value.__code__) for methods in _LINEAGE_METHODS.values() for value in methods.values())
_CODES += tuple((value, value.__code__) for _, _, value in _ENTRY_POINTS)

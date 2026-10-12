"""Terminal authority on actual v2 wrappers over fictional row/log ports.

These component regressions do not qualify a physical backend, latency,
learning, or an end-to-end comparison. BEFORE contains both original inputs
that formed the existing Claim; one fresh synthetic correction is AFTER-only.
The H intervention changes the metadata decision, not signed permission rows.
The independent C intervention changes the runtime fixture's live permission.

The capture control and H oracle retain the completed source-bound diagnostic:
denial at the final slot must precede entry into the archive's next Claim read.
Standalone C and qualified-source cases forbid returning a lineage after their
last callback withdraws authority. C may read metadata to establish refusal.
"""
import json
import sys
from threading import get_ident
import unittest
from unittest.mock import patch

from cognitive_kernel.canonical import canonical_sha256
from cognitive_kernel.contracts import ProvenanceReference
from cognitive_kernel.experience import ExperienceEvent
from flora.comparison_run import HistorySnapshot, SourceMaterial
from flora.selected import _phase_preparation as preparation
from flora.selected.context_guard import PreparedCurrentContext
from flora.selected.formation_context import register_experience_source
from flora.selected.judgment_lineage import NativeJudgmentLineageVerifier
from flora.selected.phase_routes import _QualifiedCapturePhaseLineage, _QualifiedUpdateProof
from flora.selected.phase_snapshots import (
    PreregisteredPhaseCaptureLineageVerifier, XTDBPhaseSnapshotCustody,
)

# Compose the fixture through its module. Importing/inheriting its TestCase
# would accidentally collect its existing cases again in this module.
import test_phase_callback_owners as callback_fixture
import test_phase_snapshots as phase_fixture


class _ProtectedClaimRead(AssertionError):
    """Stop before the original Claim method after terminal H denial."""


class PhaseTerminalCompletionTest(unittest.TestCase):
    def setUp(self):
        self.fixture = callback_fixture.PreregisteredCallbackOwnerTest(
            "test_original_history_anchor_replacement_refuses_before_effects")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture.f

    def _registered_before(self, label):
        support, f = self.fixture.support, self.f
        originals = tuple(support.original_events)
        before = support.histories[("case-one", "after")]
        plaintext = b"Fictional later correction; this test checks authority closure only."
        raw = f.objects.put(plaintext)
        event = ExperienceEvent.create(event_type="correction", scope=f.scope,
            occurred_at=f._clock(), content_digest=raw.plaintext_sha256,
            provenance=ProvenanceReference.create(provenance_type="generated_reconstruction",
                source_reference_ids=(originals[0].event_id,),
                derivation_activity_id="phase-terminal-completion-" + label,
                responsible_component="synthetic-authority-fixture"),
            retention_class="ordinary_experience", storage_tier="raw_buffer",
            parent_event_ids=(originals[0].event_id,), payload_reference=raw.object_id)
        f.log.append(event, expected_revision=len(f.log.replay()) - 1)
        register_experience_source(event_id=event.event_id, raw=raw,
            registry=f.registry, log=f.log, objects=f.objects,
            role="generated_reconstruction", modality="text")
        support.histories = {
            ("case-one", "before"): before,
            ("case-one", "after"): HistorySnapshot(f.scope,
                before.sources + (SourceMaterial(event, plaintext),)),
        }
        # The reusable registration helper declares index 1 as the intervention.
        # Keep every Claim input in BEFORE and the cohort, while declaring only
        # the fresh AFTER correction as the intervention.
        support.original_events = (originals[0], event, *originals[1:])
        self.fixture.custody.run_id = "phase-terminal-completion-" + label
        authority = self.fixture.registered_history_owner()
        anchor, grants = authority.anchor, self.fixture.history_grants
        self.assertNotIn(event.event_id, before.event_ids)
        self.assertEqual(anchor.spec.protocol.cases[0].intervention_event_id, event.event_id)
        self.assertEqual(anchor.history_for("case-one", "before"), before)
        for original in before.sources:
            grants.grant_closure(original.event.event_id, "personal_judgment")
        archive = XTDBPhaseSnapshotCustody(runtime=f.runtime, run_id=anchor.run_id,
            preregistration=anchor, clock=f._clock, artifact_permissions=grants.policy)
        anchor.store.bind_phase_custody(archive)
        slot = next(slot for slot in anchor.spec.slots
            if slot.phase == "before" and slot.arm == "flora_full")
        anchor.store.bind_historical_bindings(snapshot_id=slot.snapshot_id,
            bindings=dict(f.runtime.bindings))
        actual = PreregisteredPhaseCaptureLineageVerifier(runtime=f.runtime,
            preregistration=anchor, snapshot_id=slot.snapshot_id,
            case_id=slot.case_id, phase=slot.phase, arm=slot.arm,
            history_for=anchor.history_for,
            phase_receipt_for=support.verifier.phase_receipt_for)
        self.assertIs(archive.preregistration, anchor)
        self.assertIs(type(actual), PreregisteredPhaseCaptureLineageVerifier)
        return archive, anchor, authority, actual, slot, before

    @staticmethod
    def _withdrawable_history(authority, allowed):
        class WithdrawableHistory(type(authority)):
            def authorize_history_metadata(inner, **kwargs):
                return allowed[0] and super().authorize_history_metadata(**kwargs)
        independent = object.__new__(WithdrawableHistory)
        independent.__dict__.update(authority.__dict__)
        return independent

    @staticmethod
    def _terminal_frame(code, marker, consumer):
        frame = sys._getframe(1)
        while frame is not None:
            if (frame.f_code is code and marker in frame.f_locals
                    and frame.f_locals.get("self") is consumer):
                return frame
            frame = frame.f_back
        return None

    @staticmethod
    def _capture_terminal_frame(original):
        """Locate custody's exact copied consumer, not an arbitrary lookalike."""
        wrapper_code = PreregisteredPhaseCaptureLineageVerifier.context_lineage.__code__
        capture_code = XTDBPhaseSnapshotCustody.capture.__code__
        frame = sys._getframe(1)
        while frame is not None:
            if frame.f_code is wrapper_code and "actual" in frame.f_locals:
                consumer = frame.f_locals.get("self")
                if (type(consumer) is type(original)
                        and consumer.runtime is original.runtime
                        and consumer.preregistration is original.preregistration
                        and consumer.history_authority.anchor is original.history_authority.anchor
                        and consumer.history_authority.permissions is original.history_authority.permissions
                        and type(consumer.history_authority) is type(original.history_authority)
                        and all(getattr(consumer, name) == getattr(original, name)
                            for name in ("snapshot_id", "case_id", "phase", "arm", "preregistration_sha256"))):
                    caller = frame.f_back
                    while caller is not None:
                        if (caller.f_code is capture_code
                                and caller.f_locals.get("lineage") is original
                                and caller.f_locals.get("capturing") is consumer
                                and caller.f_locals.get("history_authority") is consumer.history_authority
                                and caller.f_locals.get("capture_runtime") is consumer.runtime
                                and caller.f_locals.get("history") is frame.f_locals["kwargs"]["history"]):
                            return frame
                        caller = caller.f_back
            frame = frame.f_back
        return None

    @staticmethod
    def _observe(observation, consumer):
        active = preparation._ACTIVE.get()
        observation.update(callback_reached=True,
            active_preparation=active is not None,
            native_preparation=None if active is None else active.native,
            exact_consumer=None if active is None else active.consumer is consumer,
            issued_use_count=0 if active is None else len(active.views))

    def _terminal_slot(self, anchor, consumer, observation, intervention, *, capture_copy=False):
        original = anchor.authorize_slot_use
        code = PreregisteredPhaseCaptureLineageVerifier.context_lineage.__code__
        def final_slot(**kwargs):
            value = original(**kwargs)
            if not observation["callback_reached"]:
                frame = (self._capture_terminal_frame(consumer) if capture_copy
                    else self._terminal_frame(code, "actual", consumer))
                if frame is not None:
                    reached = frame.f_locals["self"]
                    self._observe(observation, reached)
                    if capture_copy:
                        observation.update(consumer_provenance="actual_custody_capture_copy",
                            capture_copy_observed=True,
                            consumer_is_original=reached is consumer,
                            custody_history_authority_exact=True,
                            shared_runtime=True, shared_preregistration=True,
                            shared_history_anchor_and_permissions=True, exact_slot=True)
                        intervention(frame)
                    else:
                        intervention()
            return value
        return final_slot

    @staticmethod
    def _observation(label):
        return {"schema": "flora-phase-terminal-completion-v1",
            "variant": label, "evidence_kind": "contract_fixture",
            "callback_reached": False, "active_preparation": None,
            "native_preparation": None, "exact_consumer": None,
            "issued_use_count": None}

    @staticmethod
    def _report(observation):
        # Start a fresh line even when unittest has printed a case-name prefix.
        print("\n" + json.dumps(observation, sort_keys=True), flush=True)

    def _capture(self, archive, actual, slot, history):
        return archive.capture(snapshot_id=slot.snapshot_id,
            case_id=slot.case_id, phase=slot.phase, arm=slot.arm,
            plan=self.fixture.support.plan, lineage=actual, history=history)

    def _model_counts(self):
        return {role: len(binding.adapter.invocations)
            for role, binding in self.f.runtime.bindings.items()}

    def _capture_terminal(self, *, withdraw, label, mutate_metadata=False):
        archive, anchor, authority, actual, slot, history = self._registered_before(label)
        allowed, observation = [True], self._observation(label)
        observation["claim_read_entries_after_callback"] = 0
        actual.history_authority = self._withdrawable_history(authority, allowed)
        mutated_ports = []
        if mutate_metadata:
            observation["metadata_port_mutation_reached"] = False
        def intervene(frame):
            if mutate_metadata:
                check = frame.f_locals["lineage_check"]
                owner = check.__self__
                self.assertIs(type(owner), PreparedCurrentContext,
                    "this diagnostic requires the actual fallback preparation")
                self.assertIs(check.__func__, PreparedCurrentContext.revalidate)
                self.assertFalse(observation["active_preparation"])
                # The exact saved original check dynamically reads this named
                # instance port. Preserve and restore any pre-existing override.
                existed = "metadata_current" in vars(owner)
                original = owner.metadata_current
                mutated_ports.append((owner, existed, original))
                owner.metadata_current = lambda: None
                observation["metadata_port_mutation_reached"] = True
            allowed[0] = not withdraw
        final_slot = self._terminal_slot(anchor, actual, observation, intervene, capture_copy=True)
        original_read = self.f.runtime.claims.load_current
        def next_claim(*args, **kwargs):
            if observation["callback_reached"]:
                observation["claim_read_entries_after_callback"] += 1
                if withdraw:
                    raise _ProtectedClaimRead("archive Claim read followed terminal H denial")
            return original_read(*args, **kwargs)
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        try:
            with patch.object(anchor, "authorize_slot_use", final_slot), \
                    patch.object(self.f.runtime.claims, "load_current", next_claim):
                if withdraw:
                    with self.assertRaises(PermissionError):
                        self._capture(archive, actual, slot, history)
                else:
                    snapshot = self._capture(archive, actual, slot, history)
                    self.assertEqual(snapshot.record["schema"], "flora-selected-phase-snapshot-v2")
                    self.assertEqual(snapshot.record["preregistration_sha256"], anchor.preregistration_sha256)
                    self.assertEqual(snapshot.record["history_sha256"], history.digest())
                    self.assertEqual(snapshot.record["phase"], "before")
            self.assertTrue(observation["callback_reached"], "actual final slot was not reached")
            if mutate_metadata:
                self.assertTrue(observation["metadata_port_mutation_reached"])
            if withdraw:
                self.assertEqual(observation["claim_read_entries_after_callback"], 0)
                self.assertIsNone(archive.intent(slot.snapshot_id))
                self.assertIsNone(archive.metadata(slot.snapshot_id))
                self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            else:
                self.assertGreater(observation["claim_read_entries_after_callback"], 0)
                self.assertIsNotNone(archive.intent(slot.snapshot_id))
                self.assertIsNotNone(archive.metadata(slot.snapshot_id))
            self.assertEqual(self._model_counts(), models_before)
        finally:
            allowed[0] = True
            for owner, existed, original in mutated_ports:
                if existed:
                    owner.metadata_current = original
                else:
                    del owner.metadata_current
            self._report(observation)

    def test_01_unchanged_actual_v2_capture_control(self):
        self._capture_terminal(withdraw=False, label="unchanged-capture")

    def test_02_final_slot_history_denial_closes_before_claim_entry(self):
        self._capture_terminal(withdraw=True, label="terminal-history-denial")

    def test_03_standalone_final_slot_context_withdrawal_refuses_lineage(self):
        archive, anchor, authority, actual, slot, history = self._registered_before("standalone-context")
        context = self.f.runtime._context(self.fixture.support.plan)
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        observations = []
        try:
            for withdraw in (False, True):
                observation = self._observation("standalone-context-denial" if withdraw else "standalone-context-control")
                observations.append(observation)
                def intervene():
                    self.f.permitted[0] = not withdraw
                    # Runtime C is withdrawn independently: the real signed-H
                    # controller's metadata permission stays granted.
                    self.assertTrue(authority.authorize_history_metadata(
                        case_id=slot.case_id, phase=slot.phase, history=history))
                    source = self.f.registry.lookup(history.event_ids[0])
                    self.assertEqual(self.f.runtime.source_policy.permits(source, "personal_judgment"), not withdraw)
                callback = self._terminal_slot(anchor, actual, observation, intervene)
                with patch.object(anchor, "authorize_slot_use", callback):
                    def lineage():
                        return actual.context_lineage(case_id=slot.case_id,
                            phase=slot.phase, history=history, context=context)
                    if withdraw:
                        with self.assertRaises(PermissionError):
                            lineage()
                    else:
                        control = lineage()
                        self.assertTrue(control.record()["claims"])
                self.assertTrue(observation["callback_reached"], "standalone final slot was not reached")
                self.assertFalse(observation["active_preparation"], "standalone call unexpectedly borrowed issued preparation")
            self.assertIsNone(archive.intent(slot.snapshot_id))
            self.assertIsNone(archive.metadata(slot.snapshot_id))
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            self.f.permitted[0] = True
            for observation in observations:
                self._report(observation)

    def _qualified_before(self, label):
        # Route restoration queries actual Claim occurrences over all valid
        # and system time. Reuse the established temporal fixture rather than
        # the admission-only cursor, which has no generated temporal columns.
        connection = phase_fixture.PhaseSQL(self.f.connection)
        canonical_planes = (self.f.registry, self.f.candidates, self.f.authority,
            self.f.gateway, self.f.state, self.f.artifacts, self.f.private,
            self.f.runtime.private, self.fixture.custody)
        for plane in canonical_planes:
            plane.connection = connection
        self.f.connection = connection
        self.assertIs(self.f.runtime.claims, self.f.authority)
        self.assertIs(self.f.runtime.sources, self.f.registry)
        self.assertIs(self.f.runtime.context_policy.claims, self.f.authority)
        self.assertIs(self.f.runtime.context_policy.state, self.f.state)
        self.assertIs(self.fixture.custody.runtime, self.f.runtime)
        for plane in canonical_planes:
            self.assertIs(plane.connection, self.f.runtime.claims.connection,
                "qualified restoration must retain one coherent canonical connection")
        archive, anchor, authority, actual, slot, history = self._registered_before(label)
        self.assertIs(archive.connection, connection)
        allowed = [True]
        independent = self._withdrawable_history(authority, allowed)
        actual.history_authority = independent
        captured = self._capture(archive, actual, slot, history)
        metadata = archive.metadata(slot.snapshot_id)
        self.fixture.history_grants.grant_closure(metadata["event_id"], "personal_judgment")
        temporal_fields = {"_xtdb_valid_from", "_xtdb_valid_to",
            "_xtdb_system_from", "_xtdb_system_to"}
        self.assertTrue(captured.record["claims"], "qualified fixture must restore a captured Claim")
        for claim in captured.record["claims"]:
            occurrences = self.f.runtime.claims.current_history(claim["claim_id"])
            self.assertIs(type(occurrences), tuple)
            self.assertTrue(occurrences)
            self.assertTrue(all(temporal_fields.issubset(row) for row in occurrences),
                "the temporal cursor must provide the full current_history row contract")
            self.assertTrue(any(all(row.get(name) == value
                for name, value in claim["projection"].items()) for row in occurrences),
                "the frozen Claim projection must have a real fixture history occurrence")
        route = archive.capture_route(snapshot_id=slot.snapshot_id,
            history_authority=independent, historical_bindings=dict(self.f.runtime.bindings))
        self.assertIs(type(route.lineage), _QualifiedCapturePhaseLineage)
        self.assertEqual(route.snapshot.record["phase"], "before")
        self.assertIsNone(route.snapshot.record["verified_update_exclusion"])
        context = route.runtime._context(route.snapshot.plan)
        return archive, anchor, slot, history, allowed, metadata, route, context

    def test_04_qualified_last_source_callback_denial_refuses_lineage(self):
        archive, _, slot, history, allowed, metadata, route, context = self._qualified_before("qualified-source")
        original_gate = route.lineage._phase_source_gate
        code = _QualifiedUpdateProof.context_lineage.__code__
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        observations = []
        try:
            for withdraw in (False, True):
                observation = self._observation("qualified-source-denial" if withdraw else "qualified-source-control")
                observations.append(observation)
                def last_source():
                    value = original_gate()
                    frame = self._terminal_frame(code, "verified", route.lineage)
                    if frame is not None and not observation["callback_reached"]:
                        self._observe(observation, route.lineage)
                        observation["update_policy_verified"] = frame.f_locals["verified"] is None
                        allowed[0] = not withdraw
                    return value
                with patch.object(route.lineage, "_phase_source_gate", last_source):
                    def lineage():
                        return route.lineage.context_lineage(case_id=slot.case_id,
                            phase=slot.phase, history=history, context=context)
                    if withdraw:
                        with self.assertRaises(PermissionError):
                            lineage()
                    else:
                        control = lineage()
                        self.assertEqual(canonical_sha256(control.record()),
                            route.snapshot.record["context_lineage_sha256"])
                self.assertTrue(observation["callback_reached"], "qualified last source callback was not reached")
                self.assertTrue(observation["update_policy_verified"])
                self.assertFalse(observation["active_preparation"], "standalone qualified call unexpectedly borrowed preparation")
            allowed[0] = True
            self.assertEqual(archive.metadata(slot.snapshot_id), metadata)
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            allowed[0] = True
            for observation in observations:
                self._report(observation)

    def test_05_inner_callback_cannot_publish_foreign_outer_completion(self):
        archive, anchor, slot, history, _, metadata, route, context = self._qualified_before("nested-publication")
        # This is a real independently constructed preparation, with the exact
        # original method. Its check is nevertheless foreign to the nested call.
        foreign = route.runtime._prepare_current_context(route.snapshot.plan)
        self.assertIs(type(foreign), PreparedCurrentContext)
        self.assertEqual(foreign.context.receipt_record(), context.receipt_record())
        foreign_check = foreign.revalidate
        self.assertIs(foreign_check.__func__, PreparedCurrentContext.revalidate)
        foreign_check()
        from flora.selected._phase_preparation import _OWNER_ROLES, _port_readers
        foreign_readers = _port_readers(foreign,
            next(names.split() for role, names, _ in _OWNER_ROLES if role == "prepared"))
        for reader in foreign_readers:
            reader.verify()
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        outer_code = _QualifiedUpdateProof.context_lineage.__code__
        inner_code = PreregisteredPhaseCaptureLineageVerifier.context_lineage.__code__
        observations = []
        try:
            for tamper in (False, True):
                observation = self._observation("foreign-outer-completion" if tamper else "nested-publication-control")
                observations.append(observation)
                collectors = []
                def intervene():
                    inner_frame = self._terminal_frame(inner_code, "actual", route.lineage)
                    outer_frame = self._terminal_frame(outer_code, "lineage_completion", route.lineage)
                    self.assertIsNotNone(inner_frame)
                    self.assertIsNotNone(outer_frame)
                    inner = inner_frame.f_locals["lineage_completion"]
                    outer = outer_frame.f_locals["lineage_completion"]
                    self.assertIs(type(inner), list)
                    self.assertIs(type(outer), list)
                    self.assertEqual(len(inner), 1)
                    self.assertIsNot(inner[0][1].__self__, foreign)
                    collectors.extend((inner, outer))
                    observation["outer_count_before_intervention"] = len(outer)
                    if tamper:
                        # A simultaneous-publication design lets the callback
                        # replace the already published outer check with this
                        # valid-looking original method. Sequential forwarding
                        # must instead refuse the nonempty outer collector.
                        outer[:] = [(get_ident(), foreign_check, foreign_readers)]
                        observation["foreign_outer_installed"] = (
                            len(outer) == 1 and outer[0][1] is foreign_check
                            and outer[0][2] is foreign_readers)
                        self.assertTrue(observation["foreign_outer_installed"])
                callback = self._terminal_slot(anchor, route.lineage, observation, intervene)
                with patch.object(anchor, "authorize_slot_use", callback):
                    def lineage():
                        return route.lineage.context_lineage(case_id=slot.case_id,
                            phase=slot.phase, history=history, context=context)
                    if tamper:
                        with self.assertRaises(PermissionError):
                            lineage()
                    else:
                        control = lineage()
                        self.assertEqual(canonical_sha256(control.record()),
                            route.snapshot.record["context_lineage_sha256"])
                self.assertTrue(observation["callback_reached"], "inner final slot was not reached")
                self.assertFalse(observation["active_preparation"])
                self.assertEqual(len(collectors), 2)
                self.assertEqual(collectors, [[], []], "both per-call collectors must clear on exit")
                observation["both_collectors_cleared"] = True
            self.assertEqual(archive.metadata(slot.snapshot_id), metadata)
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            for observation in observations:
                self._report(observation)

    def test_06_saved_fallback_metadata_port_mutation_cannot_bypass_history_denial(self):
        self._capture_terminal(withdraw=True,
            label="fallback-metadata-port-denial", mutate_metadata=True)

    def test_07_early_phase_receipt_cannot_bless_changed_fallback_metadata_port(self):
        """Capture the basis before producer callbacks, not at publication.

        H stays granted. A late basis capture would accept the replacement as
        its starting material and return an otherwise valid lineage.
        """
        archive, anchor, authority, actual, slot, history = self._registered_before("early-metadata-port")
        context = self.f.runtime._context(self.fixture.support.plan)
        original_receipt = actual.phase_receipt_for
        native_code = NativeJudgmentLineageVerifier.context_lineage.__code__
        wrapper_code = PreregisteredPhaseCaptureLineageVerifier.context_lineage.__code__
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        observations, mutated_ports = [], []
        try:
            for tamper in (False, True):
                observation = self._observation("early-metadata-port-tamper" if tamper else "early-metadata-port-control")
                observation["phase_receipt_calls"] = 0
                observations.append(observation)
                def receipt(request):
                    value = original_receipt(request)
                    observation["phase_receipt_calls"] += 1
                    if not observation["callback_reached"]:
                        frame = self._terminal_frame(native_code, "prepared", actual)
                        wrapper = self._terminal_frame(wrapper_code, "lineage_completion", actual)
                        self.assertIsNotNone(frame, "producer callback lacks the actual Native call")
                        self.assertIsNotNone(wrapper)
                        prepared = frame.f_locals["prepared"]
                        self.assertIs(type(prepared), PreparedCurrentContext,
                            "early substitution must exercise the fallback preparation")
                        record = frame.f_locals.get("lineage_record")
                        self.assertIs(type(record), tuple)
                        self.assertEqual(len(record), 3)
                        self.assertIs(record[1].__self__, prepared)
                        self.assertIs(record[1].__func__, PreparedCurrentContext.revalidate)
                        self.assertTrue(record[2], "the prepared basis must predate this callback")
                        self.assertEqual(wrapper.f_locals["lineage_completion"], [])
                        self._observe(observation, actual)
                        self.assertFalse(observation["active_preparation"])
                        observation["basis_captured_before_callback"] = True
                        if tamper:
                            existed = "metadata_current" in vars(prepared)
                            old_port = prepared.metadata_current
                            mutated_ports.append((prepared, existed, old_port))
                            prepared.metadata_current = lambda: None
                            observation["metadata_port_mutation_reached"] = True
                            # This intervention tests port custody independently
                            # of a permission withdrawal or invalid receipt.
                            self.assertTrue(authority.authorize_history_metadata(
                                case_id=slot.case_id, phase=slot.phase, history=history))
                    return value
                with patch.object(actual, "phase_receipt_for", receipt):
                    def lineage():
                        return actual.context_lineage(case_id=slot.case_id,
                            phase=slot.phase, history=history, context=context)
                    if tamper:
                        with self.assertRaises(PermissionError):
                            lineage()
                    else:
                        control = lineage()
                        self.assertTrue(control.record()["claims"])
                self.assertTrue(observation["callback_reached"])
                if tamper:
                    self.assertTrue(observation["metadata_port_mutation_reached"])
                    self.assertEqual(observation["phase_receipt_calls"], 1,
                        "changed basis continued to the next producer phase receipt")
                else:
                    self.assertEqual(observation["phase_receipt_calls"], 2)
            self.assertIsNone(archive.intent(slot.snapshot_id))
            self.assertIsNone(archive.metadata(slot.snapshot_id))
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            for prepared, existed, old_port in mutated_ports:
                if existed:
                    prepared.metadata_current = old_port
                else:
                    del prepared.metadata_current
            for observation in observations:
                self._report(observation)

    def test_08_inner_collector_cannot_replace_pinned_record_with_same_check(self):
        """An original method does not authorize a replacement reader basis."""
        archive, anchor, slot, history, _, metadata, route, context = self._qualified_before("same-check-reader-substitution")
        inner_code = PreregisteredPhaseCaptureLineageVerifier.context_lineage.__code__
        outer_code = _QualifiedUpdateProof.context_lineage.__code__
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        observations = []
        try:
            for tamper in (False, True):
                observation = self._observation("same-check-empty-readers" if tamper else "same-check-reader-control")
                observations.append(observation)
                collectors = []
                def intervene():
                    inner_frame = self._terminal_frame(inner_code, "lineage_record", route.lineage)
                    outer_frame = self._terminal_frame(outer_code, "lineage_completion", route.lineage)
                    self.assertIsNotNone(inner_frame)
                    self.assertIsNotNone(outer_frame)
                    inner = inner_frame.f_locals["lineage_completion"]
                    outer = outer_frame.f_locals["lineage_completion"]
                    record = inner_frame.f_locals["lineage_record"]
                    check = inner_frame.f_locals["lineage_check"]
                    self.assertIs(type(record), tuple)
                    self.assertEqual(len(record), 3)
                    self.assertEqual(len(inner), 1)
                    self.assertIs(inner[0], record)
                    self.assertIs(record[1], check)
                    self.assertIs(type(check.__self__), PreparedCurrentContext)
                    self.assertTrue(record[2], "emptying an already empty basis would not discriminate")
                    collectors.extend((inner, outer))
                    observation["original_record_pinned"] = True
                    if tamper:
                        replacement = (record[0], check, ())
                        self.assertIsNot(replacement, record)
                        inner[:] = [replacement]
                        observation["same_check_preserved"] = inner[0][1] is check
                        observation["replacement_readers_empty"] = inner[0][2] == ()
                callback = self._terminal_slot(anchor, route.lineage, observation, intervene)
                with patch.object(anchor, "authorize_slot_use", callback):
                    def lineage():
                        return route.lineage.context_lineage(case_id=slot.case_id,
                            phase=slot.phase, history=history, context=context)
                    if tamper:
                        with self.assertRaises(PermissionError):
                            lineage()
                    else:
                        control = lineage()
                        self.assertEqual(canonical_sha256(control.record()),
                            route.snapshot.record["context_lineage_sha256"])
                self.assertTrue(observation["callback_reached"])
                self.assertFalse(observation["active_preparation"])
                if tamper:
                    self.assertTrue(observation["same_check_preserved"])
                    self.assertTrue(observation["replacement_readers_empty"])
                self.assertEqual(len(collectors), 2)
                self.assertEqual(collectors, [[], []])
                observation["both_collectors_cleared"] = True
            self.assertEqual(archive.metadata(slot.snapshot_id), metadata)
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            for observation in observations:
                self._report(observation)

    def test_09_saved_native_barriers_expire_when_original_call_returns(self):
        """A saved same-thread callback cannot prolong its call's authority."""
        archive, _, _, actual, slot, history = self._registered_before("returned-native-barriers")
        context = self.f.runtime._context(self.fixture.support.plan)
        original_receipt = actual.phase_receipt_for
        native_code = NativeJudgmentLineageVerifier.context_lineage.__code__
        observation = self._observation("returned-native-barriers")
        saved, effects, returned = {}, [], [False]
        canonical_before, models_before = tuple(self.f.log.replay()), self._model_counts()
        def receipt(request):
            value = original_receipt(request)
            if not observation["callback_reached"]:
                frame = self._terminal_frame(native_code, "prepared", actual)
                self.assertIsNotNone(frame)
                self.assertIs(type(frame.f_locals["prepared"]), PreparedCurrentContext)
                for name in ("lineage_metadata", "lineage_barrier"):
                    saved[name] = frame.f_locals[name]
                    self.assertTrue(callable(saved[name]))
                self._observe(observation, actual)
                self.assertFalse(observation["active_preparation"])
                observation["saved_barriers_thread"] = get_ident()
            return value
        original_sql = self.f.connection.execute
        original_ciphertext = self.f.objects.backend.get_object
        def sql(*args, **kwargs):
            if returned[0]:
                effects.append("SQL")
            return original_sql(*args, **kwargs)
        def ciphertext(*args, **kwargs):
            if returned[0]:
                effects.append("ciphertext")
            return original_ciphertext(*args, **kwargs)
        try:
            # Install observers before preparation so the successful live call
            # qualifies them; no port changes between capture and expiry probe.
            with patch.object(actual, "phase_receipt_for", receipt), \
                    patch.object(self.f.connection, "execute", sql), \
                    patch.object(self.f.objects.backend, "get_object", ciphertext):
                control = actual.context_lineage(case_id=slot.case_id,
                    phase=slot.phase, history=history, context=context)
                self.assertTrue(control.record()["claims"])
                self.assertTrue(observation["callback_reached"])
                self.assertEqual(set(saved), {"lineage_metadata", "lineage_barrier"})
                self.assertEqual(get_ident(), observation["saved_barriers_thread"])
                returned[0] = True
                for name, barrier in saved.items():
                    with self.subTest(saved_barrier=name):
                        with self.assertRaises(PermissionError):
                            barrier()
                        self.assertEqual(effects, [], "expired barrier performed a protected effect")
            observation["expired_barriers_refused"] = True
            self.assertIsNone(archive.intent(slot.snapshot_id))
            self.assertIsNone(archive.metadata(slot.snapshot_id))
            self.assertEqual(tuple(self.f.log.replay()), canonical_before)
            self.assertEqual(self._model_counts(), models_before)
        finally:
            self._report(observation)


if __name__ == "__main__":
    unittest.main()

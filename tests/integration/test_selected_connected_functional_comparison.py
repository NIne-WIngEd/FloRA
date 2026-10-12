"""One actual registered three-arm path, fictional transport outputs only.

The first physical result is retained even when setup or a control handoff fails.
No fixture success establishes learning, baseline quality, hypothesis support,
or a calibrated response-time verdict.
"""
import asyncio
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from registered_functional_case_fixture import RegisteredFunctionalCase, ScopedSyntheticOwnerBroker, OPERATING_BOUNDS
from flora.comparison_run import _context_bytes, PreparationRequest, ArmStopped
from flora.selected.comparison_custody import evaluation_purpose
from flora.selected.experiment_coordinator import coordinator_purpose
from flora.selected.phase_source_fence import verify_current_phase_sources


H_AUTHORITY_CAUSES = frozenset({"manifest source lineage or current purpose changed",
    "native read lacks current independent phase authority"})
C_AUTHORITY_CAUSES = frozenset({"phase actual source/control predicate denied use",
    "phase current source/parent grant was withdrawn"})


def expected_withdrawal_refusal(error, *, dimension, verified_c_gate=False):
    """Reject unrelated input errors and generic refusal without a reached C gate."""
    causes = H_AUTHORITY_CAUSES if dimension == "H" else C_AUTHORITY_CAUSES
    if isinstance(error, PermissionError):
        return str(error) in causes
    return (dimension == "C" and verified_c_gate and isinstance(error, ArmStopped)
        and error.status == "refused")


class SelectedConnectedFunctionalComparisonTest(unittest.TestCase):
    def withdraw_current_allow(self, fixture, event_id, purpose):
        source = fixture.f.registry.lookup(event_id)
        allowed = fixture.f.policy.current_action(event_id, purpose)
        self.assertEqual(allowed.decision, "allow")
        self.assertTrue(fixture.f.policy.permits(source, purpose))
        fixture.withdraw(event_id, purpose)
        revoked = fixture.f.policy.current_action(event_id, purpose)
        self.assertEqual(revoked.decision, "revoke")
        self.assertEqual(revoked.source_registration_sha256, source.registration_sha256)
        self.assertEqual(revoked.generation, allowed.generation + 1)
        self.assertEqual(revoked.previous_action_sha256, allowed.action_sha256)
        self.assertFalse(fixture.f.policy.permits(source, purpose))
        return revoked

    def case(self, label, *, connect=True):
        fixture = RegisteredFunctionalCase(self, run_id="connected-functional-" + label).build()
        if connect:
            vectors = QdrantClient(url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"))
            self.addCleanup(vectors.close)
            fixture.connect(vectors)
        return fixture

    def test_registered_six_positive_attempts_and_exact_passive_recovery(self):
        fixture = self.case("positive")
        started = time.monotonic()
        print(json.dumps({"mechanical_protocol": "connected-functional-mechanics-v1",
            "bounds": OPERATING_BOUNDS, "performance_acceptance": False}), flush=True)
        for arm, port in fixture.ports.items():
            self.assertEqual(port.worker.manifest.record(), port.manifest_before_registration)
            self.assertEqual(fixture.final.native_plans[arm].worker_manifest_sha256,
                port.worker.manifest.manifest_sha256)
            self.assertEqual(fixture.store.spec.native_arms[arm].worker.record(), port.worker.manifest.record())
        # Reached no-broker control: exact newly appended preflight has no
        # inherited capture grant. No running marker/inference is allowed.
        preflight = fixture.coordinator.readiness(adapters=fixture.adapters)
        self.assertEqual(preflight.status, "supplied_ports_ready")
        preflight_record = fixture.comparison.metadata(fixture.run_id, preflight.artifact_id)
        self.assertFalse(fixture.f.policy.permits(fixture.f.registry.lookup(preflight_record.event_id),
            coordinator_purpose(fixture.experiment_id, fixture.run_id, "capture")))
        before_refusal = tuple(fixture.f.log.replay())
        with self.assertRaisesRegex(PermissionError, "coordinator control purpose"):
            fixture.coordinator._put(artifact_id="coordinator:running", stage="running",
                payload={"status": "started", "execution_nonce": "no-broker-boundary-control", "attempted": True},
                parents=(fixture.comparison.metadata(fixture.run_id, "coordinator:binding").event_id, preflight_record.event_id),
                qualified=True)
        self.assertEqual(tuple(fixture.f.log.replay()), before_refusal)
        self.assertIsNone(fixture.comparison.metadata(fixture.run_id, "coordinator:running"))
        self.assertEqual(fixture.provider.calls, 0)
        self.assertTrue(all(port.codec.calls == 0 for port in fixture.ports.values()))
        print(json.dumps({"no_broker_boundary": "preflight_to_running", "result": "refused_before_append_dispatch",
            "preflight_event_id": preflight_record.event_id, "attempts_started": 0}), flush=True)
        broker = ScopedSyntheticOwnerBroker(fixture)
        broker.control_proposal(fixture.comparison, preflight_record)
        async def execute_once():
            try:
                with broker.notifications():
                    return await fixture.coordinator.execute(adapters=fixture.adapters)
            finally:
                await fixture.close_readers()
        outcome = asyncio.run(execute_once())
        self.assertEqual(outcome.status, "completed_custody")
        run = outcome.run
        matrix = {(attempt.case_id, attempt.phase, attempt.arm): attempt for attempt in run.attempts}
        expected = {("case", phase, arm) for phase in ("before", "after")
            for arm in ("flora_full", "same_evidence_ablation", "general_model_memory")}
        self.assertEqual(set(matrix), expected)
        self.assertEqual(len(run.attempts), 6)
        self.assertEqual([attempt.status for attempt in run.attempts], ["success"] * 6,
            [{"case_id": a.case_id, "phase": a.phase, "arm": a.arm, "status": a.status,
                "elapsed_ms": a.elapsed_ms} for a in run.attempts])
        canonical = {event.event_id: event for event in fixture.f.log.replay()}
        for phase in ("before", "after"):
            history = fixture.histories[("case", phase)]
            attempts = [matrix[("case", phase, arm)] for arm in ("flora_full", "same_evidence_ablation", "general_model_memory")]
            self.assertTrue(all(a.authorized_history_sha256 == history.digest() and a.authorized_event_ids == history.event_ids for a in attempts))
            self.assertEqual(attempts[0].context_sha256, attempts[1].context_sha256)
            self.assertEqual(_context_bytes(fixture.requests[(phase, "flora_full")].context),
                _context_bytes(fixture.requests[(phase, "same_evidence_ablation")].context))
            for arm in ("flora_full", "same_evidence_ablation"):
                attempt, entry = matrix[("case", phase, arm)], fixture.final.native_plans[arm].entry("case", phase)
                judged, request = fixture.judgments[(phase, arm)], fixture.requests[(phase, arm)]
                self.assertEqual(judged.execution.invocation.invocation_id, entry.invocation_id)
                self.assertEqual(request.question, fixture.question)
                self.assertEqual(attempt.context_sha256, hashlib.sha256(_context_bytes(request.context)).hexdigest())
                self.assertEqual(attempt.decision_event_id, judged.decision.event.event_id)
                self.assertEqual(canonical[attempt.decision_event_id].parent_event_ids[0], judged.execution.output_record.event.event_id)
                self.assertIn(judged.delivery.event.event_id, canonical[attempt.decision_event_id].parent_event_ids)
                metadata = fixture.comparison.metadata(fixture.run_id, "output:case:" + phase + ":" + arm)
                self.assertEqual(metadata.record["parent_event_ids"], [attempt.decision_event_id])
            before = PreparationRequest("case", phase, fixture.question, history, fixture.final.plan)
            points, _ = fixture.memory.client.scroll(collection_name=fixture.memory.collection(before), with_payload=True, limit=100)
            self.assertEqual({p.payload["source_window"]["event_id"] for p in points}, set(history.event_ids))
        self.assertEqual(fixture.provider.calls, 2)
        self.assertEqual(sum(port.codec.calls for port in fixture.ports.values()), 4)
        positions = {item.event.event_id: item.stream_position for item in fixture.f.log.replay_committed()}
        self.assertLess(positions[fixture.before_seal.event_id], positions[fixture.gate.event_id])
        self.assertLess(positions[fixture.gate.event_id], positions[fixture.final.event_id])
        for phase in ("before", "after"):
            full, ablation = (fixture.router.route_for(case_id="case", phase=phase, arm=arm)
                for arm in ("flora_full", "same_evidence_ablation"))
            expected_version = fixture.accepted.claim_version_id if phase == "before" else fixture.updated.claim_version_id
            self.assertEqual(full.runtime.claims.load_current(fixture.accepted.claim_id)["current_claim_version_id"], expected_version)
            self.assertEqual(ablation.runtime.claims.load_current(fixture.accepted.claim_id)["current_claim_version_id"], expected_version)
            old = fixture.baseline_roles["personality_judgment"].checkpoint_sha256
            new = fixture.f.runtime._resolve("personality_judgment")[1].checkpoint_sha256
            self.assertNotEqual(old, new)
            full_artifact = full.runtime._resolve("personality_judgment")[1]
            ablation_artifact = ablation.runtime._resolve("personality_judgment")[1]
            self.assertEqual(full_artifact.checkpoint_sha256, old if phase == "before" else new)
            self.assertEqual(ablation_artifact.checkpoint_sha256, old)
            self.assertEqual(fixture.final.plan.binding_for("case", phase, "flora_full").model_artifact_sha256,
                full_artifact.checkpoint_sha256)
            self.assertEqual(fixture.final.plan.binding_for("case", phase, "same_evidence_ablation").model_artifact_sha256,
                ablation_artifact.checkpoint_sha256)
        # Later current owner grants are separate from inference/disclosure grants.
        # This exact run root already contains its plan/input/output/context ancestry.
        run_artifact = fixture.comparison.metadata(fixture.run_id, "run")
        fixture.grant(run_artifact.event_id, "comparison_local_recovery")
        before_recovery = tuple(fixture.f.log.replay())
        original_bytes = fixture.comparison.read(run_id=fixture.run_id, artifact_id="run",
            permissions=fixture.f.policy, purpose="comparison_local_recovery")
        provider_calls = fixture.provider.calls
        fixture.provider.generate = lambda *_args, **_kwargs: self.fail("passive recovery dispatched provider")
        for port in fixture.ports.values():
            port.worker.run = lambda *_args, **_kwargs: self.fail("passive recovery dispatched native worker")
        with fixture.fresh_comparison_reader() as (fresh, permissions):
            self.assertIsNot(fresh, fixture.comparison)
            self.assertIsNot(fresh.connection, fixture.comparison.connection)
            self.assertIsNot(fresh.registry, fixture.comparison.registry)
            self.assertIsNot(fresh.objects, fixture.comparison.objects)
            self.assertIsNot(fresh.log, fixture.comparison.log)
            self.assertIsNot(permissions, fixture.f.policy)
            with patch.object(fresh.log, "append", side_effect=AssertionError("passive recovery appended canonical event")):
                recovered = fresh.recover_run(run_id=fixture.run_id, permissions=permissions)
                self.assertEqual([a.receipt() for a in recovered.attempts], [a.receipt() for a in run.attempts])
                self.assertEqual([a.output for a in recovered.attempts], [a.output for a in run.attempts])
                self.assertEqual(fresh.read(run_id=fixture.run_id, artifact_id="run",
                    permissions=permissions, purpose="comparison_local_recovery"), original_bytes)
                self.assertEqual(fresh.metadata(fixture.run_id, "run"), run_artifact)
        self.assertEqual(tuple(fixture.f.log.replay()), before_recovery)
        self.assertEqual(fixture.provider.calls, provider_calls)
        self.assertTrue(all(connection.closed for connection in fixture.opened_connections))
        # Owner withdrawal refuses a later notification even for a known source;
        # no new action can be minted or existing revoke silently overridden.
        broker.active = False
        owner_before = tuple(fixture.f.log.replay())
        with self.assertRaisesRegex(PermissionError, "intent withdrawn"):
            broker.grant_exact(preflight_record.event_id)
        self.assertEqual(tuple(fixture.f.log.replay()), owner_before)
        print(json.dumps({"connected_functional_status": "six_positive_attempts_exact_recovery",
            "attempts": [a.receipt() for a in recovered.attempts], "elapsed_seconds": time.monotonic() - started,
            "owner_intent_sha256": broker.intent_sha256, "owner_signed_actions": broker.decisions,
            "learned_behavioral_evidence": False}), flush=True)

    def test_fresh_h_withdrawal_after_successful_owned_read_blocks_later_effects(self):
        fixture = self.case("withdraw-h", connect=False)
        entry = fixture.final.native_plans["flora_full"].entry("case", "before")
        reads = fixture.ports["flora_full"].reads
        adapter = fixture.native_adapter("flora_full")
        async def exercise():
            try:
                preparation = PreparationRequest("case", "before", fixture.question,
                    fixture.histories[("case", "before")], fixture.final.plan)
                control = await adapter.prepare(preparation)
                original_request = fixture.requests[("before", "flora_full")]
                self.assertEqual(control, original_request.context)
                self.assertEqual(adapter._check(original_request, control), entry)
                revoked = self.withdraw_current_allow(fixture, fixture.original.event_id,
                    evaluation_purpose(fixture.run_id, "case", "before"))
                self.assertEqual(adapter._check(original_request, control), entry)
                before = tuple(fixture.f.log.replay())
                effects = []
                def forbidden(*_args, **_kwargs):
                    effects.append(True)
                    self.fail("withdrawn H reached a private read, dispatch or append")
                with patch.object(fixture.f.objects.backend, "get_object", forbidden), \
                        patch.object(fixture.f.log, "append", forbidden), \
                        patch.object(fixture.ports["flora_full"].worker, "run", forbidden):
                    with self.assertRaises(PermissionError) as reader_refused:
                        await reads.prepare_context(entry)
                self.assertTrue(expected_withdrawal_refusal(reader_refused.exception, dimension="H"),
                    str(reader_refused.exception))
                self.assertEqual(effects, [])
                self.assertEqual(tuple(fixture.f.log.replay()), before)
                with patch.object(fixture.f.objects.backend, "get_object", forbidden), \
                        patch.object(fixture.f.log, "append", forbidden), \
                        patch.object(fixture.ports["flora_full"].codec, "encode_request", forbidden), \
                        patch.object(fixture.ports["flora_full"].worker, "run", forbidden):
                    with self.assertRaises((ArmStopped, PermissionError)) as refused:
                        await adapter.execute(original_request)
                self.assertTrue(expected_withdrawal_refusal(refused.exception, dimension="H"), str(refused.exception))
                self.assertEqual(fixture.f.policy.current_action(fixture.original.event_id,
                    evaluation_purpose(fixture.run_id, "case", "before")), revoked)
                self.assertEqual(effects, [])
                self.assertEqual(tuple(fixture.f.log.replay()), before)
                print(json.dumps({"negative": "current_H_withdrawal", "adapter_boundary": "first_execute",
                    "refusal_type": type(refused.exception).__name__, "dispatches": 0, "later_effects": 0}), flush=True)
            finally:
                await fixture.close_readers()
        asyncio.run(exercise())

    def test_fresh_c_withdrawal_after_successful_owned_read_blocks_later_effects(self):
        fixture = self.case("withdraw-c", connect=False)
        entry = fixture.final.native_plans["flora_full"].entry("case", "before")
        reads = fixture.ports["flora_full"].reads
        adapter = fixture.native_adapter("flora_full")
        async def exercise():
            try:
                preparation = PreparationRequest("case", "before", fixture.question,
                    fixture.histories[("case", "before")], fixture.final.plan)
                control = await adapter.prepare(preparation)
                original_request = fixture.requests[("before", "flora_full")]
                self.assertEqual(control, original_request.context)
                self.assertEqual(adapter._check(original_request, control), entry)
                self.assertTrue(await reads.authorize_context(entry=entry, request=original_request,
                    context=control, arm="flora_full"))
                # Tamper the actual held context, keeping H/task/entry/final IDs exact.
                tampered = replace(control, plan=replace(control.plan, request_id="tampered-context-request"))
                request = replace(original_request, context=tampered)
                before = tuple(fixture.f.log.replay())
                effects = []
                def forbidden(*_args, **_kwargs):
                    effects.append(True)
                    self.fail("tampered C reached a private read, dispatch or append")
                with patch.object(fixture.f.objects.backend, "get_object", forbidden), \
                        patch.object(fixture.f.log, "append", forbidden), \
                        patch.object(fixture.ports["flora_full"].worker, "run", forbidden):
                    with self.assertRaisesRegex(ValueError, "frozen"):
                        await reads.authorize_context(entry=entry, request=request, context=tampered, arm="flora_full")
                self.assertEqual(effects, [])
                self.assertEqual(tuple(fixture.f.log.replay()), before)
                # Independent current C: revoke the actual approved-state use,
                # keeping the exact original history evaluation authority live.
                approval = next(item.approval_event_id for item in control.items if item.approval_event_id is not None)
                revoked = self.withdraw_current_allow(fixture, approval, "personal_judgment")
                self.assertEqual(adapter._check(original_request, control), entry)
                self.assertTrue(fixture.evidence.authorize_history_metadata(case_id="case", phase="before",
                    history=fixture.histories[("case", "before")]))
                before = tuple(fixture.f.log.replay())
                effects.clear()
                def actual_current_context_gate(session):
                    routed, _history, guard, _arm, _receipt = reads._phase_session(session, entry,
                        original_request, arm="flora_full")
                    guard()
                    return verify_current_phase_sources(policy=routed.runtime.context_policy,
                        source_event_ids=(approval,), authority_guard=guard)
                with patch.object(fixture.f.objects.backend, "get_object", forbidden), \
                        patch.object(fixture.f.log, "append", forbidden), \
                        patch.object(fixture.ports["flora_full"].worker, "run", forbidden):
                    with self.assertRaises(PermissionError) as gate_refused:
                        await reads._read(actual_current_context_gate)
                    self.assertTrue(expected_withdrawal_refusal(gate_refused.exception, dimension="C"),
                        str(gate_refused.exception))
                    try:
                        allowed = await reads.authorize_context(entry=entry, request=original_request,
                            context=control, arm="flora_full")
                    except PermissionError as error:
                        self.assertTrue(expected_withdrawal_refusal(error, dimension="C"), str(error))
                    else:
                        self.assertIs(allowed, False)
                self.assertEqual(effects, [])
                self.assertEqual(tuple(fixture.f.log.replay()), before)
                with patch.object(fixture.f.objects.backend, "get_object", forbidden), \
                        patch.object(fixture.f.log, "append", forbidden), \
                        patch.object(fixture.ports["flora_full"].codec, "encode_request", forbidden), \
                        patch.object(fixture.ports["flora_full"].worker, "run", forbidden):
                    with self.assertRaises((ArmStopped, PermissionError)) as refused:
                        await adapter.execute(original_request)
                self.assertTrue(expected_withdrawal_refusal(refused.exception, dimension="C", verified_c_gate=True),
                    str(refused.exception))
                self.assertEqual(fixture.f.policy.current_action(approval, "personal_judgment"), revoked)
                self.assertTrue(fixture.evidence.authorize_history_metadata(case_id="case", phase="before",
                    history=fixture.histories[("case", "before")]))
                self.assertEqual(effects, [])
                self.assertEqual(tuple(fixture.f.log.replay()), before)
                print(json.dumps({"negative": "current_C_withdrawal", "adapter_boundary": "first_execute",
                    "refusal_type": type(refused.exception).__name__, "current_C_gate_cause": str(gate_refused.exception),
                    "dispatches": 0, "later_effects": 0}), flush=True)
            finally:
                await fixture.close_readers()
        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()

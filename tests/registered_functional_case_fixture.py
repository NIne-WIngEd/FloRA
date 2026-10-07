"""Actual two-stage selected chronology; all producer bytes are fictional.

This verifies custody/routing mechanics, not learning, quality, or readiness
for the FloRA experiment. Nothing in this fixture trains either missing model.
"""
import base64
import asyncio
from copy import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time
import sys
import unittest
from unittest.mock import patch
import psycopg
from psycopg.conninfo import conninfo_to_dict
import tempfile
import uuid
import threading
from contextlib import contextmanager
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cognitive_kernel.canonical import canonical_json_bytes, canonical_sha256
from cognitive_kernel.contracts import ProvenanceReference
from cognitive_kernel.experience import ExperienceEvent
from flora.comparator import encoded, sha
from flora.comparison_run import ArmResult, ExecutionRequest, MeasuredUsage, SourceMaterial, _validate_result
from flora.comparison_run import _context_bytes
from flora.comparator import Ed25519TransportObservationVerifier, GeneralMemoryArmAdapter, ProviderResponse
from flora.selected.bounded_xtdb_reads import BoundedXTDBReadConfiguration, BoundedXTDBReadOpener, ExplicitXTDBReadCredentials
from flora.selected.native_arm import NativeArmAdapter, NativeWorkerCompletion, VerifiedNativeUsage
from flora.selected.native_writer_guard import NativeWriterConfiguration, NativeWriterGuard, VerifiedNativeWriterOwnership
from flora.selected.experiment_coordinator import RegisteredExperimentCoordinator, coordinator_purpose
from flora.selected.assessment_custody import XTDBAssessmentCustody
from flora.selected.comparator_memory import QdrantOriginalMemory, SelectedComparatorDisclosure, SelectedComparatorRecorder
from flora.selected.provider_attempt_custody import OriginalMemoryProviderInputVerifier, XTDBProviderAttemptCustody, capture_purpose
from flora.providers.openai_responses import TransportAttempt
from flora.selected.formation_policy import FormationPermissionAction, formation_permission_payload
from flora.selected.formation_policy import XTDBFormationPermissionPolicy
from flora.selected.formation_registry import XTDBFormationSourceRegistry
from flora.selected.object_store import EncryptedObjectPlane, LocalObjectBackend
from flora.selected.experience import KurrentExperienceLog
from kurrentdbclient import KurrentDBClient
import os
from flora.selected.artifact_registry import ArtifactManifest
from flora.selected.comparison_custody import XTDBComparisonCustody, SelectedRunEvidencePolicy, evaluation_purpose
from flora.selected.context import ContextPlan, StateRoute
from flora.selected.experiment_runtime import FloRAExperimentRuntime
from flora.selected.experiment_manifests import (
    CohortEntry, SelectedSourceAuthority, SplitIsolationRule, XTDBExperimentManifestCustody,
    cohort_source_purpose, manifest_purpose,
)
from flora.selected.experiment_preregistration import (
    CaptureSlotDeclaration, ExperimentPreregistration, NativeArmDeclaration,
    XTDBExperimentPreregistrationCustody, preregistration_purpose,
)
from flora.selected.formation_context import register_experience_source
from flora.selected.native_worker import NativeWorkerManifest
from flora.selected.native_reads import (
    InitializedNativeSessionFactory, NativeReadManifest, NativeReadSession, SelectedNativeReadServices,
)
from flora.selected.judgment_context import RegisteredJudgmentContextPolicy
from flora.selected.judgment_lineage import NativeJudgmentLineageVerifier
from flora.selected.personal_artifact_custody import DurablePersonalReferences
from flora.selected.phase_routes import SelectedPhaseLineageRouter, derive_preregistered_ablation_runtime
from flora.selected.phase_snapshots import (
    FrozenPhaseUpdatePolicy, PreregisteredPhaseCaptureLineageVerifier, XTDBPhaseSnapshotCustody,
)

import test_selected_phase_history_routes as support
import native_contract_fixture as native_fixture
import comparator_fixtures as comparator_fixture


def public(key):
    return key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


class FictionalPreregisteredQualifier(support._lf.FictionalPhaseQualifier):
    """Independent signed fixture allow-list; it inspects no learned update."""
    update_allowed = True
    def _signed(self, request, receipt, schema):
        wrapper = json.loads(receipt)
        payload = wrapper["payload"]
        self.public_key.verify(base64.b64decode(wrapper["signature"], validate=True), canonical_json_bytes(payload))
        if payload["schema"] != schema or payload["request_sha256"] != canonical_sha256(request):
            raise PermissionError("fictional signed qualification changed the exact anchored request")
        return payload

    def verify_preregistered_update(self, *, request, receipt):
        if not self.update_allowed:
            raise PermissionError("fictional independent update qualification withdrawn")
        payload = self._signed(request, receipt, "fictional-preregistered-update-v1")
        return {**payload, "schema": "flora-qualified-preregistered-update-v1", "receipt_sha256": sha(receipt)}

    def verify_phase_update_policy(self, *, request, receipt):
        payload = self._signed(request, receipt, "fictional-anchored-update-exclusion-v1")
        return {**payload, "schema": "flora-qualified-phase-update-exclusion-v2", "receipt_sha256": sha(receipt)}


# New mechanical protocol: these are finite resource containment, not a speed score.
OPERATING_BOUNDS = {
    "attempt_ms": 300000, "read_operation_ms": 240000, "writer_operation_ms": 240000,
    "backend_query_ms": 30000, "read_session_ms": 240000, "connect_seconds": 5,
    "relay_wall_ms": 5000, "relay_terminate_grace_ms": 80,
    "relay_input_bytes": 65536, "relay_output_bytes": 4096, "relay_stderr_bytes": 4096,
    "relay_artifact_bytes": 67108864, "reader_concurrency_per_arm": 1,
    "whole_job_seconds": 3600,
    "hard_process_seconds": 2700, "hard_process_kill_grace_seconds": 30,
}


class SignedFixtureWriterQualifier:
    """Fictional independent ownership attestation; actual guard enforces exclusivity."""
    def __init__(self):
        self.key = Ed25519PrivateKey.generate()

    def receipt(self, request):
        payload = {"schema": "fictional-connected-writer-v1", "request_sha256": canonical_sha256(request)}
        return canonical_json_bytes({"payload": payload, "signature": base64.b64encode(
            self.key.sign(canonical_json_bytes(payload))).decode()})

    def verify_native_writer(self, *, request, receipt):
        body = json.loads(receipt)
        self.key.public_key().verify(base64.b64decode(body["signature"], validate=True), canonical_json_bytes(body["payload"]))
        if body["payload"] != {"schema": "fictional-connected-writer-v1", "request_sha256": canonical_sha256(request)}:
            raise PermissionError("fictional writer attestation changed its physical binding")
        return VerifiedNativeWriterOwnership("fixture-owner-qualifier", "fixture-owner-qualification",
            canonical_sha256(request), sha(receipt), True)


class ConnectedFixtureMeter(native_fixture.FixtureMeter):
    def __init__(self, arm):
        super().__init__(None)
        self.arm, self.judgments = arm, None
        self.artifact_sha256 = sha(Path(__file__).read_bytes())
        self.usage = MeasuredUsage("fixture-feature", 5, 10, 5, 0)
        self.configuration_sha256 = canonical_sha256({"schema": "fictional-connected-meter-config-v1",
            "arm": arm, "usage": vars(self.usage), "public_key_sha256": sha(public(self.key))})

    def payload(self, request):
        judgment = self.judgments[(request.phase, self.arm)]
        return {"schema": "fictional-native-meter-v1", "run_plan": request.plan.digest(),
            "case_id": request.case_id, "phase": request.phase,
            "invocation_id": judgment.execution.invocation.invocation_id,
            "input_sha256": judgment.execution.invocation.input_sha256,
            "output_sha256": sha(judgment.execution.result.output), "usage": vars(self.usage)}


class ConnectedFixtureCodec(native_fixture.FixtureWorkerCodec):
    def __init__(self, arm, meter):
        super().__init__(None)
        self.arm, self.meter, self.judgments = arm, meter, None
        self.artifact_sha256 = sha(Path(__file__).read_bytes())
        self.calls = 0

    def encode_request(self, *, frozen, entry, request):
        self.calls += 1
        return canonical_json_bytes({"invocation_id": entry.invocation_id,
            "output_event": self.judgments[(request.phase, self.arm)].execution.output_record.event.event_id,
            "meter": base64.b64encode(self.meter.receipt(request)).decode(),
            "question_sha256": sha(request.question), "context_sha256": sha(_context_bytes(request.context)),
            "frozen_arm_sha256": frozen.lineage_sha256})


class ScopedSyntheticOwnerBroker:
    """A supplied fixture owner, separate from runtime authorization gates.

    Notification is a proposal. A signed prior intent, current parents, no
    existing denial and exact frozen receipt/control identity decide each grant.
    This broker has no inference, source-disclosure or evaluation grant authority.
    """
    def __init__(self, fixture):
        self.fixture, self.active, self.started = fixture, True, time.monotonic()
        self.owner_thread = threading.get_ident()
        self.decisions, self.granted_sources = [], set()
        self.approved_proposals = {}
        self.initial_receipts = {record.event.event_id for judged in fixture.judgments.values()
            for record in (judged.delivery, judged.decision, judged.execution.output_record)}
        self.baseline_receipts = {}
        ready_payload = {"status": "supplied_ports_ready", "reasons": [], "attempted": False,
            "behavioral_result": "not_collected"}
        ready_metadata = {"binding_sha256": fixture.coordinator.binding_sha256, "stage": "preflight",
            "qualified_phases_required": False, "part1_accepted": False}
        ready_body = {"schema": "flora-experiment-coordinator-stage-v1", **ready_metadata, "payload": ready_payload}
        self.intent = {"schema": "fictional-connected-owner-intent-v1", "scope": fixture.f.scope.metadata_record(),
            "authority_namespace_id": fixture.f.namespace, "run_id": fixture.run_id,
            "binding_sha256": fixture.coordinator.binding_sha256, "final_plan_sha256": fixture.final.plan.digest(),
            "purposes": [coordinator_purpose(fixture.experiment_id, fixture.run_id, operation) for operation in ("capture", "read")],
            "maximum_signed_actions": 128, "expires_after_seconds": 2700,
            "control_kinds": ["coordinator_preflight", "coordinator_running", "coordinator_completed", "coordinator_interrupted",
                "context", "comparator_provider_exchange", "output", "rejected_output", "run"],
            "native_delivery_ids": sorted(judged.delivery.event.event_id for judged in fixture.judgments.values()),
            "native_receipts": [{"phase": phase, "arm": arm,
                "delivery_event_id": judged.delivery.event.event_id, "delivery_event_sha256": judged.delivery.event.event_sha256,
                "decision_event_id": judged.decision.event.event_id, "decision_event_sha256": judged.decision.event.event_sha256,
                "context_sha256": sha(_context_bytes(judged.context)),
                "context_receipt_sha256": sha(encoded(judged.context.receipt_record())),
                "context_source_ids": list(judged.context.source_event_ids),
                "output_sha256": sha(judged.execution.result.output)}
                for (phase, arm), judged in sorted(fixture.judgments.items())],
            "provider_task_ids": sorted(fixture.store.spec.provider_task_ids.values()),
            "baseline_configuration_sha256": fixture.store.spec.comparator.digest(),
            "ready_preflight_artifact_id": "coordinator:preflight:" + canonical_sha256(ready_payload),
            "ready_preflight_metadata": ready_metadata,
            "ready_preflight_content_sha256": sha(encoded(ready_body)),
            "baseline_receipt_types": ["context_delivery", "decision"],
            "baseline_receipt_contract": "exact enrolled captured task context bytes and ordered sources; signed successful response verdict; frozen producer/model",
            "refuse_missing_parent_grants": True, "refuse_prior_deny_or_revoke": True}
        self.intent_sha256 = canonical_sha256(self.intent)
        self.signature = fixture.f.fabric.signer.sign(canonical_json_bytes(self.intent))

    def current_intent(self):
        f = self.fixture
        f.f.fabric.signer.public_key().verify(self.signature, canonical_json_bytes(self.intent))
        if (not self.active or not f.owner_actions_enabled or threading.get_ident() != self.owner_thread
                or time.monotonic() - self.started >= self.intent["expires_after_seconds"]
                or canonical_sha256(self.intent) != self.intent_sha256
                or self.intent["scope"] != f.f.scope.metadata_record()
                or self.intent["authority_namespace_id"] != f.f.namespace or self.intent["run_id"] != f.run_id
                or f.coordinator.binding_sha256 != self.intent["binding_sha256"]
                or f.final.plan.digest() != self.intent["final_plan_sha256"]):
            raise PermissionError("synthetic owner intent withdrawn, expired or changed")

    def _same_custody(self, custody):
        f = self.fixture
        return (custody.scope == f.f.scope and custody.authority_namespace_id == f.f.namespace
            and getattr(custody, "_physical_custody", custody) is f.comparison)

    def _canonical(self, event_id):
        return next((event for event in self.fixture.f.log.replay() if event.event_id == event_id), None)

    def _provider_capture(self, phase):
        """Inspect only the actual issued, declared, currently guarded task handle."""
        self.current_intent()
        f = self.fixture
        task_id = f.store.spec.provider_task_ids[("case", phase)]
        sink, response = f.provider_tasks.get(task_id, (None, None))
        if sink is None or task_id not in self.intent["provider_task_ids"]:
            raise PermissionError("synthetic owner lacks its declared issued provider task")
        body, request = sink.body, sink.request
        if (body["run_id"] != f.run_id or body["task_id"] != task_id or body["case_id"] != "case"
                or body["phase"] != phase or body["arm"] != "general_model_memory"
                or body["plan_sha256"] != self.intent["final_plan_sha256"]
                or tuple(body["original_event_ids"]) != f.histories[("case", phase)].event_ids
                or body["history_sha256"] != f.histories[("case", phase)].digest()
                or base64.b64decode(body["question_base64"], validate=True) != f.question
                or base64.b64decode(body["context_base64"], validate=True) != _context_bytes(request.context)
                or tuple(body["context_source_ids"]) != request.context.source_event_ids
                or canonical_sha256(body["provider_configuration"]) != f.store.spec.comparator.provider.digest()):
            raise PermissionError("synthetic owner issued provider task changed frozen exact inputs")
        # These actual methods check the durable task/observation/signature and
        # current capture/final authority; no broad audit grant or private scan.
        sink.verify_response(response)
        observation, _usage = sink._captured_observation()
        self.current_intent()
        return sink, response, observation

    def grant_exact(self, event_id):
        self.current_intent()
        f, policy = self.fixture, self.fixture.f.policy
        approved = self.approved_proposals.get(event_id)
        if approved is None:
            raise PermissionError("synthetic owner target lacks an approved typed proposal")
        target, signature = approved
        f.f.fabric.signer.public_key().verify(signature, canonical_json_bytes(target))
        source = f.f.registry.lookup(event_id)
        event = next((event for event in f.f.log.replay() if event.event_id == event_id), None)
        if (source is None or event is None or target["intent_sha256"] != self.intent_sha256
                or target["registration_sha256"] != source.registration_sha256
                or target["event_sha256"] != event.event_sha256
                or target["parents"] != list(source.evidence.parent_refs)):
            raise PermissionError("synthetic owner approved target changed its exact registered source")
        if target["artifact_id"] is not None:
            control = f.comparison.metadata(f.run_id, target["artifact_id"])
            if control is None or control.record["record_sha256"] != target["control_record_sha256"]:
                raise PermissionError("synthetic owner approved control changed its exact registered metadata")
        for purpose in self.intent["purposes"]:
            self.current_intent()
            prior = policy.current_action(event_id, purpose)
            if prior is not None:
                if prior.decision != "allow" or not policy.permits(source, purpose):
                    raise PermissionError("synthetic owner refuses prior denial or missing ancestor authority")
                continue
            for parent_id in source.evidence.parent_refs:
                parent = f.f.registry.lookup(parent_id)
                if parent is None or not policy.permits(parent, purpose):
                    raise PermissionError("synthetic owner refuses a missing parent grant")
            if len(self.decisions) >= self.intent["maximum_signed_actions"]:
                raise PermissionError("synthetic owner signed-action allowance exhausted")
            # This is the actual independently signed canonical owner action.
            # It never calls the recursive setup grant helper.
            f.base.eval_grant(source, purpose)
            self.current_intent()
            if not policy.permits(source, purpose):
                raise PermissionError("owner exact grant did not retain current parent authority")
            action = policy.current_action(event_id, purpose)
            self.decisions.append({"event_id": event_id, "registration_sha256": source.registration_sha256,
                "purpose": purpose, "action_id": action.action_id, "action_sha256": action.action_sha256,
                "intent_sha256": self.intent_sha256})
        self.granted_sources.add(event_id)

    def _approve_typed_target(self, event_id, *, kind, control=None):
        """Called only after the typed proposal validators prove exact membership."""
        self.current_intent()
        f = self.fixture
        source = f.f.registry.lookup(event_id)
        event = next((event for event in f.f.log.replay() if event.event_id == event_id), None)
        if (source is None or event is None or event.scope != f.f.scope
                or event.content_digest != source.evidence.content_digest
                or event.parent_event_ids != source.evidence.parent_refs
                or event.payload_reference != source.object_ref
                or (control is not None and event.event_type != "comparison_artifact")
                or (control is None and event.event_type != kind)):
            raise PermissionError("synthetic owner typed proposal lacks exact canonical registered identity")
        if control is not None and (control.record["content_sha256"] != event.content_digest
                or control.record["parent_event_ids"] != list(event.parent_event_ids)):
            raise PermissionError("synthetic owner control content/parents changed canonical identity")
        target = {"event_id": event_id, "event_sha256": event.event_sha256, "kind": kind,
            "registration_sha256": source.registration_sha256, "parents": list(source.evidence.parent_refs),
            "artifact_id": None if control is None else control.record["artifact_id"],
            "control_record_sha256": None if control is None else control.record["record_sha256"],
            "intent_sha256": self.intent_sha256}
        prior = self.approved_proposals.get(event_id)
        if prior is not None and prior[0] != target:
            raise PermissionError("synthetic owner typed target identity is immutable")
        self.approved_proposals[event_id] = target, f.f.fabric.signer.sign(canonical_json_bytes(target))
        self.grant_exact(event_id)

    def receipt_proposal(self, custody, recorded):
        if not self._same_custody(custody):
            return
        event, f = recorded.event, self.fixture
        config = f.store.spec.comparator
        if event.event_type not in {"context_delivery", "decision"} or event.event_id in self.initial_receipts:
            return
        self.current_intent()
        if (event.provenance.responsible_component != config.producer_component
                or recorded.raw.plaintext_sha256 != event.content_digest or recorded.raw.object_id != event.payload_reference):
            raise PermissionError("synthetic owner refuses another producer receipt")
        parents = event.parent_event_ids
        if event.event_type == "decision":
            if (not parents or (parents[0], "sources") not in self.baseline_receipts
                    or event.provenance.model_id != config.provider.digest()):
                raise PermissionError("synthetic owner decision lacks its exact enrolled delivery")
            phase = self.baseline_receipts[parents[0]]
            if tuple(parents[1:]) != self.baseline_receipts[(parents[0], "sources")]:
                raise PermissionError("synthetic owner decision changed original parents")
            _sink, response, _observation = self._provider_capture(phase)
            expected = encoded({"schema": "flora-decision-v1", "verdict_base64": base64.b64encode(response.output).decode(),
                "consumed_event_ids": list(parents), "model_artifact_sha256": config.provider.digest()})
            if event.content_digest != sha(expected):
                raise PermissionError("synthetic owner decision changed exact captured response verdict")
        else:
            phases = []
            for phase in ("before", "after"):
                task_id = f.store.spec.provider_task_ids[("case", phase)]
                if task_id not in f.provider_tasks:
                    continue
                sink, _response, _observation = self._provider_capture(phase)
                if (parents == tuple(sink.body["context_source_ids"])
                        and event.content_digest == sha(encoded(sink.request.context.receipt_record()))):
                    phases.append(phase)
            if len(phases) != 1:
                raise PermissionError("synthetic owner delivery lacks one exact captured provider task")
            phase = phases[0]
        if event.scope != f.f.scope or custody.registry.lookup(event.event_id) != f.f.registry.lookup(event.event_id):
            raise PermissionError("synthetic owner receipt changed canonical source identity")
        self._approve_typed_target(event.event_id, kind=event.event_type)
        self.baseline_receipts[event.event_id] = phase
        if event.event_type == "context_delivery":
            self.baseline_receipts[(event.event_id, "sources")] = tuple(parents)

    def control_proposal(self, custody, record):
        if not self._same_custody(custody) or record.record["run_id"] != self.fixture.run_id:
            return
        f, body = self.fixture, record.record
        kind, identity, meta = body["kind"], body["artifact_id"], body["metadata"]
        if kind not in self.intent["control_kinds"]:
            return
        self.current_intent()
        if f.comparison.metadata(f.run_id, identity) != record:
            raise PermissionError("synthetic owner control is not exact registered metadata")
        if kind.startswith("coordinator_"):
            stage = kind.removeprefix("coordinator_")
            prefix = "coordinator:" + stage
            if (meta["binding_sha256"] != self.intent["binding_sha256"] or meta["stage"] != stage
                    or (stage != "preflight" and identity != prefix)
                    or meta.get("part1_accepted") is not False
                    or meta.get("qualified_phases_required") is not (stage in {"running", "completed"})):
                raise PermissionError("synthetic owner control changed coordinator stage identity")
            if stage == "preflight" and (identity != self.intent["ready_preflight_artifact_id"]
                    or meta != self.intent["ready_preflight_metadata"]
                    or body["content_sha256"] != self.intent["ready_preflight_content_sha256"]):
                raise PermissionError("synthetic owner preflight changed declared actual readiness identity")
            parents = [r["event_id"] for r in f.coordinator._manifest_records.values()]
            parents.append(f.coordinator._input_records["plan"].event_id)
            if stage in {"preflight", "running"}:
                parents.append(f.comparison.metadata(f.run_id, "coordinator:binding").event_id)
            if stage == "running":
                preflights = [parent for parent in body["parent_event_ids"]
                    if f.f.registry.lookup(parent) is not None and parent not in parents]
                if len(preflights) != 1 or preflights[0] not in self.granted_sources:
                    raise PermissionError("synthetic owner running control lacks its authorized exact preflight")
                approved = self.approved_proposals.get(preflights[0])
                if approved is None:
                    raise PermissionError("synthetic owner running parent lacks approved typed preflight")
                target, signature = approved
                f.f.fabric.signer.public_key().verify(signature, canonical_json_bytes(target))
                exact = f.comparison.metadata(f.run_id, self.intent["ready_preflight_artifact_id"])
                source, canonical = f.f.registry.lookup(preflights[0]), self._canonical(preflights[0])
                if (target["kind"] != "coordinator_preflight" or target["intent_sha256"] != self.intent_sha256
                        or target["artifact_id"] != self.intent["ready_preflight_artifact_id"]
                        or exact is None or exact.event_id != preflights[0]
                        or exact.record["run_id"] != f.run_id or exact.record["kind"] != "coordinator_preflight"
                        or exact.record["metadata"] != self.intent["ready_preflight_metadata"]
                        or exact.record["content_sha256"] != self.intent["ready_preflight_content_sha256"]
                        or exact.record["record_sha256"] != target["control_record_sha256"]
                        or source is None or source.registration_sha256 != target["registration_sha256"]
                        or canonical is None or canonical.event_sha256 != target["event_sha256"]
                        or list(source.evidence.parent_refs) != target["parents"]):
                    raise PermissionError("synthetic owner running parent is not exact approved typed preflight")
                parents += preflights
            if stage in {"completed", "interrupted"}:
                parents.append(f.comparison.metadata(f.run_id, "coordinator:running").event_id)
            if stage == "completed":
                parents.append(f.comparison.metadata(f.run_id, "run").event_id)
            if sorted(set(parents)) != body["parent_event_ids"]:
                raise PermissionError("synthetic owner coordinator control changed stage parents")
        elif kind == "context":
            delivery = meta["delivery_event_id"]
            declared_deliveries = set(self.intent["native_delivery_ids"]) | {
                event_id for event_id in self.baseline_receipts if isinstance(event_id, str)
                and (event_id, "sources") in self.baseline_receipts}
            if (identity != "context:" + delivery or tuple(body["parent_event_ids"]) != (delivery,)
                    or delivery not in declared_deliveries):
                raise PermissionError("synthetic owner context lacks a declared delivery")
            actual_delivery = next((event for event in f.f.log.replay() if event.event_id == delivery), None)
            if actual_delivery is None or actual_delivery.event_type != "context_delivery":
                raise PermissionError("synthetic owner context parent is not an actual declared delivery")
            native = next((item for item in self.intent["native_receipts"] if item["delivery_event_id"] == delivery), None)
            if native is not None:
                context_sha, receipt_sha, source_ids = native["context_sha256"], native["context_receipt_sha256"], native["context_source_ids"]
                if actual_delivery.event_sha256 != native["delivery_event_sha256"]:
                    raise PermissionError("synthetic owner native delivery changed exact declared identity")
            else:
                sink, _response, _observation = self._provider_capture(self.baseline_receipts[delivery])
                context_sha = sha(base64.b64decode(sink.body["context_base64"], validate=True))
                receipt_sha, source_ids = sha(encoded(sink.request.context.receipt_record())), sink.body["context_source_ids"]
            if (body["content_sha256"] != context_sha or meta["context_sha256"] != context_sha
                    or meta["source_event_ids"] != source_ids or actual_delivery.content_digest != receipt_sha
                    or list(actual_delivery.parent_event_ids) != source_ids):
                raise PermissionError("synthetic owner context changed exact declared captured bytes/sources")
        elif kind == "comparator_provider_exchange":
            decision = meta["decision_event_id"]
            canonical = self._canonical(decision)
            if (identity != "provider_exchange:" + decision or decision not in self.baseline_receipts
                    or canonical is None or canonical.event_type != "decision"
                    or meta["provider_configuration_sha256"] != f.store.spec.comparator.provider.digest()):
                raise PermissionError("synthetic owner exchange lacks its enrolled frozen receipt")
            expected_parents = (decision, f.comparison.metadata(f.run_id, "question:case").event_id)
            if tuple(body["parent_event_ids"]) != expected_parents:
                raise PermissionError("synthetic owner exchange changed exact decision/question parents")
            sink, response, observation = self._provider_capture(self.baseline_receipts[decision])
            exchange = {"schema": "flora-comparator-provider-exchange-v1", "dispatch": sink.provider_request.record(),
                "observation": response.observation(), "proof_base64": base64.b64encode(response.proof).decode(),
                "actual_request_base64": base64.b64encode(sink.provider_request.payload).decode(),
                "actual_response_base64": base64.b64encode(response.raw_response).decode(),
                "token_count": sink.body["preflight_count"], "authorization_marker": response.authorization_marker,
                "decision_event_id": decision}
            if (meta["request_sha256"] != observation.metadata["request_sha256"]
                    or meta["response_sha256"] != observation.metadata["response_sha256"]
                    or body["content_sha256"] != sha(encoded(exchange))):
                raise PermissionError("synthetic owner exchange changed exact captured request/response bytes")
        elif kind in {"output", "rejected_output"}:
            case, phase = meta["case_id"], meta["phase"]
            if (case, phase) not in f.histories or identity not in {"output:" + case + ":" + phase + ":" + arm for arm in f.adapters}:
                raise PermissionError("synthetic owner output is outside the frozen matrix")
            arm = identity.rsplit(":", 1)[-1]
            native = next((item for item in self.intent["native_receipts"] if item["phase"] == phase and item["arm"] == arm), None)
            decisions = ({native["decision_event_id"]} if native is not None
                else {event_id for event_id, actual_phase in self.baseline_receipts.items()
                    if isinstance(event_id, str) and actual_phase == phase
                    and f.f.registry.lookup(event_id).evidence.ref_id == event_id
                    and next(e for e in f.f.log.replay() if e.event_id == event_id).event_type == "decision"})
            if kind == "rejected_output":
                if tuple(body["parent_event_ids"]) != f.histories[(case, phase)].event_ids or meta["attempt_status"] == "success":
                    raise PermissionError("synthetic owner rejected output changed exact original parents/status")
            elif (meta["attempt_status"] != "success" or len(body["parent_event_ids"]) != 1
                    or body["parent_event_ids"][0] not in decisions):
                raise PermissionError("synthetic owner output changed exact decision parent")
            elif native is not None:
                if (self._canonical(body["parent_event_ids"][0]).event_sha256 != native["decision_event_sha256"]
                        or body["content_sha256"] != native["output_sha256"] or meta["output_sha256"] != native["output_sha256"]):
                    raise PermissionError("synthetic owner native output changed its declared actual verdict")
            else:
                _sink, response, _observation = self._provider_capture(phase)
                if body["content_sha256"] != sha(response.output) or meta["output_sha256"] != sha(response.output):
                    raise PermissionError("synthetic owner baseline output changed its exact captured verdict")
        elif kind == "run":
            expected = {(case, phase, arm) for case, phase in f.histories for arm in f.adapters}
            if (identity != "run" or meta["plan_sha256"] != f.final.plan.digest()
                    or len(meta["matrix"]) != len(expected)
                    or {(row["case_id"], row["phase"], row["arm"]) for row in meta["matrix"]} != expected):
                raise PermissionError("synthetic owner run is outside the complete frozen matrix")
            parents = {f.comparison.metadata(f.run_id, "plan").event_id}
            for row in meta["matrix"]:
                case, phase, arm = row["case_id"], row["phase"], row["arm"]
                parents.update((f.comparison.metadata(f.run_id, "history:" + case + ":" + phase).event_id,
                    f.comparison.metadata(f.run_id, "question:" + case).event_id))
                output = f.comparison.metadata(f.run_id, "output:" + case + ":" + phase + ":" + arm)
                if output is not None:
                    parents.add(output.event_id)
                if row["status"] == "success":
                    if output is None or output.record["kind"] != "output":
                        raise PermissionError("synthetic owner run lost its successful output")
                    decision = self._canonical(output.record["parent_event_ids"][0])
                    if decision is None or decision.event_type != "decision" or not decision.parent_event_ids:
                        raise PermissionError("synthetic owner run lost canonical decision lineage")
                    first = self._canonical(decision.parent_event_ids[0])
                    if first is None:
                        raise PermissionError("synthetic owner run lost canonical decision first parent")
                    offset = 1 if first.event_type == "qualified_model_output" else 0
                    if len(decision.parent_event_ids) <= offset:
                        raise PermissionError("synthetic owner run decision omits exact context delivery")
                    delivery = decision.parent_event_ids[offset]
                    delivered = self._canonical(delivery)
                    if delivered is None or delivered.event_type != "context_delivery":
                        raise PermissionError("synthetic owner run decision parent is not context delivery")
                    context = f.comparison.metadata(f.run_id, "context:" + delivery)
                    if context is None or context.record["kind"] != "context":
                        raise PermissionError("synthetic owner run lost exact successful context")
                    parents.add(context.event_id)
            if sorted(parents) != body["parent_event_ids"]:
                raise PermissionError("synthetic owner run changed exact attempt/control parents")
        self._approve_typed_target(record.event_id, kind=kind, control=record)

    @contextmanager
    def notifications(self):
        original_put, original_register = XTDBComparisonCustody._put, XTDBComparisonCustody.register_recorded
        broker = self
        def register(custody, recorded):
            result = original_register(custody, recorded)
            broker.receipt_proposal(custody, recorded)
            return result
        def put(custody, **kwargs):
            record = original_put(custody, **kwargs)
            broker.control_proposal(custody, record)
            return record
        with patch.object(XTDBComparisonCustody, "register_recorded", register), patch.object(XTDBComparisonCustody, "_put", put):
            yield self

class RegisteredFunctionalCase:
    """One real registered chronology plus fictional supplied producer receipts."""
    def __init__(self, test, *, run_id):
        self.test, self.run_id, self.experiment_id = test, run_id, run_id + "-exp"
        self.base = support.SelectedPhaseHistoryRoutesTest()
        self.base.setUp()
        test.addCleanup(self.base.doCleanups)
        self.f = self.base.f
        self.ports, self.opened_connections = {}, []
        self.provider_tasks = {}
        self.boundary_hook = None
        self.owner_actions_enabled = True

    def __getattr__(self, name):
        return getattr(self.test, name)

    def grant(self, event_id, purpose):
        source = self.f.registry.lookup(event_id)
        if source is None:
            raise ValueError("fixture owner can only grant actual registered sources")
        if self.f.policy.permits(source, purpose):
            return
        prior = self.f.policy.current_action(event_id, purpose)
        if prior is not None and prior.decision != "allow":
            raise PermissionError("fixture setup may not regrant an explicit deny/revoke")
        for parent_id in source.evidence.parent_refs:
            self.grant(parent_id, purpose)
        if not self.f.policy.permits(source, purpose):
            self.base.eval_grant(source, purpose)

    def control_grants(self, store):
        """Explicit enrolled owner actions after each actual control append."""
        for kind in ("anchor", "before_seal", "update_gate", "update", "final_seal"):
            record = store._metadata(kind)
            if record is not None:
                for operation in ("capture", "read"):
                    self.grant(record.event_id, preregistration_purpose(store.run_id, operation))
        for slot in store.spec.slots:
            record = store._metadata("slot", slot.snapshot_id)
            if record is not None:
                for operation in ("capture", "read"):
                    self.grant(record.event_id, preregistration_purpose(store.run_id, operation))

    def signed(self, payload):
        return canonical_json_bytes({"payload": payload, "signature": base64.b64encode(
            self.f.qualification_key.sign(canonical_json_bytes(payload))).decode()})

    def replace_personality(self):
        f, role = self.f, "personality_judgment"
        payload = b"fictional new checkpoint produced only after the canonical update gate"
        checkpoint = Path(f.fabric.directory.name) / "preregistered-after-personality.checkpoint"
        checkpoint.write_bytes(payload)
        manifest = ArtifactManifest(f.scope, "fictional-preregistered-after-personality", role,
            "fictional-repo", "fictional-branch", "a" * 40, sha(payload), len(payload),
            f.codec.input_contract_id, f.codec.input_contract_sha256, f.codec.output_contract_id, f.codec.output_contract_sha256)
        receipt = self.signed({"schema": "fictional-qualification-v1", "qualifier_id": "fictional-independent-qualifier",
            "qualification_id": "fictional-preregistered-after-qualified", "manifest_sha256": manifest.manifest_sha256,
            "runtime_allowed": True})
        f.artifacts.admit(manifest=manifest, checkpoint_path=checkpoint, external_receipt=receipt,
            verifier=f.qualifier, expected_previous_artifact_id="fictional-personality_judgment", expected_previous_generation=1)
        f.bindings[role] = replace(f.bindings[role], checkpoint_path=checkpoint)
        # Retain every actual source/state/custody controller. Only the actual
        # producer port changes; no live Claim or artifact head is rewound.
        f.runtime.bindings[role] = f.bindings[role]

    def build(self):
        started = time.monotonic()
        def completed(label):
            print(f"[history-preregistration] {label}: elapsed={time.monotonic() - started:.3f}s", flush=True)
        phase_labels = {
            ("before", "flora_full"): "before-full",
            ("before", "same_evidence_ablation"): "before-ablation",
            ("after", "flora_full"): "after-full",
            ("after", "same_evidence_ablation"): "after-ablation",
        }
        f, run_id, exp = self.f, self.run_id, self.experiment_id
        original = f.fabric._source(b"fictional two-stage before evidence")
        correction = f.fabric._source(b"fictional two-stage corrected evidence", correction_parent=original.event_id)
        training = f.fabric._source(b"independent fictional recipe input, excluded from heldout history")
        for event in (original, correction):
            f._judgment_permission(f.registry.lookup(event.event_id))
        bundle, candidates = f.fabric._bundle(original, prefix="preregistered-original")
        bound, at = f.fabric._prepare(bundle, candidates)
        adjudication = support._rf._semantic_fixture.fixture_adjudication(bound, at=at)
        f.fabric.semantic_proof.approve_fixture(adjudication, bound)
        accepted = f.fabric._admit(bound, adjudication, candidates)
        f.qualifier = FictionalPreregisteredQualifier(f.qualification_key.public_key())
        f._artifact("memory_formation")
        f._artifact("personality_judgment")
        old_bindings = dict(f.bindings)
        old_state = f._state_activation(accepted, original)
        completed("source-and-baseline-setup-complete")
        context_plan = ContextPlan("preregistered-exact-selection", "personal_judgment",
            exact_claim_ids=(accepted.claim_id,), minimum_claims=1,
            state_routes=(StateRoute("owner", f.scope.host_instance_id, old_state.projection_id),))
        histories, question, design_plan = support._cf.inputs(f.scope.host_instance_id,
            actual_sources=[SourceMaterial(event, f.objects.get(f.references.get(event.payload_reference)))
                for event in (original, correction)])
        question_event = f.fabric._source(question)
        originals = (training, original, correction, question_event)
        local = SelectedSourceAuthority(f.registry, f.log, f.policy, f.objects)
        for event in originals:
            for operation in ("capture", "read"):
                self.grant(event.event_id, manifest_purpose(exp, operation))
            self.grant(event.event_id, cohort_source_purpose(exp, "training" if event == training else "heldout"))
        for phase in ("before", "after"):
            for event_id in histories[("case", phase)].event_ids + (question_event.event_id,):
                self.grant(event_id, evaluation_purpose(run_id, "case", phase))
        lineage_key, result_key = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
        manifests = XTDBExperimentManifestCustody(experiment_id=exp, local=local, authorities=(local,),
            connection=f.connection, control_anchor_event_id=training.event_id,
            lineage_public_key=public(lineage_key), approved_lineage_key_sha256=sha(public(lineage_key)),
            qualification_public_key=public(result_key), approved_qualification_key_sha256=sha(public(result_key)),
            part1_validator=None, clock=f.fabric._time)
        entries = tuple(CohortEntry("entry-" + str(index), local.authority_id, event.event_id,
            "training" if event == training else "heldout", "recipe-family" if event == training else "heldout-family",
            "fixture-generator", "a" * 64, "recipe-scenario" if event == training else "heldout-scenario", (),
            "recipe-person" if event == training else "heldout-person", "host",
            "question" if event == question_event else "authorized_history") for index, event in enumerate(originals))
        rules = (SplitIsolationRule("heldout", "training", tuple(sorted({"source_family", "scenario_ancestry",
            "person_family", "source_ancestry"})), ("generator_family",)),)
        cohort_body = {"entries": [entry.record() for entry in entries], "rules": [rule.record() for rule in rules],
            "bindings": {entry.entry_id: local.binding(entry.event_id) for entry in entries}}
        claim = {"schema": "flora-cohort-lineage-attestation-v1", "experiment_id": exp,
            "enrolled_key_sha256": sha(public(lineage_key)), "actual_family_ancestry_verified": True,
            "cohort_sha256": canonical_sha256(cohort_body)}
        cohort = manifests.register_cohort(cohort_id="cohort", entries=entries, rules=rules,
            lineage_claim=claim, lineage_proof=lineage_key.sign(encoded(claim)))
        completed("cohort-registered")
        self.grant(cohort["event_id"], manifest_purpose(exp, "read"))
        recipe = manifests.register_recipe(recipe_id="recipe", cohort_id="cohort",
            code_files=(("tests/registered_functional_case_fixture.py", Path(__file__).read_bytes()),),
            dependency_lock=b"fictional fixture lock: no model training", role_contracts=(("personality", b"supplied producer port"),),
            source_choices=(("entry-0", "eligible"),), stop_defer_contract=b"supplied fixture stop/defer contract")
        completed("recipe-registered")
        self.grant(recipe["event_id"], manifest_purpose(exp, "read"))
        comparison = XTDBComparisonCustody(scope=f.scope, authority_namespace_id=f.namespace,
            connection=f.connection, registry=f.registry, objects=f.objects, log=f.log)
        store = XTDBExperimentPreregistrationCustody(comparison=comparison, manifests=manifests,
            cohort_id="cohort", recipe_id="recipe", permissions=f.policy, clock=f.fabric._time)
        design, selection = b"supplied fictional baseline design", b"supplied exact two-stage selection contract"
        protocol = replace(design_plan.protocol, protocol_id="connected-functional-mechanics-v1", wall_time_budget_ms=OPERATING_BOUNDS["attempt_ms"], baseline_design_sha256=sha(design), builder_recipe_sha256=recipe["content_sha256"])
        self.construct_ports()
        baseline_roles = {role: f.runtime._resolve(role)[1] for role in old_bindings}
        arms = ("flora_full", "same_evidence_ablation")
        slots = tuple(CaptureSlotDeclaration("case", phase, arm, "v2-" + phase + "-" + arm,
            "capture-" + phase + "-" + arm, "evaluation-" + phase + "-" + arm, sha(selection),
            "withhold_personal_judgment_update" if phase == "after" and arm == "same_evidence_ablation" else "full_update")
            for phase in ("before", "after") for arm in arms)
        spec = ExperimentPreregistration(f.scope, f.namespace, run_id, protocol, {"case": sha(question)},
            20000, 20000, 1, "contract_fixture", support._cf.configuration(), design,
            {arm: NativeArmDeclaration(arm, self.ports[arm].worker.manifest, f.bindings["personality_judgment"].adapter.adapter_id,
                "fixture-supplied-update") for arm in arms}, baseline_roles,
            {role: b"supplied role qualification contract" for role in old_bindings}, selection,
            b"supplied exact update contract", b"supplied before role nomination", slots,
            {("case", phase): "provider-" + phase for phase in ("before", "after")},
            {"case": "before-separate-probe"}, {"case": ("actual-fixture-update",)})
        for record in (cohort, recipe):
            for operation in ("capture", "read"):
                self.grant(record["event_id"], preregistration_purpose(run_id, operation))
        anchor = store.register(spec=spec, histories=histories, questions={"case": question})
        completed("anchor-registered")
        self.control_grants(store)
        self.assertIsNone(store._metadata("final_seal"))
        self.assertNotIn("phase_bindings", store.recover_control(kind="anchor"))
        self.assertNotIn("run_plan_sha256", store.recover_control(kind="anchor"))
        store.register_original_inputs(occurred_at=f.fabric._time())
        completed("original-inputs-registered")
        for phase in ("before", "after"):
            self.grant(comparison.metadata(run_id, "history:case:" + phase).event_id,
                evaluation_purpose(run_id, "case", phase))
        archive = XTDBPhaseSnapshotCustody(runtime=f.runtime, run_id=run_id, preregistration=anchor,
            clock=f.fabric._time)
        store.bind_phase_custody(archive)
        authority = anchor.history_authority()
        def lineage(slot, runtime=None):
            return PreregisteredPhaseCaptureLineageVerifier(runtime=runtime or f.runtime, preregistration=anchor,
                snapshot_id=slot.snapshot_id, case_id=slot.case_id, phase=slot.phase, arm=slot.arm,
                history_for=anchor.history_for,
                phase_receipt_for=lambda request: support._lf.fictional_phase_receipt(request, f.qualification_key))
        captured, bindings = {}, {}
        def capture(slot, *, ports, **kwargs):
            store.bind_historical_bindings(snapshot_id=slot.snapshot_id, bindings=ports)
            bindings[slot.snapshot_id] = ports
            snapshot = archive.capture(snapshot_id=slot.snapshot_id, case_id=slot.case_id,
                phase=slot.phase, arm=slot.arm, plan=context_plan, lineage=lineage(slot),
                history=histories[(slot.case_id, slot.phase)], **kwargs)
            captured[(slot.phase, slot.arm)] = snapshot
            event_id = archive.metadata(slot.snapshot_id)["event_id"]
            f._judgment_permission(f.registry.lookup(event_id))
            for operation in ("capture", "read"):
                self.grant(event_id, preregistration_purpose(run_id, operation))
            route = archive.capture_route(snapshot_id=slot.snapshot_id,
                history_authority=authority, historical_bindings=ports)
            observed = route.observed_binding()
            self.assertEqual(observed.context_lineage_sha256, snapshot.record["context_lineage_sha256"])
            self.assertEqual(route.snapshot.record["context_receipt"], snapshot.record["context_receipt"])
            store.publish_capture(snapshot_id=slot.snapshot_id)
            self.control_grants(store)
            completed(phase_labels[(slot.phase, slot.arm)] + "-capture-published")
            return snapshot
        for slot in slots:
            if slot.phase == "before":
                snapshot = capture(slot, ports=old_bindings)
                self.assertIsNone(archive.run_plan_sha256)
                self.assertEqual(snapshot.record["preregistration_sha256"], anchor.preregistration_sha256)
                self.assertNotIn("run_plan_sha256", snapshot.record)
        before_seal = store.seal_before()
        completed("before-seal-committed")
        self.control_grants(store)
        probe = archive.before_probe_route(snapshot_id=captured[("before", "flora_full")].snapshot_id,
            case_id="case", historical_bindings=old_bindings)
        probe_run = probe.runtime.judge(plan=context_plan, task=question, invocation_id="before-separate-probe")
        self.assertEqual(probe_run.execution.invocation.invocation_id, "before-separate-probe")
        completed("before-probe-complete")
        gate = store.begin_update()
        completed("update-gate-committed")
        self.control_grants(store)
        original_before_bytes = encoded(captured[("before", "flora_full")].record)
        # Genuine actual selected Claim, approved state and artifact heads move
        # only now, after the real before seal and canonical update gate.
        changed_bundle, changed_candidates = f.fabric._bundle(correction, prefix="preregistered-corrected",
            correction_of=accepted.claim_version_id)
        changed, at = f.fabric._prepare(changed_bundle, changed_candidates, identity=bound.interpretation.candidate.identity)
        previous = support._rf._semantic_fixture.fixture_projection(f.claims.load_current(accepted.claim_id))
        decision = support._rf._semantic_fixture.fixture_adjudication(changed, at=at, conflict_id="preregistered-correction-conflict")
        conflict = support._rf._semantic_fixture.fixture_conflict(changed, decision, previous)
        f.fabric.semantic_proof.approve_fixture(decision, changed)
        updated = f.fabric._admit(changed, decision, changed_candidates, expected_previous=previous, conflict=conflict)
        new_state = self.base.next_state(old_state, updated, correction)
        self.replace_personality()
        completed("selected-head-replacement-complete")
        raw = f.objects.put(b"fictional receipt identifies these real moved heads; no learned model claim")
        update_event = ExperienceEvent.create(event_type="observation", scope=f.scope, occurred_at=f.fabric._time(),
            content_digest=raw.plaintext_sha256, provenance=ProvenanceReference.create(provenance_type="derived_inference",
                source_reference_ids=(gate.event_id,), derivation_activity_id="actual-fixture-update",
                responsible_component="fictional-producer"), retention_class="ordinary_experience", storage_tier="raw_buffer",
            parent_event_ids=(gate.event_id,), payload_reference=raw.object_id)
        f.log.append(update_event, expected_revision=len(f.log.replay()) - 1)
        register_experience_source(event_id=update_event.event_id, raw=raw, registry=f.registry, log=f.log,
            objects=f.objects, role="derived_inference", modality="structured")
        for operation in ("capture", "read"):
            self.grant(update_event.event_id, preregistration_purpose(run_id, operation))
        position = next(item.stream_position for item in f.log.replay_committed() if item.event == update_event)
        update_request = {"schema": "flora-preregistered-update-request-v1", "scope": f.scope.metadata_record(),
            "authority_namespace_id": f.namespace, "run_id": run_id, "preregistration_sha256": anchor.preregistration_sha256,
            "before_seal_event_id": before_seal.event_id, "before_seal_record_sha256": before_seal.record["record_sha256"],
            "update_gate_event_id": gate.event_id, "update_gate_event_sha256": gate.record["event_sha256"],
            "update_contract_sha256": sha(spec.update_contract), "actual_update_events": [{"event_id": update_event.event_id,
                "event_sha256": update_event.event_sha256, "stream_position": position, "event_type": update_event.event_type}]}
        receipts = {role: self.signed({"schema": "fictional-preregistered-update-v1", "role": role,
            "request_sha256": canonical_sha256({**update_request, "role": role,
                "role_policy_contract_sha256": sha(spec.role_policy_contracts[role])}),
            "qualifier_id": spec.baseline_roles[role].qualifier_id, "allowed": True,
            "authorized_before_execution": True}) for role in old_bindings}
        store.record_update(update_event_ids=(update_event.event_id,), receipts=receipts)
        completed("qualified-update-recorded")
        self.control_grants(store)
        for slot in slots:
            if slot.phase != "after":
                continue
            ports, kwargs = dict(f.bindings), {}
            if slot.arm == "same_evidence_ablation":
                before = captured[("before", "flora_full")]
                policy = FrozenPhaseUpdatePolicy("withhold_personal_judgment_update", before.snapshot_id,
                    before.snapshot_sha256, (correction.event_id,))
                def current():
                    anchor.authorize_slot_capture(snapshot_id=slot.snapshot_id, case_id="case", phase="after",
                        arm=slot.arm, history=histories[("case", "after")], plan=context_plan)
                    archive.authorize(snapshot_id=before.snapshot_id, history=histories[("case", "before")],
                        history_authority=authority)
                    archive._sources_now(histories[("case", "after")].event_ids, claim_ids=(accepted.claim_id,))
                derived = derive_preregistered_ablation_runtime(custody=archive, before_snapshot=before,
                    personality_binding=old_bindings["personality_judgment"], authority_guard=current)
                actual = lineage(slot, derived).context_lineage(case_id="case", phase="after",
                    history=histories[("case", "after")], context=derived._context(context_plan, authority_guard=current),
                    authority_guard=current)
                artifact = derived._resolve("personality_judgment", authority_guard=current)[1]
                request = {"schema": "flora-phase-update-exclusion-request-v2", "scope": f.scope.metadata_record(),
                    "authority_namespace_id": f.namespace, "run_id": run_id, "preregistration_sha256": anchor.preregistration_sha256,
                    "case_id": "case", "phase": "after", "arm": slot.arm,
                    "history_sha256": histories[("case", "after")].digest(), "context_lineage_sha256": actual.lineage_sha256,
                    "update_policy": policy.record(), "artifact_manifest_sha256": artifact.manifest_sha256}
                receipt = self.signed({"schema": "fictional-anchored-update-exclusion-v1",
                    "request_sha256": canonical_sha256(request), "artifact_manifest_sha256": artifact.manifest_sha256,
                    "qualifier_id": artifact.qualifier_id, "qualification_id": artifact.qualification_id, "allowed": True})
                ports["personality_judgment"] = old_bindings["personality_judgment"]
                kwargs = {"update_policy": policy, "update_receipt": receipt,
                    "ablation_personality_binding": old_bindings["personality_judgment"]}
            capture(slot, ports=ports, **kwargs)
        self.assertEqual(encoded(archive.recover(snapshot_id=captured[("before", "flora_full")].snapshot_id,
            history=histories[("case", "before")], history_authority=authority).record), original_before_bytes)
        final = store.finalize()
        completed("final-seal-committed")
        self.control_grants(store)
        store.register_final_inputs(final_authority=final, occurred_at=f.fabric._time())
        completed("final-inputs-registered")
        self.assertEqual(final.plan.preregistration_sha256, anchor.preregistration_sha256)
        snapshots = {(slot.case_id, slot.phase, slot.arm): final.native_plans[slot.arm].entry(slot.case_id, slot.phase).phase_snapshot
            for slot in slots}
        history_authority = SelectedRunEvidencePolicy(custody=comparison, run_id=run_id, permissions=f.policy,
            final_authority=final)
        router = SelectedPhaseLineageRouter(custody=archive, run_plan=final.plan, histories=histories,
            history_authority=history_authority, bindings_by_snapshot=bindings, snapshots=snapshots,
            frozen_native_arms=final.native_plans, final_authority=final)
        native_policy = SelectedRunEvidencePolicy(custody=comparison, run_id=run_id, permissions=f.policy,
            native_lineage=router, final_authority=final)
        requests, results, judgments = {}, {}, {}
        for slot in slots:
            route = router.route_for(case_id="case", phase=slot.phase, arm=slot.arm)
            expected = accepted.claim_version_id if slot.phase == "before" else updated.claim_version_id
            self.assertEqual(route.runtime.claims.load_current(accepted.claim_id)["current_claim_version_id"], expected)
            actual_checkpoint = route.runtime._resolve("personality_judgment")[1].checkpoint_sha256
            self.assertEqual(actual_checkpoint, baseline_roles["personality_judgment"].checkpoint_sha256
                if slot.phase == "before" or slot.arm == "same_evidence_ablation"
                else f.runtime._resolve("personality_judgment")[1].checkpoint_sha256)
            judged = route.runtime.judge(plan=context_plan, task=question, invocation_id=slot.evaluation_invocation_id)
            request = ExecutionRequest("case", slot.phase, question, f.scope, histories[("case", slot.phase)].digest(),
                histories[("case", slot.phase)].event_ids, judged.context, final.plan.binding_for("case", slot.phase, slot.arm), final.plan)
            result = ArmResult(judged.execution.result.output, judged.delivery, judged.decision,
                MeasuredUsage(final.plan.protocol.feature_engine_id, 1, 1, 1, 0))
            qualified = router.verify_native_result(request, result, arm=slot.arm)
            for record in (judged.delivery, qualified, judged.decision):
                route.check_live()
                comparison.register_recorded(record)
            requests[(slot.phase, slot.arm)], results[(slot.phase, slot.arm)] = request, result
            judgments[(slot.phase, slot.arm)] = judged
            completed(phase_labels[(slot.phase, slot.arm)] + "-result-qualified")
        self.__dict__.update(dict(manifests=manifests, cohort=cohort, recipe=recipe, comparison=comparison,
            store=store, archive=archive, final=final, router=router, evidence=native_policy,
            histories=histories, question=question, question_event=question_event, slots=slots,
            bindings=bindings, requests=requests, results=results, judgments=judgments,
            original=original, correction=correction, accepted=accepted, updated=updated,
            old_state=old_state, new_state=new_state, old_bindings=old_bindings,
            baseline_roles=baseline_roles, context_plan=context_plan, before_seal=before_seal, gate=gate,
            history_entry_ids={("case", "before"): ("entry-1",), ("case", "after"): ("entry-1", "entry-2")},
            question_entry_ids={"case": "entry-3"}))
        for port in self.ports.values():
            port.meter.judgments = port.codec.judgments = judgments
        for ports in (old_bindings, *bindings.values(), f.bindings):
            for binding in ports.values():
                binding.adapter.invoke = lambda *_: self.fail("passive connected fixture invoked a model")
        return self

    def construct_ports(self):
        """Declare concrete ports before registration; final data are bound later."""
        f, bounds = self.f, OPERATING_BOUNDS
        ownership = SignedFixtureWriterQualifier()
        owner_configuration = NativeWriterConfiguration(f.scope, f.namespace, "connected-fixture-owner",
            psycopg.__version__, sha(b"one actual owner thread; shared guard serializes both native arms"),
            bounds["writer_operation_ms"])
        self.writer_guard = NativeWriterGuard(connection=f.connection, configuration=owner_configuration,
            verifier=ownership, qualification_receipt=b"receipt initialized before preregistration",
            qualifier_id="fixture-owner-qualifier", qualification_id="fixture-owner-qualification")
        self.writer_guard.qualification_receipt = ownership.receipt(self.writer_guard._request)
        parameters = conninfo_to_dict(f.connection.info.dsn)
        program = ("import sys,json,hashlib\nraw=sys.stdin.buffer.read()\nr=json.loads(raw)\n"
            "sys.stdout.write(json.dumps({'invocation_id':r['invocation_id'],"
            "'worker_request_sha256':hashlib.sha256(raw).hexdigest(),"
            "'qualified_output_event_id':r['output_event'],'meter':r['meter']},sort_keys=True,separators=(',',':')))\n")
        for arm in ("flora_full", "same_evidence_ablation"):
            reader_configuration = BoundedXTDBReadConfiguration(f.connection.info.hostaddr,
                int(f.connection.info.port), f.connection.info.dbname, f.connection.info.user, psycopg.__version__,
                bounds["connect_seconds"], bounds["backend_query_ms"], bounds["read_session_ms"],
                maximum_concurrent_sessions=bounds["reader_concurrency_per_arm"])
            opener = BoundedXTDBReadOpener(configuration=reader_configuration,
                credentials=ExplicitXTDBReadCredentials(parameters.get("password") or "explicit-fixture-trust"))
            def open_owned(*, read_timeout_ms, _opener=opener):
                connection = _opener(read_timeout_ms=read_timeout_ms)
                self.opened_connections.append(connection)
                return connection
            artifact = sha(Path(__file__).read_bytes())
            configuration = canonical_sha256({"schema": "connected-owned-read-config-v1", "arm": arm,
                "opener": reader_configuration.record(), "operation_ms": bounds["read_operation_ms"],
                "allow_current_fixture_route": False})
            factory = InitializedNativeSessionFactory(artifact_sha256=artifact, configuration_sha256=configuration,
                connection_opener=open_owned, bind_initialized=self.bind_owned_read,
                backend_read_timeout_ms=bounds["backend_query_ms"])
            manifest = NativeReadManifest(f.scope, f.namespace, artifact, configuration,
                bounds["reader_concurrency_per_arm"], bounds["read_operation_ms"], bounds["backend_query_ms"],
                allow_current_fixture_route=False)
            reads = SelectedNativeReadServices(manifest=manifest, factory=factory)
            meter, temporary = ConnectedFixtureMeter(arm), tempfile.TemporaryDirectory()
            self.test.addCleanup(temporary.cleanup)
            codec = ConnectedFixtureCodec(arm, meter)
            worker = native_fixture.worker_fixture.worker_fixture(temporary.name, program,
                wall_ms=bounds["relay_wall_ms"], maximum_output=bounds["relay_output_bytes"],
                scope=f.scope, namespace=f.namespace)
            worker.manifest = replace(worker.manifest, worker_id="connected-relay-" + arm,
                codec_artifact_sha256=codec.artifact_sha256,
                read_service_artifact_sha256=reads.artifact_sha256,
                read_service_configuration_sha256=reads.configuration_sha256,
                meter_artifact_sha256=meter.artifact_sha256, meter_configuration_sha256=meter.configuration_sha256,
                writer_guard_artifact_sha256=self.writer_guard.artifact_sha256,
                writer_guard_configuration_sha256=self.writer_guard.configuration_sha256,
                maximum_input_bytes=bounds["relay_input_bytes"], maximum_stderr_bytes=bounds["relay_stderr_bytes"],
                maximum_artifact_bytes=bounds["relay_artifact_bytes"], terminate_grace_ms=bounds["relay_terminate_grace_ms"])
            key = Ed25519PrivateKey.generate()
            payload = {"schema": "fictional-worker-qualification-v1", "manifest": worker.manifest.manifest_sha256}
            worker.qualification_receipt = canonical_json_bytes({"payload": payload, "signature": base64.b64encode(
                key.sign(canonical_json_bytes(payload))).decode()})
            worker.verifier = native_fixture.worker_fixture.FictionalWorkerQualifier(key.public_key())
            self.ports[arm] = SimpleNamespace(worker=worker, codec=codec, meter=meter, reads=reads,
                manifest_before_registration=worker.manifest.record(), read_configuration=reader_configuration)

    def bind_owned_read(self, connection):
        """Same final chronology on exclusively owned SELECT-only connections."""
        f, final, comparison, bindings = self.f, self.final, self.comparison, self.bindings
        registry, policy, claims, candidates = map(copy, (f.registry, f.policy, f.claims, f.candidates))
        for service in (registry, policy, claims, candidates):
            service.connection = connection
        policy.registry = registry
        state, artifacts, personal = map(copy, (f.state, f.artifacts, f.private))
        for service in (state, artifacts, personal):
            service.connection = connection
        state.registry, state.policy = registry, policy
        references = DurablePersonalReferences(custody=personal, originals=registry)
        owner = copy(f.owner_verifier)
        owner.proofs = copy(owner.proofs)
        owner.proofs.custody = personal
        admission = copy(f.admission)
        admission.authority, admission.candidates = claims, candidates
        runtime = FloRAExperimentRuntime(artifacts=artifacts, bindings=f.bindings, claims=claims,
            sources=registry, source_policy=policy, candidates=candidates, admission=admission,
            state=state, log=f.log, objects=f.objects, references=references,
            context_policy=RegisteredJudgmentContextPolicy(claims=claims, state=state, log=f.log,
                registry=registry, permissions=policy), state_approval_verifier=owner, clock=f.fabric._time)
        runtime.private.register = lambda *_: self.fail("passive reader tried to register private custody")
        metadata_final = final.bind_read_connection(connection)
        owned_archive = XTDBPhaseSnapshotCustody(runtime=runtime, run_id=self.run_id,
            preregistration=metadata_final.store.anchor, clock=f.fabric._time)
        owned_final = final.bind_read_connection(connection, phase_custody=owned_archive,
            historical_bindings_by_snapshot=bindings)
        owned_final.store.comparison._physical_custody = comparison
        owned_archive = owned_final.store.phase_custody
        evidence = SelectedRunEvidencePolicy(custody=owned_final.store.comparison, run_id=self.run_id,
            permissions=policy, final_authority=owned_final)
        representative = NativeJudgmentLineageVerifier(runtime=runtime, run_plan_sha256=final.plan.digest(),
            history_authority=evidence, history_for=owned_final.store.anchor.history_for,
            invocation_id_for=lambda request, result: "not-a-phase-authority",
            phase_receipt_for=lambda request: (_ for _ in ()).throw(PermissionError("phase proof needs exact archive")))
        def resolve(*, entry, request, artifact_permissions):
            archive_view = copy(owned_archive)
            archive_view.artifact_permissions = artifact_permissions
            archive_view.artifact_source_policy = copy(owned_archive.artifact_source_policy)
            archive_view.artifact_source_policy.permissions = artifact_permissions
            archive_view.artifact_source_policy.state = copy(owned_archive.artifact_source_policy.state)
            archive_view.artifact_source_policy.state.policy = artifact_permissions
            route = support.SelectedPhaseRoute(custody=archive_view, snapshot_id=entry.phase_snapshot.snapshot_id,
                history=self.histories[(entry.case_id, entry.phase)], history_authority=representative.history_authority,
                historical_bindings=bindings[entry.phase_snapshot.snapshot_id], final_authority=owned_final,
                invocation_id_for=lambda *_: entry.invocation_id)
            if self.boundary_hook is not None:
                self.boundary_hook(route, entry, request)
            return route
        return NativeReadSession(runtime, representative, (connection,), resolve)

    def connect(self, vectors):
        f, config = self.f, self.store.spec.comparator
        compiler, tokenizer = comparator_fixture.FixtureCompiler(), comparator_fixture.FixtureByteCounter()
        memory = QdrantOriginalMemory(custody=self.comparison, run_id=self.run_id, configuration=config,
            client=vectors, embeddings=comparator_fixture.FixtureEmbeddings(), tokenizer=tokenizer,
            wire_compiler=compiler, evidence=self.evidence)
        disclosure = SelectedComparatorDisclosure(custody=self.comparison, run_id=self.run_id, configuration=config,
            permissions=f.policy, wire_compiler=compiler, evidence=self.evidence)
        transport_key = Ed25519PrivateKey.generate()
        observer_public = public(transport_key)
        exchange_verifier = Ed25519TransportObservationVerifier(configuration=config.provider, public_key=observer_public)
        provider_custody = XTDBProviderAttemptCustody(comparison=self.comparison, evidence=self.evidence,
            permissions=f.policy, input_verifier=OriginalMemoryProviderInputVerifier(configuration=config, compiler=compiler),
            tokenizer=tokenizer, tokenizer_artifact_sha256=config.memory.tokenizer_artifact_sha256,
            tokenizer_configuration_sha256=config.memory.tokenizer_configuration_sha256,
            observer_public_key=observer_public, approved_observer_public_key_sha256=sha(observer_public), clock=f.fabric._time)
        fixture = self
        class SuppliedContractClient:
            configuration = config.provider
            calls = 0
            async def generate(self, request, *, authorize_transfer, attempt_sink):
                self.calls += 1
                marker = authorize_transfer()
                output = b"Supplied fictional output. No model inference occurred."
                response_bytes = encoded({"model": "fixture-snapshot", "status": "completed",
                    "output": [{"type": "message", "role": "assistant", "status": "completed", "content": [
                        {"type": "output_text", "text": output.decode()}]}],
                    "usage": {"input_tokens": len(request.payload), "output_tokens": 9}})
                metadata = {"schema": "flora-openai-transport-attempt-v1", "configuration_sha256": config.provider.digest(),
                    "request_sha256": sha(request.payload), "authorization_marker": marker, "response_sha256": sha(response_bytes),
                    "http_status": 200, "response_complete": True, "request_id": "fixture-request", "result": "success",
                    "returned_model_id": "fixture-snapshot", "usage": {"feature_engine_id": "fixture-feature",
                        "context_tokens": len(request.payload), "input_tokens": len(request.payload), "output_tokens": 9,
                        "feature_calls": 1, "cost_microunits": None, "currency": None},
                    "cost_microunits": None, "observer_public_key_sha256": sha(observer_public)}
                attempt_sink.record(TransportAttempt(metadata, request.payload, response_bytes, transport_key.sign(encoded(metadata))))
                response = ProviderResponse(config.provider.digest(), sha(request.payload), "fixture-request", "fixture-snapshot",
                    response_bytes, output, len(request.payload), 9, marker, b"unsigned")
                response = replace(response, proof=transport_key.sign(encoded(response.observation())))
                if attempt_sink.body["task_id"] in fixture.provider_tasks:
                    raise PermissionError("fictional provider task was already supplied once")
                fixture.provider_tasks[attempt_sink.body["task_id"]] = attempt_sink, response
                return response
        self.provider = SuppliedContractClient()
        recorder = SelectedComparatorRecorder(custody=self.comparison, run_id=self.run_id, configuration=config,
            disclosure=disclosure, exchange_verifier=exchange_verifier, clock=f.fabric._time)
        baseline = GeneralMemoryArmAdapter(configuration=config, memory=memory, tokenizer=tokenizer,
            wire_compiler=compiler, client=self.provider, exchange_verifier=exchange_verifier, disclosure=disclosure,
            recorder=recorder, attempt_custody=provider_custody,
            task_id_for=lambda request: self.store.spec.provider_task_ids[(request.case_id, request.phase)])
        self.adapters = {arm: NativeArmAdapter(run_id=self.run_id, run_plan=self.final.plan,
            frozen=self.final.native_plans[arm], custody=self.comparison, worker=port.worker, codec=port.codec,
            reads=port.reads, meter=port.meter, writer_guard=self.writer_guard, final_authority=self.final)
            for arm, port in self.ports.items()}
        self.adapters["general_model_memory"] = baseline
        self.provider_custody, self.memory = provider_custody, memory
        self.coordinator = RegisteredExperimentCoordinator(manifests=self.manifests, cohort_id="cohort", recipe_id="recipe",
            comparison=self.comparison, evidence=self.evidence,
            assessment=XTDBAssessmentCustody(comparison_custody=self.comparison, signature_authority=object()),
            plan=self.final.plan, histories=self.histories, questions={"case": self.question}, native_plans=self.final.native_plans,
            history_entry_ids=self.history_entry_ids, question_entry_ids=self.question_entry_ids,
            provider_task_ids=self.store.spec.provider_task_ids, phase_router=self.router, provider_custody=provider_custody,
            final_authority=self.final, clock=f.fabric._time)
        initial = (*self.coordinator._manifest_records.values(), *self.coordinator._input_records.values())
        for record in initial:
            event_id = record["event_id"] if isinstance(record, dict) else record.event_id
            for operation in ("capture", "read"):
                self.grant(event_id, coordinator_purpose(self.experiment_id, self.run_id, operation))
        # These known native outputs already exist before coordinator execution.
        # Initial owner actions explicitly enumerate their actual parent closure.
        for judged in self.judgments.values():
            for record in (judged.delivery, judged.decision, judged.execution.output_record):
                for operation in ("capture", "read"):
                    self.grant(record.event.event_id, coordinator_purpose(self.experiment_id, self.run_id, operation))
        for event_id in (self.original.event_id, self.correction.event_id,
                self.comparison.metadata(self.run_id, "question:case").event_id,
                *(self.comparison.metadata(self.run_id, "history:case:" + phase).event_id for phase in ("before", "after"))):
            self.grant(event_id, capture_purpose(self.run_id))
        for event_id in (self.original.event_id, self.correction.event_id, self.comparison.metadata(self.run_id, "question:case").event_id):
            self.grant(event_id, "comparison_external:fixture-provider")
        binding = self.coordinator.prepare()
        for operation in ("capture", "read"):
            self.grant(binding.event_id, coordinator_purpose(self.experiment_id, self.run_id, operation))
        return self

    async def close_readers(self):
        for port in self.ports.values():
            await port.reads.aclose()
            self.assertEqual(len(port.reads._pending), 0)

    def native_adapter(self, arm):
        port = self.ports[arm]
        return NativeArmAdapter(run_id=self.run_id, run_plan=self.final.plan,
            frozen=self.final.native_plans[arm], custody=self.comparison, worker=port.worker, codec=port.codec,
            reads=port.reads, meter=port.meter, writer_guard=self.writer_guard, final_authority=self.final)

    @contextmanager
    def fresh_comparison_reader(self):
        """Reopen actual selected rows/objects/log with no retained run controller."""
        f = self.f
        parameters = conninfo_to_dict(f.connection.info.dsn)
        opener = BoundedXTDBReadOpener(configuration=self.ports["flora_full"].read_configuration,
            credentials=ExplicitXTDBReadCredentials(parameters.get("password") or "explicit-fixture-trust"))
        connection = opener(read_timeout_ms=OPERATING_BOUNDS["backend_query_ms"])
        client = KurrentDBClient(os.environ.get("KURRENTDB_URI", "kurrentdb://127.0.0.1:2113?tls=false"))
        try:
            objects = EncryptedObjectPlane(scope=f.scope, key=f.objects._key,
                backend=LocalObjectBackend(f.objects.backend.root))
            log = KurrentExperienceLog(scope=f.scope, client=client)
            registry = XTDBFormationSourceRegistry(scope=f.scope, authority_namespace_id=f.namespace, connection=connection)
            policy = XTDBFormationPermissionPolicy(scope=f.scope, authority_namespace_id=f.namespace,
                connection=connection, registry=registry)
            custody = XTDBComparisonCustody(scope=f.scope, authority_namespace_id=f.namespace, connection=connection,
                registry=registry, objects=objects, log=log)
            yield custody, policy
        finally:
            client.close()
            connection.close()
            self.assertTrue(connection.closed)
            self.assertFalse(connection.watchdog_alive)

    def withdraw(self, event_id, purpose):
        """One actual independently signed successor permission action."""
        f = self.f
        source = f.registry.lookup(event_id)
        prior = f.policy.current_action(event_id, purpose)
        if prior is None or prior.decision != "allow":
            raise ValueError("withdrawal needs a successful existing owner grant")
        previous = f.policy._stored_action(prior.action_id)["request_event_id"]
        action = FormationPermissionAction.create(scope=f.scope, authority_namespace_id=f.namespace,
            action_id="connected-withdraw-" + uuid.uuid4().hex, source_ref_id=event_id,
            source_registration_sha256=source.registration_sha256, purpose=purpose, decision="revoke",
            generation=prior.generation + 1, previous_action_sha256=prior.action_sha256,
            authorization_ref="fictional-enrolled-owner", authorized_at=f.fabric._time())
        event, raw = f.fabric._append(formation_permission_payload(action), event_type="formation_permission_action",
            parents=(event_id, previous), at=action.authorized_at, provenance="owner_attested_canonical")
        f.private.register_formation_permission(action=action, request_event_id=event.event_id,
            raw=raw, log=f.log, objects=f.objects)
        f._persist_proof(event, "formation_permission")
        f.policy.apply(action, request_event_id=event.event_id, log=f.log, objects=f.objects,
            references=f.references, verifier=f.owner_verifier)
        self.owner_actions_enabled = False
        return event

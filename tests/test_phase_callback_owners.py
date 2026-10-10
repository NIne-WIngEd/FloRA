"""Bounded actual capture/registered-H ownership; fictional SQL and grants.

Imports the real preregistration controller and its platform dependencies.
There is deliberately no Windows fcntl shim or supplied anchor admission.
"""
from copy import copy
from dataclasses import replace
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from flora.comparator import sha
from flora.evaluation_protocol import EvaluationCase, EvaluationProtocol
from flora.selected.comparison_custody import XTDBComparisonCustody, evaluation_purpose
from flora.selected.experiment_manifests import (
    CohortEntry, SelectedSourceAuthority, XTDBExperimentManifestCustody,
    manifest_purpose, cohort_source_purpose,
)
from flora.selected.experiment_preregistration import (
    CaptureSlotDeclaration, ExperimentPreregistration, NativeArmDeclaration,
    XTDBExperimentPreregistrationCustody,
    preregistration_purpose,
)
from flora.selected.native_worker import NativeWorkerManifest
from test_phase_snapshots import PhaseDefaultVerifierTest
from comparator_fixtures import configuration
from phase_callback_permissions import PhaseHistoryPermissions


class PreregisteredCallbackOwnerTest(PhaseDefaultVerifierTest):
    def registered_history_owner(self):
        f, run_id, experiment = self.f, self.custody.run_id, "callback-owner-exp"
        grants = PhaseHistoryPermissions(f)
        self.history_grants = grants
        permissions = grants.policy
        local = SelectedSourceAuthority(registry=f.registry, log=f.log, objects=f.objects, permissions=permissions)
        keys = (Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate())
        public = tuple(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw) for key in keys)
        histories = self.support.histories
        original = self.support.original_events[0]
        grants.grant_closure(original.event_id, manifest_purpose(experiment, "capture"))
        for event in self.support.original_events:
            grants.grant_closure(event.event_id, cohort_source_purpose(experiment, "heldout"))
        for (case_id, phase), history in histories.items():
            for event_id in history.event_ids:
                grants.grant_closure(event_id, evaluation_purpose(run_id, case_id, phase))
        manifests = XTDBExperimentManifestCustody(experiment_id=experiment, local=local, authorities=(local,),
            connection=f.connection, control_anchor_event_id=original.event_id,
            lineage_public_key=public[0], approved_lineage_key_sha256=sha(public[0]),
            qualification_public_key=public[1], approved_qualification_key_sha256=sha(public[1]),
            part1_validator=None, clock=f._clock)
        entries = tuple(CohortEntry("history-" + str(index), local.authority_id, event.event_id,
            "heldout", "fixture-source", "fixture-generator", "a" * 64, "fixture-scenario", (),
            "fixture-person", "owner", "authorized_history") for index, event in enumerate(self.support.original_events))
        entries += (replace(entries[0], entry_id="question", usage_role="question"),)
        cohort = manifests.register_cohort(cohort_id="cohort", entries=entries, rules=())
        grants.grant_closure(cohort["event_id"], manifest_purpose(experiment, "read"))
        recipe = manifests.register_recipe(recipe_id="recipe", cohort_id="cohort",
            code_files=(("tests/test_phase_callback_owners.py", b"# supplied callback ownership fixture\n"),),
            dependency_lock=b"fixture only", role_contracts=(("personality", b"supplied port"),),
            source_choices=((entries[0].entry_id, "defer"),), stop_defer_contract=b"heldout source stays outside training")
        grants.grant_closure(recipe["event_id"], manifest_purpose(experiment, "read"))
        for record in (cohort, recipe):
            grants.grant_closure(record["event_id"], preregistration_purpose(run_id, "capture"))
        comparison = XTDBComparisonCustody(scope=f.scope, authority_namespace_id=f.namespace,
            connection=f.connection, registry=f.registry, objects=f.objects, log=f.log)
        store = XTDBExperimentPreregistrationCustody(comparison=comparison, manifests=manifests,
            cohort_id="cohort", recipe_id="recipe", permissions=permissions, clock=f._clock)
        design, selection = b"supplied fixture design", b"supplied fixture selection"
        question = histories[("case-one", "before")].sources[0].plaintext
        case = EvaluationCase("case-one", f.scope.host_instance_id, "relevant_correction", "heldout",
            histories[("case-one", "before")].digest(), histories[("case-one", "after")].digest(),
            "c" * 64, self.support.original_events[1].event_id)
        protocol = EvaluationProtocol(protocol_id="callback-owner-protocol", goal_sha256="d" * 64,
            frozen_at=f._clock(), feature_engine_id="fixture-feature", response_token_budget=16,
            wall_time_budget_ms=1000, cases=(case,), baseline_design_sha256=sha(design),
            scoring_rubric_sha256="e" * 64, threshold_spec_sha256="f" * 64,
            builder_recipe_sha256=recipe["content_sha256"], builder_transfer_host_ids=("other-host",))
        worker = NativeWorkerManifest(f.scope, f.namespace, "fictional-worker",
            *("a" * 64 for _ in range(8)), 4096, 4096, 1024, 1000, 100, 8192)
        arms = ("flora_full", "same_evidence_ablation")
        slots = tuple(CaptureSlotDeclaration("case-one", phase, arm, "slot-" + phase + "-" + arm,
            "capture-" + phase + "-" + arm, "evaluation-" + phase + "-" + arm, sha(selection),
            "withhold_personal_judgment_update" if phase == "after" and arm == "same_evidence_ablation" else "full_update")
            for phase in ("before", "after") for arm in arms)
        roles = {role: f.runtime._resolve(role)[1] for role in f.runtime.bindings}
        spec = ExperimentPreregistration(f.scope, f.namespace, run_id, protocol, {"case-one": sha(question)},
            20000, 20000, 1, "contract_fixture", configuration(), design,
            {arm: NativeArmDeclaration(arm, worker, "fixture-producer", "supplied-update") for arm in arms},
            roles, {role: b"supplied policy" for role in roles}, selection,
            b"supplied update", b"supplied nomination", slots,
            {("case-one", phase): "provider-" + phase for phase in ("before", "after")},
            {"case-one": "before-probe"}, {"case-one": ("producer-update",)})
        anchor = store.register(spec=spec, histories=histories, questions={"case-one": question})
        for operation in ("capture", "read"):
            grants.grant_closure(anchor.event_id, preregistration_purpose(run_id, operation))
        store.register_original_inputs(occurred_at=f._clock())
        for (case_id, phase), history in histories.items():
            record = comparison.metadata(run_id, "history:" + case_id + ":" + phase)
            grants.grant_closure(record.event_id, evaluation_purpose(run_id, case_id, phase))
        authority = anchor.history_authority()
        for (case_id, phase), history in histories.items():
            self.assertTrue(authority.authorize_history(case_id=case_id, phase=phase, history=history),
                "registered-H setup must authenticate original history before mutation")
        return authority

    def test_original_history_anchor_replacement_refuses_before_effects(self):
        original = self.registered_history_owner()
        self.support.verifier.history_authority = original.bind_private_guard(lambda: True)
        _, assemblies = self.capture(snapshot_id="unmutated-history-control")
        self.assertEqual(assemblies, 1, "unmutated registered-H actual capture must prepare once")
        qualifier = self.f.runtime.bindings["personality_judgment"].qualification_verifier
        anchor, fired, effects = original.anchor, [], []
        execute, get = self.f.connection.execute, self.f.objects.backend.get_object
        replacement = copy(anchor)
        replacement.store = copy(anchor.store)
        current = replacement.store._current
        def redirected(*args, **kwargs):
            effects.append("replacement authority callback")
            return current(*args, **kwargs)
        replacement.store._current = redirected
        def mutate():
            if not fired:
                fired.append(True)
                original.anchor = replacement
        def sql(*args, **kwargs):
            if fired:
                effects.append("SQL")
            return execute(*args, **kwargs)
        def ciphertext(*args, **kwargs):
            if fired:
                effects.append("ciphertext")
            return get(*args, **kwargs)
        qualifier.callback = mutate
        try:
            with patch.object(self.f.connection, "execute", sql), patch.object(self.f.objects.backend, "get_object", ciphertext):
                with self.assertRaises(PermissionError):
                    self.capture()
        finally:
            qualifier.callback = None
            original.anchor = anchor
        self.assertTrue(fired)
        self.assertEqual(effects, [], "retained H owner was checked only after a protected effect")

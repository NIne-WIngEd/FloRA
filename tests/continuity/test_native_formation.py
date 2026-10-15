"""Native 1.6 contracts and actual authority; runtime replies are explicit fixtures."""
from copy import deepcopy
import unittest

from test_continuity_kernel import KernelFixture
from test_continuity_store import T0


POLICY = dict(role="authenticated_owner_statement", modality="text",
              subject_ref="ari", minimum_sensitivity="private", identity_core_allowed=False)


def answer(context, opened, *, action="propose", domain="host"):
    source = context["base_context"]["experience_refs"][0]
    proposal = dict(proposal_id="estimate", kind="host_observation", domain=domain,
        subject_ref="ari", value_ref="estimate-value", value_text="Project needs four hours.",
        evidence_refs=[source], anchors=[dict(ref_id=source, start_byte=0,
            end_byte=len(dict(opened)[source]), locator=None)], epistemic_status="owner_statement",
        valid_from="2026-10-01T10:00:00.000000Z", valid_to=None, confidence=.6,
        uncertainty_ref=None, contradicts=[], target_refs=[], disposition_scope_ref="host",
        temporal_granularity="instant")
    return {"schema":"mfm-formation-output-v1.6", "proposals": [{"proposal":proposal,
        "sensitivity_hint":"private", "episode":None, "relationship_counterpart_ref":None,
        "mission_target_refs":[], "workspace_target_refs":[]}] if action=="propose" else [],
        "dispositions":[dict(scope_ref="host", action=action, evidence_refs=[source], target_refs=[])]}


class NativeFormationTests(KernelFixture, unittest.TestCase):
    def setUp(self):
        self.make_kernel()

    def native_source(self):
        self.assertTrue(hasattr(self.store, "capture_native"), "typed native source intake is missing")
        source=self.store.capture_native("native-source", "owner", "host",
            b"Project needs four hours.", event_at=T0, policy=POLICY, source_root="one-original")
        self.store.bind_native_subject("host-subject","host","ari",support=[source])
        return source

    def port(self, runtime=answer):
        from flora.continuity.formation import NativeFormationPort
        return NativeFormationPort(self.store.scope, "a"*64, runtime)

    def test_native_meaning_and_exact_independent_acceptance(self):
        source=self.native_source()
        calls=[]
        def runtime(context, opened):
            calls.append((context,opened))
            self.assertEqual(dict(opened)[source], b"Project needs four hours.")
            return answer(context,opened)
        port=self.port(runtime)
        candidate=self.kernel.form_native("native-form","formation",port,source)
        self.assertEqual(self.kernel.form_native("native-form","formation",port,source),candidate)
        self.assertEqual(len(calls),1)
        self.assertFalse(any(r.kind=="memory" for r in self.store.recollect("personality","judgment").records))
        with self.assertRaises(PermissionError):
            self.kernel.accept_native("self-approval","formation",candidate)
        memories=self.kernel.accept_native("accept","owner",candidate)
        memory=self.store.record(memories[0])
        p=memory.value["native_proposal"]["proposal"]
        self.assertEqual(p["value_text"], "Project needs four hours.")
        self.assertEqual(p["confidence"],.6)
        self.assertEqual(p["anchors"][0]["ref_id"],source)
        # Offered legacy evidence has unknown sensitivity: do not lower its floor
        # merely because the model did not cite it.
        self.assertEqual(memory.value["minimum_sensitivity"],"highly_sensitive")
        self.assertEqual(memory.value["native_proposal"]["sensitivity_hint"],"private")
        self.assertIsNone(self.store.recollect("personality","judgment").state("host","hours"))

    def test_explicit_state_binding_retains_typed_value_and_predecessor(self):
        source=self.native_source()
        candidate=self.kernel.form_native("native-form","formation",self.port(),source)
        self.kernel.accept_native("accept","owner",candidate,
            state_bindings={"estimate":{"subject":"host","slot":"workload","predecessor":None}})
        state=self.store.recollect("personality","judgment").state("host","workload")
        self.assertEqual(state.value["content"]["proposal"]["value_text"],"Project needs four hours.")
        self.assertEqual(state.value["epistemic"],"owner_statement")

    def test_abstention_is_preserved_without_fabricated_state(self):
        source=self.native_source()
        port=self.port(lambda c,o:answer(c,o,action="abstain"))
        candidate=self.kernel.form_native("abstain","formation",port,source)
        self.assertEqual(self.kernel.accept_native("accept","owner",candidate),[])
        view=self.store.recollect("personality","judgment")
        decisions=[r for r in view.records if r.kind=="formation_decision"]
        self.assertEqual(decisions[0].value["dispositions"][0]["action"],"abstain")
        self.assertFalse(any(r.kind=="memory" for r in view.records))

    def test_invalid_anchor_and_sensitivity_do_not_publish(self):
        source=self.native_source()
        for defect in ("anchor","sensitivity"):
            def bad(c,o):
                output=answer(c,o)
                if defect=="anchor":output["proposals"][0]["proposal"]["anchors"][0]["end_byte"]=99999
                else:output["proposals"][0]["sensitivity_hint"]="public"
                return output
            before=self.store.recollect("owner","judgment")
            with self.assertRaises(ValueError):
                self.kernel.form_native(defect,"formation",self.port(bad),source)
            self.assertEqual(self.store.recollect("owner","judgment").records,before.records)

    def test_source_policy_cannot_be_promoted_by_observer(self):
        self.assertTrue(hasattr(self.store,"capture_native"))
        with self.assertRaises(PermissionError):
            self.store.capture_native("forged","reader","source_person",b"an assertion",
                event_at=T0,policy=dict(POLICY,role="owner_attested_source_person",identity_core_allowed=True))

    def test_new_evidence_refuses_native_acceptance_and_withdrawal_reaches_memory(self):
        source=self.native_source()
        candidate=self.kernel.form_native("form","formation",self.port(),source)
        self.capture("contradiction",b'{"hours":12}')
        with self.assertRaisesRegex(ValueError,"stale"):
            self.kernel.accept_native("accept","owner",candidate)
        candidate=self.kernel.form_native("fresh","formation",self.port(),source)
        memories=self.kernel.accept_native("fresh-accept","owner",candidate)
        self.kernel.withdraw("withdraw",source)
        self.assertTrue(all(self.store.record(m).status=="withdrawn" for m in memories))

    def test_wrong_subject_binding_cannot_write_source_identity(self):
        source=self.native_source()
        candidate=self.kernel.form_native("form","formation",self.port(),source)
        with self.assertRaises(ValueError):
            self.kernel.accept_native("accept","owner",candidate,
                state_bindings={"estimate":{"subject":"source_person","slot":"anchor","predecessor":None}})


if __name__=="__main__":unittest.main()

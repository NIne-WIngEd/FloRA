"""Rich native semantics, independent authority and native consumer refusal."""
from copy import deepcopy
import unittest
import test_native_formation as formation_tests
import test_native_personality as pe_tests
from test_continuity_kernel import KernelFixture
from test_continuity_store import T0

class NativeRichTests(KernelFixture,unittest.TestCase):
    setUp=pe_tests.NativePersonalityTests.setUp
    native_source=formation_tests.NativeFormationTests.native_source
    formation_port=formation_tests.NativeFormationTests.port
    pe_port=pe_tests.NativePersonalityTests.port

    def test_unknown_subject_and_dangling_targets_cannot_become_state(self):
        source=self.native_source()
        for defect in ("subject","target","contradicts"):
            def bad(c,o):
                output=formation_tests.answer(c,o)
                p=output["proposals"][0]["proposal"]
                if defect=="subject":p["subject_ref"]="another-person"
                else:p["target_refs" if defect=="target" else "contradicts"]=["missing-target"]
                return output
            with self.subTest(defect=defect),self.assertRaises(ValueError):
                candidate=self.kernel.form_native(defect,"formation",self.formation_port(bad),source)
                self.kernel.accept_native("accept-"+defect,"owner",candidate,
                    state_bindings={"estimate":{"subject":"host","slot":"workload-"+defect,"predecessor":None}})
            self.assertIsNone(self.store.recollect("personality","judgment").state("host","workload-"+defect))

    def test_dispositions_and_deletion_requests_do_not_execute_commands(self):
        source=self.native_source()
        for action in ("defer","retain_raw"):
            candidate=self.kernel.form_native(action,"formation",
                self.formation_port(lambda c,o:formation_tests.answer(c,o,action=action)),source)
            self.assertEqual(self.kernel.accept_native("accept-"+action,"owner",candidate),[])
        def request(c,o):
            output=formation_tests.answer(c,o)
            output["proposals"][0]["proposal"].update(kind="deletion_request",target_refs=[source])
            return output
        candidate=self.kernel.form_native("deletion","formation",self.formation_port(request),source)
        with self.assertRaises(ValueError):
            self.kernel.accept_native("bad-state","owner",candidate,
                state_bindings={"estimate":{"subject":"host","slot":"request","predecessor":None}})
        memories=self.kernel.accept_native("accept-deletion","owner",candidate)
        self.assertEqual(self.store.record(source).status,"active")
        self.assertIn(("target_refs",source),self.store.record(memories[0]).links)

    def test_episode_relationship_mission_workspace_and_day_interval(self):
        source=self.native_source()
        entity=self.store.register_native_target("person","entity","world",support=[source])
        scene=self.store.register_native_target("scene","scene","world",support=[source])
        workspace=self.store.register_native_target("workspace","workspace","world",support=[source])
        def rich(c,o):
            output=formation_tests.answer(c,o)
            episode=output["proposals"][0]
            p=episode["proposal"]
            p.update(kind="episode",epistemic_status="inference",evidence_refs=sorted([source,self.mission]),
                anchors=[dict(ref_id=i,start_byte=0,end_byte=len(dict(o)[i]),locator=None)
                         for i in sorted([source,self.mission])],
                valid_from="2026-10-01T00:00:00.000000Z",valid_to="2026-10-01T00:00:00.000000Z",
                temporal_granularity="day")
            episode.update(sensitivity_hint="highly_sensitive",
                episode=dict(event_start="2026-10-01T10:00:00.000000Z",event_end=None,
                    participant_refs=[entity],scene_refs=[scene]),
                mission_target_refs=[self.mission],workspace_target_refs=[workspace])
            relation=deepcopy(episode)
            relation["proposal"].update(proposal_id="relation",value_ref="relation-value",kind="relationship_norm",domain="relationship")
            relation.update(episode=None,relationship_counterpart_ref=entity)
            output["proposals"].append(relation)
            return output
        candidate=self.kernel.form_native("rich","formation",self.formation_port(rich),source)
        memories=self.kernel.accept_native("accept-rich","owner",candidate,
            state_bindings={"estimate":{"subject":"host","slot":"day-event","predecessor":None}})
        self.assertEqual(len(memories),2)
        first=self.store.record(memories[0])
        self.assertIn(("participant_refs",entity),first.links)
        self.assertIn(("scene_refs",scene),first.links)
        self.assertIn(("mission_target_refs",self.mission),first.links)
        self.assertIn(("workspace_target_refs",workspace),first.links)
        self.assertIn(("relationship_counterpart",entity),self.store.record(memories[1]).links)
        state=self.store.state_at("owner","host","day-event",valid_at="2026-10-01T18:00:00+00:00")
        self.assertIsNotNone(state)
        self.assertIsNone(self.store.state_at("owner","host","day-event",valid_at="2026-10-02T00:00:00+00:00"))
        affected=self.kernel.withdraw("remove-scene",scene)
        self.assertIn(first.id,affected)

    def test_actual_upstream_consumer_rejects_corrupt_inputs_before_admission(self):
        from alice_personality.identity.consumer import DecisionConsumer
        from flora.continuity.personality import build_document
        from dataclasses import replace
        port=self.pe_port()
        document=build_document(self.store.recollect("personality","judgment"),port.situation,port.candidates,port.labels)
        producer=port.producer_factory()
        produced=producer.produce(document)
        session=producer.close_and_verify()
        class Sentinel:
            def _evidence(self):raise RuntimeError("reached actual admission boundary")
        for defect in ("session","features"):
            bad_session=deepcopy(session)
            bad_produced=produced
            if defect=="session":bad_session["receipt_sha256"]="0"*64
            else:bad_produced=replace(produced,binding=dict(produced.binding,binding_sha256="0"*64))
            with self.subTest(defect=defect),self.assertRaisesRegex(ValueError,"binding changed"):
                DecisionConsumer.respond(Sentinel(),document,bad_produced,bad_session)
        with self.assertRaisesRegex(RuntimeError,"admission boundary"):
            DecisionConsumer.respond(Sentinel(),document,produced,session)

    def test_local_bundle_references_survive_without_becoming_global_ids(self):
        from flora.continuity.formation import NativeFormationResult
        source=self.native_source()
        def local(c,o):
            output=formation_tests.answer(c,o)
            first=output["proposals"][0]
            first["proposal"]["uncertainty_ref"]="new-uncertainty"
            second=deepcopy(first)
            second["proposal"].update(proposal_id="alternative",value_ref="alternative-value",
                contradicts=["estimate"],target_refs=["estimate-value"])
            output["proposals"].append(second)
            output["dispositions"][0]["target_refs"]=["alternative-value"]
            return NativeFormationResult(output,("new-uncertainty",))
        candidate=self.kernel.form_native("local","formation",self.formation_port(local),source)
        memories=self.kernel.accept_native("local-accept","owner",candidate)
        view=self.store.recollect("personality","judgment")
        decision=next(r for r in view.records if r.kind=="formation_decision")
        self.assertEqual(decision.value["local_references"]["estimate"]["records"],[memories[0]])
        self.assertEqual(decision.value["local_references"]["new-uncertainty"]["records"],memories)
        from flora.continuity.semantic import semantic_text
        text=semantic_text(view,view.record(memories[1]))
        self.assertIn("contradicts",text)
        self.assertIn("same accepted bundle",text)
        self.assertNotIn("estimate-value",text)
        affected=self.kernel.withdraw("withdraw-local",source)
        self.assertTrue(set(memories)<=set(affected))

    def test_other_registered_person_cannot_become_the_enrolled_host(self):
        source=self.native_source()
        self.store.capture_native("other","owner","world",b"Another person supplied this.",event_at=T0,
            policy=dict(formation_tests.POLICY,subject_ref="other-person"))
        def other(c,o):
            output=formation_tests.answer(c,o)
            output["proposals"][0]["proposal"]["subject_ref"]="other-person"
            return output
        candidate=self.kernel.form_native("other-person","formation",self.formation_port(other),source)
        with self.assertRaisesRegex(ValueError,"enrolled"):
            self.kernel.accept_native("wrong-person","owner",candidate,
                state_bindings={"estimate":{"subject":"host","slot":"workload","predecessor":None}})

    def test_withdrawal_closes_forward_and_cyclic_local_bundle_meaning(self):
        source=self.native_source()
        def cyclic(c,o):
            output=formation_tests.answer(c,o)
            first=output["proposals"][0]
            first["proposal"]["target_refs"]=["later"]
            second=deepcopy(first)
            second["proposal"].update(proposal_id="later",value_ref="later-value",target_refs=["estimate"])
            output["proposals"].append(second)
            return output
        candidate=self.kernel.form_native("cycle","formation",self.formation_port(cyclic),source)
        memories=self.kernel.accept_native("cycle-accept","owner",candidate,
            state_bindings={"later":{"subject":"host","slot":"cyclic","predecessor":None}})
        before=self.store.recollect("personality","judgment")
        from flora.continuity.semantic import semantic_text
        self.assertIn("same accepted bundle",semantic_text(before,before.record(memories[1])))
        affected=self.kernel.withdraw("withdraw-one",memories[0])
        self.assertTrue(set(memories)<=set(affected))
        self.assertIsNone(self.store.recollect("personality","judgment").state("host","cyclic"))
        self.assertEqual(self.store.record(source).status,"active")
        # Historical descendants remain in the dependency index. A later
        # withdrawal of their original source must still finish atomically.
        self.kernel.withdraw("withdraw-original-after-bundle",source)
        self.assertEqual(self.store.record(source).status,"withdrawn")

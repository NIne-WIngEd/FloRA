"""One connected native-schema episode. No trained behavior is asserted."""
import json
from pathlib import Path
import unittest
import test_native_personality as pe_tests
from test_native_formation import POLICY,answer
from test_continuity_kernel import KernelFixture
from test_continuity_store import T0,open_store
from flora.continuity.formation import NativeFormationPort
from flora.continuity.store import now

class NativeEpisodeTests(KernelFixture,unittest.TestCase):
    setUp=pe_tests.NativePersonalityTests.setUp
    port=pe_tests.NativePersonalityTests.port

    def test_actual_outcome_native_formation_mixed_state_and_reopened_native_judgment(self):
        host=self.store.capture_native("host","owner","host",b"Ari initially estimates four project hours.",
            event_at=T0,policy=POLICY)
        anchor=self.store.capture_native("anchor","owner","source_person",b"The source person values careful evidence.",
            event_at=T0,policy=dict(POLICY,role="owner_attested_source_person",subject_ref="source-person",identity_core_allowed=True))
        self.store.bind_native_subject("bind-host","host","ari",support=[host])
        self.store.bind_native_subject("bind-self","self","friday-self",support=[anchor])
        project=self.store.create_mission("project","Finish project","project file exists")
        port=self.port()
        judgment=self.kernel.judge("before","personality",port)
        action=self.kernel.authorize_action("approve-action",judgment,{"task":"finish project"},
            missions=(project,self.mission),executor="executor",owner_reason="Owner selects project despite unresolved model fixture")
        self.assertIsNotNone(self.kernel.claim_action(action,"executor"))
        world=Path(self.tmp.name)/"world.json"
        world.write_text(json.dumps({"project_file":True,"research_submission":False}))
        self.kernel.acknowledge("ack","executor",action,{"reported":"done"})
        measured=json.loads(world.read_text())
        observed=self.store.capture_native("observe","reader","world",world.read_bytes(),event_at=now(),
            observes_action=action,policy=dict(POLICY,role="tool_or_action_observation",subject_ref=None))
        outcome=self.kernel.observe("outcome","reader",action,observed,{
            project:{"criterion":"project file exists","status":"met" if measured["project_file"] else "missed"},
            self.mission:{"criterion":"submission exists","status":"met" if measured["research_submission"] else "missed"}})
        def native_runtime(context,opened):
            # Explicit formation fixture reads actual independent outcome content.
            trigger=context["base_context"]["experience_refs"][0]
            outcomes=json.loads(dict(opened)[trigger])["value"]["assessments"]
            output=answer(context,opened)
            first=output["proposals"][0]
            first["sensitivity_hint"]="highly_sensitive"
            first["proposal"].update(epistemic_status="observation",
                value_text="Project outcome: "+outcomes[project]["status"]+"; research outcome: "+outcomes[self.mission]["status"])
            import copy
            second=copy.deepcopy(first)
            second["proposal"].update(proposal_id="self-update",value_ref="self-value",kind="self_observation",
                domain="self",subject_ref="friday-self",value_text="My action completed project and left research "+outcomes[self.mission]["status"])
            output["proposals"].append(second)
            return output
        candidate=self.kernel.form_native("experience","formation",
            NativeFormationPort(self.store.scope,"a"*64,native_runtime),outcome)
        self.kernel.accept_native("accept-experience","owner",candidate,state_bindings={
            "estimate":{"subject":"host","slot":"workload-outcome","predecessor":None},
            "self-update":{"subject":"self","slot":"project-consequence","predecessor":None}})
        self.store.close()
        self.store=open_store(self.tmp.name)
        self.kernel=self.kernel_type(self.store)
        after=self.kernel.judge("after","personality",port)
        native=self.store.record(after).value["packet"]["native_output"]
        texts=" ".join(s["text"] for s in native["document"]["sources"])
        self.assertIn("research outcome: missed",texts)
        self.assertIn("My action completed project",texts)
        self.assertNotIn("tensor_archive",texts)
        for record in self.store.recollect("personality","judgment").records:self.assertNotIn(record.id,texts)
        self.assertEqual(self.kernel.mission_status(project),"met")
        self.assertEqual(self.kernel.mission_status(self.mission),"missed")
        self.assertEqual(self.store.record(anchor).status,"active")
        self.assertEqual(native["response"]["qualification"],"UNQUALIFIED")
        self.assertEqual(self.consumer.calls,2)

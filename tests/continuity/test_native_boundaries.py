"""Regression proofs for review findings; these are mechanics, never learning."""
import json
from dataclasses import replace
import test_native_personality as pe_tests
from test_continuity_kernel import KernelFixture
import unittest
from test_native_formation import POLICY, answer
from test_continuity_store import T0, open_store
from flora.continuity.formation import NativeFormationPort, build_context
from flora.continuity.personality import build_document

class NativeBoundaryTests(KernelFixture,unittest.TestCase):
    setUp=pe_tests.NativePersonalityTests.setUp
    port=pe_tests.NativePersonalityTests.port
    def test_repeated_judgment_keeps_custody_out_of_semantic_inputs(self):
        port=self.port()
        first=self.kernel.judge("first","personality",port)
        self.store.close()
        self.store=open_store(self.tmp.name)
        self.kernel=self.kernel_type(self.store)
        second=self.kernel.judge("second","personality",port)
        self.assertNotEqual(first,second)
        output=self.store.record(second).value["packet"]["native_output"]
        document=output["document"]
        semantic=json.dumps(document)
        self.assertNotIn("tensor_archive",semantic)
        self.assertNotIn("feature_binding",semantic)
        self.assertIn("UNQUALIFIED",semantic)
        self.assertIn("tensor_archive",self.store.record(first).value["packet"]["native_output"])
        view=self.store.recollect("formation","formation")
        _,opened=build_context(view,self.store.scope,self.evidence)
        self.assertNotIn(b"tensor_archive",b"".join(c for _,c in opened))

    def test_native_provenance_and_event_times_reach_semantic_features(self):
        port=self.port()
        for index,role in enumerate(("authenticated_owner_statement","hypothetical_training","generated_reconstruction","outside_source")):
            identity=self.store.capture_native("role-"+str(index),"owner","host",b"Project needs four hours.",
                event_at=T0,policy=dict(POLICY,role=role))
            doc=build_document(self.store.recollect("personality","judgment"),port.situation,port.candidates,port.labels)
            source=next(s for s in doc.sources if s.record.record_id==identity)
            self.assertIn(role,source.text)
            self.assertIn('"domain":"host"',source.text)
            self.assertIn("2026-10-01",source.text)
            self.assertIn("Project needs four hours.",source.text)
            self.assertFalse(source.record.identity_core_allowed)
            for r in self.store.recollect("personality","judgment").records:
                self.assertNotIn(r.id,source.text)
                if r.kind=="evidence":
                    self.assertNotIn(r.value["sha256"],source.text)

    def test_same_operation_changed_native_request_is_refused(self):
        port=self.port()
        first=self.kernel.judge("same","personality",port)
        self.assertEqual(self.kernel.judge("same","personality",port),first)
        from copy import copy
        changed=copy(port)
        changed.situation="Choose a different task."
        changed.candidates=(("different","An unrelated option."),)
        with self.assertRaisesRegex(ValueError,"idempotency"):
            self.kernel.judge("same","personality",changed)
        self.assertEqual(self.consumer.calls,1)

    def test_derived_sources_share_conservative_native_family(self):
        source=self.store.capture_native("source","owner","host",b"Project needs four hours.",
            event_at=T0,policy=POLICY,source_root="one-original")
        formation=NativeFormationPort(self.store.scope,"a"*64,answer)
        self.store.bind_native_subject("host-subject","host","ari",support=[source])
        candidate=self.kernel.form_native("form","formation",formation,source)
        memories=self.kernel.accept_native("accept","owner",candidate,
            state_bindings={"estimate":{"subject":"host","slot":"workload","predecessor":None}})
        port=self.port()
        view=self.store.recollect("personality","judgment")
        claim=view.state("host","workload")
        doc=build_document(view,port.situation,port.candidates,port.labels)
        families={s.record.record_id:s.record.source_family_id for s in doc.sources}
        self.assertEqual(families[source],families[memories[0]])
        self.assertEqual(families[source],families[claim.id])
        context,_=build_context(view,self.store.scope,source)
        refs={r.ref_id:r.duplicate_group_ref for r in context.base.evidence}
        self.assertEqual(refs[source],refs[memories[0]])
        self.assertEqual(refs[source],refs[claim.id])

    def test_legacy_capture_receipt_still_replays(self):
        # Re-create the exact baseline receipt, not a fabricated expected hash.
        from flora.continuity.store import require_time
        request=["capture","host",b"old",require_time(T0),None,None]
        identity=self.store._write("baseline-capture","owner",{"owner"},request,
            lambda tx:tx.append("evidence","host",{"baseline_receipt_fixture":True}))
        self.assertEqual(self.store.capture("baseline-capture","owner","host",b"old",event_at=T0),identity)

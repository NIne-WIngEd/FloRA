"""Adapter tests use upstream untrained tensor mechanics, never model training."""
from dataclasses import replace
import unittest
from types import SimpleNamespace
import torch

from alice_personality.identity.codec import fingerprint
from alice_personality.identity.contracts import HEAD_FAMILIES, IdentityModelConfig, LabelSpec
from alice_personality.identity.feature_producer import FrozenFrameProducer
from alice_personality.identity.model import IdentityModel
from test_continuity_kernel import KernelFixture
from test_continuity_store import T0
from test_native_formation import POLICY


class Tokenizer:
    def __call__(self,texts,**kwargs):
        data=list(texts[0].encode())
        ids=torch.tensor([[b+1 for b in data]])
        return {"input_ids":ids,"attention_mask":torch.ones_like(ids)}


class Features:
    hidden_size=8; hidden_state_count=2; max_source_tokens=20000; device=torch.device("cpu")
    def extract_features(self,input_ids,attention_mask):
        value=input_ids.float()[...,None].expand(-1,-1,8)/256
        states=(value,value+.1)
        return SimpleNamespace(hidden_states=states[-1],all_hidden_states=states,attention_mask=attention_mask)


class PublicConsumer:
    """Only response/custody shell is doubled; native tensor model and codec are real."""
    def __init__(self,model,mode="normal"):
        self.model=model; self.calls=0; self.mode=mode
    def respond(self,document,produced,closed_session):
        self.calls+=1
        packet=self.model(produced.frame)
        if self.mode=="double":self.model(produced.frame)
        return {"schema":"public-untrained-response-fixture", "packet_sha256":
            "0"*64 if self.mode=="wrong" else fingerprint(packet),
            "document_sha256":document.sha256,"frame_sha256":produced.binding["frame_sha256"],
            "feature_binding_sha256":produced.binding["binding_sha256"],
            "closed_session_sha256":closed_session["receipt_sha256"],
            "qualification":"UNQUALIFIED","response_text":None}


class NativePersonalityTests(KernelFixture,unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1); torch.manual_seed(17)
        self.make_kernel()

    def port(self,mode="normal"):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec("flora.continuity.personality"),"native PE connection missing")
        from flora.continuity.personality import NativePersonalityPort
        config=IdentityModelConfig(8,2,learned_width=16,attention_heads=4,graph_layers=1,readout_layers=1)
        self.consumer=PublicConsumer(IdentityModel(config),mode)
        labels={f:(LabelSpec(f+"-label",f,"Explicit test descriptor for "+f,
            "normalized_intensity" if f=="voice" else "categorical",
            0 if f=="voice" else None,1 if f=="voice" else None),) for f in HEAD_FAMILIES}
        return NativePersonalityPort("b"*64,self.consumer,
            lambda:FrozenFrameProducer(Tokenizer(),Features(),config,_fixture=True),
            situation="Choose a project schedule.",candidates=(("project","Do the project first."),("research","Do research first.")),labels=labels)

    def test_complete_native_packet_from_same_call_is_persisted(self):
        port=self.port()
        identity=self.kernel.judge("native-judge","personality",port)
        packet=self.store.record(identity).value["packet"]["native_output"]
        self.assertEqual(self.consumer.calls,1)
        self.assertIn("native_latent",packet["decision"])
        self.assertEqual(set(packet["decision"]["heads"]),set(HEAD_FAMILIES))
        self.assertIn("source_tokens",packet["tensor_archive"]["fields"]["representation"]["fields"])
        self.assertEqual(packet["response"]["qualification"],"UNQUALIFIED")
        self.assertEqual(self.consumer.model._forward_hooks,{})

    def test_document_preserves_host_identity_and_original_content(self):
        port=self.port()
        from flora.continuity.personality import build_document
        source=self.store.capture_native("identity","owner","source_person",b"Source person values careful evidence.",
            event_at=T0,policy=dict(POLICY,role="owner_attested_source_person",subject_ref="source-person",identity_core_allowed=True))
        view=self.store.recollect("personality","judgment")
        doc=build_document(view,port.situation,port.candidates,port.labels)
        records={s.record.record_id:s for s in doc.sources}
        self.assertIn("Source person values careful evidence.",records[source].text)
        self.assertTrue(records[source].record.identity_core_allowed)
        self.assertFalse(records[self.evidence].record.identity_core_allowed)
        self.assertEqual(records[self.evidence].record.source_kind,"HOST")
        self.assertIsNone(next(f.text for f in doc.fields if f.semantic_role=="social_emotional"))

    def test_wrong_packet_or_extra_forward_never_commits_judgment(self):
        for mode in ("wrong","double"):
            port=self.port(mode)
            with self.assertRaisesRegex(ValueError,"packet|forward"):
                self.kernel.judge(mode,"personality",port)
            self.assertEqual(self.consumer.model._forward_hooks,{})
        self.assertFalse(any(r.kind=="judgment" for r in self.store.recollect("owner","judgment").records))

    def test_revocation_during_real_native_forward_prevents_publication(self):
        port=self.port()
        handle=self.consumer.model.register_forward_hook(lambda *_:self.store.revoke("stop","personality"))
        try:
            with self.assertRaises(PermissionError):self.kernel.judge("judge","personality",port)
        finally:handle.remove()
        self.assertFalse(any(r.kind=="judgment" for r in self.store.recollect("owner","judgment").records))


if __name__=="__main__":unittest.main()

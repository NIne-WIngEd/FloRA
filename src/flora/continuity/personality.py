"""Real PE schema/consumer integration; models and feature loaders remain external."""
import base64
from dataclasses import fields,is_dataclass
from hashlib import sha256
from collections.abc import Mapping
import json
import threading
import weakref

import torch
from alice_personality.identity.codec import (
    REQUIRED_ROLES, CandidateEntry, ConceptEntry, CognitiveFrameDocument, GraphEdge,
    SemanticEntry, SituationField, SourceEntry, canonical, decision_to_mapping, fingerprint)
from alice_personality.identity.contracts import ConceptRecord, SourceRecord
from .semantic import semantic_text, caption, model_records, source_families

_locks=weakref.WeakKeyDictionary()
_locks_guard=threading.Lock()

RELATION_MEANINGS={
    "supports":"The source is declared support for the stated record; this does not establish truth.",
    "contradicts":"The records are declared in conflict; neither is erased or automatically preferred.",
    "target_refs":"The proposal refers to the target; a request is not an executed command.",
    "mission_target_refs":"The memory explicitly concerns this mission.",
    "workspace_target_refs":"The memory explicitly concerns this workspace.",
    "relationship_counterpart":"The relationship identifies this registered counterpart.",
    "participant_refs":"The registered entity participates in the proposed episode.",
    "scene_refs":"The proposed episode identifies this registered scene.",
    "observed_after":"The observation is bound to this dispatched action; chronology alone is not causality.",
    "evaluates":"The independent outcome assesses this mission against its exact criterion.",
    "pursues":"The owner-authorized action pursues this mission; intent is not completion.",
    "depends_on":"This mission depends on the other mission.",
    "conflicts_with":"The two missions have an explicitly registered conflict.",
    "supersedes":"The accepted successor revises this older state while retaining its history."}


def build_document(view, situation, candidates, labels, representation="structured"):
    """Deterministic content assembly, not a semantic teacher or answer generator."""
    if representation not in {"structured","flat"}:raise ValueError("unknown representation")
    sources=[]; concepts=[]; edges=[]; relations=[]
    current=set(view.heads.values())
    families=source_families(view)
    for r in model_records(view):
        text=semantic_text(view,r)
        policy=r.value.get("native_policy") if r.kind=="evidence" else None
        identity=bool(policy and policy["identity_core_allowed"])
        kind="E0" if identity else {"host":"HOST","relationship":"RELATIONSHIP","self":"ASELF"}.get(r.subject,"UNKNOWN")
        provenance="A-SELF" if kind=="ASELF" else kind
        root=families[r.id]
        sources.append(SourceEntry(text,SourceRecord(r.id,root,kind,provenance,
            identity,True,identity,False,False,False)))
        if identity or r.id in current or r.kind=="memory":
            concept="concept-"+r.id
            target="identity" if identity else {"HOST":"host","RELATIONSHIP":"relationship","ASELF":"self"}.get(kind,"context")
            concepts.append(ConceptEntry(text,ConceptRecord(concept,target)))
            edges.append(GraphEdge(r.id,concept,"registered-content",
                                   "identity_support" if identity else "context_only"))
            relations.append({"concept_view":target,
                "role":"identity_support" if identity else "context_only",
                "meaning":"The concept contains exactly this source content without additional inference.",
                "content":text})
    source_by_id={s.record.record_id:s.record for s in sources}
    relation_entries=[SemanticEntry("registered-content","This concept contains the same registered content as its source; it adds no inference.")]
    used=set()
    for r in model_records(view):
        for role,target_id in r.links:
            if role not in RELATION_MEANINGS or target_id not in source_by_id:continue
            concept="relation-"+r.id+"-"+role+"-"+target_id
            if concept in used:continue
            used.add(concept)
            target_view={"HOST":"host","RELATIONSHIP":"relationship","ASELF":"self"}.get(
                source_by_id[target_id].source_kind,"context")
            meaning={"meaning":RELATION_MEANINGS[role],"source":caption(view,target_id),
                "about":caption(view,r.id),"concept_view":target_view,"role":"context_only"}
            concepts.append(ConceptEntry(canonical(meaning).decode("utf-8"),ConceptRecord(concept,target_view)))
            relation_id="continuity-"+role
            edges.append(GraphEdge(target_id,concept,relation_id,"context_only"))
            relations.append(meaning)
            if not any(e.entry_id==relation_id for e in relation_entries):
                relation_entries.append(SemanticEntry(relation_id,RELATION_MEANINGS[role]))
    supplied={"situation":situation}
    if relations:supplied["selected_spans"]=canonical(relations[0]).decode("utf-8")
    goals=[semantic_text(view,r) for r in view.records if r.kind=="mission"]
    if goals:supplied["goals_constraints"]="\n".join(goals)
    doc=CognitiveFrameDocument(tuple(SituationField(role,role,role.replace("_"," "),
        supplied.get(role),role in supplied) for role in sorted(REQUIRED_ROLES))+
        tuple(SituationField("relation-description-"+str(i),"selected_spans","registered relation",
            canonical(row).decode("utf-8"),True) for i,row in enumerate(relations[1:],1)),
        tuple(sources),tuple(concepts),tuple(CandidateEntry(i,t,True,True) for i,t in candidates),
        tuple(relation_entries),
        labels,tuple(edges) if representation=="structured" else ())
    doc.validate()
    return doc


def tensor_archive(value):
    """Lossless typed custody alongside PE's human-usable downstream codec.

    No pickle or executable decoder. All dataclass fields, including native
    representation fields omitted from the downstream view, remain recoverable.
    """
    if isinstance(value,torch.Tensor):
        data=value.detach().cpu().contiguous()
        flat=data.reshape(-1)
        if flat.stride(-1)!=1:flat=flat.clone(memory_format=torch.contiguous_format)
        return {"kind":"tensor","dtype":str(data.dtype),"shape":list(data.shape),
            "bytes":base64.b64encode(flat.view(torch.uint8).numpy().tobytes()).decode("ascii")}
    if is_dataclass(value):
        return {"kind":"dataclass","type":type(value).__module__+"."+type(value).__qualname__,
                "fields":{f.name:tensor_archive(getattr(value,f.name)) for f in fields(value)}}
    if isinstance(value,Mapping):
        if any(not isinstance(k,str) for k in value):raise ValueError("native mapping keys must be text")
        return {"kind":"mapping","items":{k:tensor_archive(v) for k,v in value.items()}}
    if isinstance(value,(tuple,list)):
        return {"kind":"tuple" if isinstance(value,tuple) else "list","items":[tensor_archive(v) for v in value]}
    if value is None or type(value) in (bool,int,float,str):return value
    raise ValueError("unsupported native packet value")


class NativePersonalityPort:
    def __init__(self, artifact_sha256, consumer, producer_factory, *, situation,candidates,labels,representation="structured"):
        from cognitive_kernel.canonical import require_sha256
        self.model_ref="pe:"+require_sha256(artifact_sha256,"artifact_sha256")
        self.consumer,self.producer_factory=consumer,producer_factory
        self.situation,self.candidates,self.labels=situation,tuple(candidates),labels
        self.representation=representation
        with _locks_guard:
            self._lock=_locks.setdefault(consumer.model,threading.Lock())

    @property
    def request_sha256(self):
        from dataclasses import asdict
        return sha256(canonical({"situation":self.situation,"candidates":self.candidates,
            "labels":{k:[asdict(v) for v in values] for k,values in self.labels.items()},
            "representation":self.representation,"adapter_schema":"continuity-native-pe-v1"})).hexdigest()

    def snapshot_request(self):
        from copy import copy,deepcopy
        port=copy(self)
        port.situation,port.candidates,port.labels=deepcopy((self.situation,self.candidates,self.labels))
        return port

    def judge(self,view):
        with self._lock:
            document=build_document(view,self.situation,self.candidates,self.labels,self.representation)
            producer=self.producer_factory()
            produced=producer.produce(document)
            session=producer.close_and_verify()
            captured=[]
            def retain(module,args,packet):
                packet.validate()
                captured.append({"digest":fingerprint(packet),"decision":decision_to_mapping(packet),
                                 "archive":tensor_archive(packet)})
                # Returning None leaves the actual forward output untouched.
            handle=self.consumer.model.register_forward_hook(retain)
            try:
                response=self.consumer.respond(document,produced,session)
            finally:
                handle.remove()
            if len(captured)!=1:
                raise ValueError("native consumer must perform exactly one captured forward")
            packet=captured[0]
            expected={"packet_sha256":packet["digest"],"document_sha256":document.sha256,
                "frame_sha256":produced.binding["frame_sha256"],
                "feature_binding_sha256":produced.binding["binding_sha256"],
                "closed_session_sha256":session["receipt_sha256"]}
            if any(response.get(k)!=v for k,v in expected.items()):
                raise ValueError("native response packet/input binding differs from actual call")
            output={"document":document.to_mapping(),"feature_binding":produced.binding,
                "closed_session":session,"response":response,"decision":packet["decision"],
                "tensor_archive":packet["archive"]}
            # Freeze before returning to the authority; no tensors or aliases escape.
            return json.loads(canonical({"model_ref":self.model_ref,
                "native_schema":"alice-personality-decision-document-v2",
                "support":[r.id for r in model_records(view)],"support_kind":"offered",
                "request_sha256":self.request_sha256,
                "native_output":output}))

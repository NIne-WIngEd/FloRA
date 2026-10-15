"""MFM 1.6 integration. Uses native validators; never supplies semantic answers."""
from hashlib import sha256
import json
import uuid

from cognitive_kernel.canonical import normalize_timestamp
from cognitive_kernel.formation_contracts import (
    EVIDENCE_ROLES, EVIDENCE_MODALITIES, FormationContextPacket, FormationEvidenceRef)
from cognitive_kernel.formation_semantics_v16 import (
    FormationContextV16, RegisteredSourceSensitivity, RegisteredFormationTarget,
    SENSITIVITY_ORDER, bundle_v16_from_output, validate_formation_grounding_v16)

from .store import json_bytes
from .semantic import record_bytes, model_records, source_families
from dataclasses import dataclass


@dataclass(frozen=True)
class NativeFormationResult:
    output: dict
    local_uncertainty_refs: tuple[str, ...] = ()


def validate_source_policy(policy, subject):
    names={"role","modality","subject_ref","minimum_sensitivity","identity_core_allowed"}
    if (not isinstance(policy,dict) or set(policy)!=names or policy["role"] not in EVIDENCE_ROLES
            or policy["modality"] not in EVIDENCE_MODALITIES
            or policy["minimum_sensitivity"] not in SENSITIVITY_ORDER
            or type(policy["identity_core_allowed"]) is not bool):
        raise ValueError("explicit native source policy required")
    if policy["identity_core_allowed"] and (subject!="source_person"
            or policy["role"]!="owner_attested_source_person"):
        raise ValueError("identity authority requires independently attested source-person evidence")
    return json.loads(json_bytes(policy))


def build_context(view, scope, trigger):
    if view.scope!=scope.storage_scope():
        raise ValueError("native context scope differs from authority")
    source=view.record(trigger)
    if source.kind not in {"evidence","outcome"}:
        raise ValueError("native formation needs evidence or independent outcome")
    records=model_records(view)
    ids={r.id for r in records}
    families=source_families(view)
    refs=[]; sensitivities=[]; opened=[]; targets=[]
    for record in records:
        content=record_bytes(view,record)
        policy=record.value.get("native_policy") if record.kind=="evidence" else None
        if policy:
            validate_source_policy(policy,record.subject)
        else:
            if record.kind=="evidence":
                content.decode("utf-8")  # Unknown binary content needs explicit native modality.
            policy=dict(role={"mission":"mission_state", "claim":"authoritative_claim",
                "memory":"authoritative_claim", "outcome":"tool_or_action_observation"}.get(
                    record.kind,"historical_experience"), modality="text" if record.kind=="evidence" else "structured",
                subject_ref=None,minimum_sensitivity="highly_sensitive",identity_core_allowed=False)
        refs.append(FormationEvidenceRef(record.id,scope,"continuity",sha256(content).hexdigest(),
            policy["role"],policy["modality"], subject_ref=policy["subject_ref"],
            source_item_ref=record.id,observed_at=normalize_timestamp(record.event_at),
            recorded_at=normalize_timestamp(record.recorded_at),
            duplicate_group_ref=families[record.id],
            parent_refs=tuple(sorted(p for p in record.parents if p in ids))))
        sensitivities.append(RegisteredSourceSensitivity(record.id,policy["minimum_sensitivity"]))
        opened.append((record.id,content))
        if record.kind in {"mission","target"}:
            support=tuple(sorted(p for p in record.parents if p in ids)) or (record.id,)
            targets.append(RegisteredFormationTarget(record.id,
                "mission" if record.kind=="mission" else record.value["target_kind"],
                scope,"continuity",support))
    context=FormationContextV16(FormationContextPacket(scope,"continuity",(trigger,),tuple(refs)),
        tuple(sensitivities),tuple(targets))
    context.validate()
    return context,tuple(opened)


class NativeFormationPort:
    """Runtime(context_record, opened_sources) returns the actual 1.6 output.

    The trusted host supplies the admitted runtime/artifact. A digest binds the
    invocation; this class does not claim to load, train or qualify its weights.
    """
    def __init__(self, scope, artifact_sha256, runtime):
        from cognitive_kernel.canonical import require_sha256
        self.scope=scope
        self.artifact_sha256=require_sha256(artifact_sha256,"artifact_sha256")
        self.model_ref="mfm-1.6:"+self.artifact_sha256
        self.runtime=runtime

    def propose(self, view, trigger):
        context,opened=build_context(view,self.scope,trigger)
        output=self.runtime(context.record(),opened)
        result=output if isinstance(output,NativeFormationResult) else NativeFormationResult(output)
        output=result.output
        run="run-"+uuid.uuid4().hex
        bundle=bundle_v16_from_output(context,output,artifact_sha256=self.artifact_sha256,inference_run_id=run)
        validate_formation_grounding_v16(context,bundle,opened)
        packet={"model_ref":self.model_ref,"native_schema":"mfm-formation-output-v1.6",
            "native_output":bundle.output_record(),"context":context.record(),
            "artifact_sha256":self.artifact_sha256,"inference_run_id":run,"trigger":trigger,
            "local_uncertainty_refs":list(result.local_uncertainty_refs)}
        packet["local_references"]=resolve_references(view,packet)
        return packet


def validate_packet(view, scope, packet):
    context,opened=build_context(view,scope,packet["trigger"])
    if context.record()!=packet["context"] or packet["model_ref"]!="mfm-1.6:"+packet["artifact_sha256"]:
        raise ValueError("native input/artifact binding differs from consumed authority")
    bundle=bundle_v16_from_output(context,packet["native_output"],
        artifact_sha256=packet["artifact_sha256"],inference_run_id=packet["inference_run_id"])
    validate_formation_grounding_v16(context,bundle,opened)
    if packet["native_schema"]!="mfm-formation-output-v1.6":raise ValueError("native schema mismatch")
    if packet.get("local_references")!=resolve_references(view,packet):
        raise ValueError("native local namespace binding differs")
    return bundle

def resolve_references(view, packet):
    """Resolve final JSON against the actual caller namespaces, not syntax alone."""
    records={r.id:r for r in model_records(view)}
    rows=packet["native_output"]["proposals"]
    subjects={r.value["native_policy"]["subject_ref"] for r in records.values()
        if r.kind=="evidence" and r.value.get("native_policy")}
    subjects.update(r.value.get("subject_ref") for r in records.values() if r.kind=="target")
    subjects.update(r.id for r in records.values()
        if r.kind=="target" and r.value["target_kind"]=="entity")
    subjects.discard(None)
    local={}
    for row in rows:
        p=row["proposal"]
        if p["subject_ref"] not in subjects:raise ValueError("native subject is not registered")
        for key,kind in (("proposal_id","proposal"),("value_ref","value")):
            identity=p[key]
            if identity in local or identity in records:raise ValueError("ambiguous native local namespace")
            local[identity]={"kind":kind,"proposal_id":p["proposal_id"]}
    declared=packet.get("local_uncertainty_refs",[])
    if not isinstance(declared,list) or len(set(declared))!=len(declared):
        raise ValueError("explicit distinct local uncertainty declarations required")
    from cognitive_kernel.canonical import require_identifier
    for identity in declared:
        if require_identifier(identity,"local uncertainty")!=identity or identity in local or identity in records:
            raise ValueError("ambiguous native uncertainty namespace")
        if not any(r["proposal"]["uncertainty_ref"]==identity for r in rows):
            raise ValueError("unused local uncertainty declaration")
        local[identity]={"kind":"uncertainty"}
    for row in rows:
        p=row["proposal"]
        for identity in (*p["contradicts"],*p["target_refs"]):
            if identity not in records and identity not in local:raise ValueError("unregistered governance target")
        identity=p["uncertainty_ref"]
        if identity is not None:
            registered=records.get(identity)
            if not ((identity in local and local[identity]["kind"]=="uncertainty") or
                    (registered and registered.kind=="memory" and
                     registered.value["native_proposal"]["proposal"]["kind"]=="uncertainty")):
                raise ValueError("unregistered uncertainty reference")
    for d in packet["native_output"]["dispositions"]:
        if any(i not in records and i not in local for i in d["target_refs"]):
            raise ValueError("unregistered disposition target")
    return local

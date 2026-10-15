"""Explicit model meaning, separate from exact owner-audit custody."""
from dataclasses import asdict
from hashlib import sha256
from .store import json_bytes

SEMANTIC_KINDS=frozenset({"evidence","mission","claim","memory","judgment","action","outcome","ack","target","formation_decision"})

def model_records(view):
    return tuple(r for r in view.records if r.kind in SEMANTIC_KINDS)

def root_ancestry(records):
    """All influence parents, including non-public proposals; snapshot-only."""
    roots={}
    for record in sorted(records,key=lambda r:r.sequence):
        if record.kind=="evidence":
            value=(str(record.value["source_root"]),)
        else:
            value=tuple(sorted({root for p in record.parents for root in roots[p]}))
            if not value:value=("local-record:"+record.id,)
        roots[record.id]=value
    return roots

def source_families(view):
    """Single-family native APIs conservatively merge overlapping root sets.

    This may under-count independent origins. It never creates corroboration
    from copies/derivatives and is not an empirical independence estimator.
    """
    records=model_records(view)
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    for r in records:
        roots=view.source_roots[r.id]
        first=find(roots[0])
        for root in roots[1:]:parent[find(root)]=first
    groups={}
    for root in parent:groups.setdefault(find(root),[]).append(root)
    ids={leader:"roots-"+sha256(json_bytes(sorted(roots))).hexdigest() for leader,roots in groups.items()}
    return {r.id:ids[find(view.source_roots[r.id][0])] for r in records}

def semantic_value(record):
    value=record.value
    if record.kind=="claim":
        return {k:v for k,v in value.items() if k!="packet"}
    if record.kind=="judgment":
        packet=value["packet"]
        native=packet["native_output"]
        if packet["native_schema"]=="alice-personality-decision-document-v2":
            decision={k:v for k,v in native["decision"].items() if k!="native_latent"}
            response={k:native["response"][k] for k in (
                "status","qualification","training_state","selected_candidate_ids",
                "acceptable_candidate_ids","intents","response_text","acceptance_authority")
                if k in native["response"]}
            return {"model_ref":packet["model_ref"],"native_schema":packet["native_schema"],
                    "decision":decision,"response":response}
        return {"model_ref":packet["model_ref"],"native_schema":packet["native_schema"],"decision":native}
    if record.kind=="action":
        return {k:v for k,v in value.items() if k not in {"time_basis","publication_generation"}}
    return value

def semantic_record(view,record):
    if record.kind not in SEMANTIC_KINDS:raise ValueError("audit-only record is not semantic input")
    row=asdict(record)
    row["value"]=semantic_value(record)
    if record.kind=="evidence":
        # Authenticated bytes remain exact in MFM opened_sources. PE receives
        # the text plus explicit provenance; no renderer silently invents it.
        row["value"]=dict(record.value,content=view.evidence[record.id].decode("utf-8"))
    row["source_roots"]=view.source_roots[record.id]
    row["current_state"]=record.id in view.heads.values() if record.kind=="claim" else None
    return {"schema":"continuity-semantic-record-v1",**row}

def record_bytes(view,record):
    if record.kind=="evidence":return view.evidence[record.id]
    return json_bytes(semantic_record(view,record))


def caption(view,identity):
    """One-hop exact content for relation operands; never recursive custody."""
    try:r=view.record(identity)
    except StopIteration:return {"availability":"historical operand outside current semantic view"}
    if r.kind=="evidence":return {"domain":r.subject,"content":view.evidence[r.id].decode("utf-8")}
    if r.kind=="claim":
        value=r.value["content"]
        return {"domain":r.subject,"slot":r.value["slot"],"content":
            value["proposal"]["value_text"] if isinstance(value,dict) and "proposal" in value else value}
    if r.kind=="memory":return {"domain":r.subject,"content":r.value["native_proposal"]["proposal"]["value_text"]}
    if r.kind=="mission":return r.value
    if r.kind=="target":
        return {"domain":r.subject,"kind":r.value["target_kind"],
                "description":[caption(view,p) for role,p in r.links if role=="supports"
                               and view.record(p).kind in {"evidence","claim","memory"}]}
    if r.kind=="judgment":return {"kind":"prior judgment","domain":r.subject,"event_at":r.event_at}
    if r.kind=="action":return {"kind":"authorized action","request":r.value["request"]}
    return {"kind":r.kind,"domain":r.subject,"event_at":r.event_at}

def _proposal_meaning(row):
    p=row["proposal"]
    value={k:p[k] for k in ("kind","domain","value_text","epistemic_status","valid_from",
        "valid_to","confidence","temporal_granularity")}
    value["sensitivity_hint"]=row["sensitivity_hint"]
    if row["episode"]:value["episode"]={k:row["episode"][k] for k in ("event_start","event_end")}
    value["uncertainty_declared"]=p["uncertainty_ref"] is not None
    return value

def semantic_text(view,record):
    """PE feature text: meaning only; pointer/digest custody stays in metadata."""
    v=record.value
    if record.kind=="evidence":
        policy=v.get("native_policy") or {}
        meaning={"content":view.evidence[record.id].decode("utf-8"),
            "source_role":policy.get("role","historical_experience"),
            "modality":policy.get("modality","text"),
            "minimum_sensitivity":policy.get("minimum_sensitivity","highly_sensitive"),
            "identity_core_allowed":policy.get("identity_core_allowed",False)}
    elif record.kind=="memory":meaning=_proposal_meaning(v["native_proposal"])
    elif record.kind=="claim":
        content=v["content"]
        meaning={"slot":v["slot"],"content":_proposal_meaning(content)
            if isinstance(content,dict) and "proposal" in content else content,
            "epistemic":v["epistemic"],"valid_from":v["valid_from"],"valid_to":v.get("valid_to"),
            "current_state":record.id in view.heads.values()}
    elif record.kind=="judgment" and v["packet"]["native_schema"]=="alice-personality-decision-document-v2":
        native=v["packet"]["native_output"]
        decision=native["decision"]
        # Pointer distributions and latent features remain exact audit data;
        # downstream semantic judgment quantities and label descriptions remain visible.
        keys=("training_state","qualification","candidate_mask","preference_logits","preference_margins",
            "preferences","co_valid_probabilities","value_tradeoff_margins","voice_control_values",
            "voice_control_confidence","evidence_sufficiency","uncertainty","contraindications",
            "failure_tail_risk","owner_fidelity_uncertainty","identity_grounding_available")
        meaning={k:decision[k] for k in keys}
        meaning["candidates"]=[c["text"] for c in native["document"]["candidates"]]
        meaning["heads"]={family:{**{k:head[k] for k in ("scores","activations","mask")},
            "specs":[[{k:s[k] for k in ("name","description","unit","minimum","maximum")}
                if s else None for s in row] for row in head["specs"]]}
            for family,head in decision["heads"].items()}
        response=native["response"]
        meaning["response"]={k:response[k] for k in ("status","response_text","qualification","acceptance_authority")
                             if k in response}
    elif record.kind=="outcome":
        meaning={"assessments":[{"mission":caption(view,m),**assessment}
                                for m,assessment in v["assessments"].items()]}
    elif record.kind=="action":
        meaning={"request":v["request"],"owner_reason":v["owner_reason"],
                 "missions":[caption(view,m) for m in v["missions"]]}
    elif record.kind=="ack":
        meaning={"actor_report":v["receipt"],"verification":"actor report is not independent outcome evidence"}
    elif record.kind=="formation_decision":
        meaning={"dispositions":[{"scope":d["scope_ref"],"action":d["action"],
            "targets":[caption(view,i) for i in d["target_refs"] if i not in v.get("local_references",{})]}
            for d in v["dispositions"]]}
    elif record.kind=="target":meaning=caption(view,record.id)
    else:meaning=semantic_value(record)
    # Registered relation words and actual endpoint content are available in
    # both structured/flat arms. Authority-only pointers are not model prose.
    relations=[{"relation":role,"target":caption(view,target)} for role,target in record.links
        if role not in {"derived_from","authorized_by","subject_binding"}]
    if record.kind=="memory":
        p=v["native_proposal"]["proposal"]
        registry=next((r.value.get("local_references",{}) for r in view.records
            if r.kind=="formation_decision" and record.id in r.value["memories"]),{})
        for key in ("contradicts","target_refs"):
            for target in p[key]:
                if target in registry:
                    relations.append({"relation":key,"namespace":"same accepted bundle",
                        "targets":[caption(view,i) for i in registry[target]["records"]]})
    return json_bytes({"kind":record.kind,"domain":record.subject,"event_at":record.event_at,
        "recorded_at":record.recorded_at,"status":record.status,"meaning":meaning,"relations":relations}).decode("utf-8")

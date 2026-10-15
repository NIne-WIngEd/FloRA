"""Equal-evidence construction and descriptive paired counts; no learned oracle."""
from hashlib import sha256
import json
import math
from .store import json_bytes
from .semantic import model_records, semantic_record, source_families

def digest(value):
    return sha256(json_bytes(value)).hexdigest()

def matched_documents(view,port):
    from .personality import build_document
    common=(view,port.situation,port.candidates,port.labels)
    structured=build_document(*common,representation="structured")
    flat=build_document(*common,representation="flat")
    a,b=(json.loads(json_bytes(d.to_mapping())) for d in (structured,flat))
    a["edges"]=[]
    if a!=b:raise ValueError("structured/flat semantic content differs")
    return {"structured":structured,"flat":flat,"common_semantics_sha256":digest(b),
            "source_roots":{r.id:list(view.source_roots[r.id]) for r in model_records(view)},
            "source_families":source_families(view),"model_ref":port.model_ref}

def comparison_case(case_id,view,*,situation,candidates,oracle_sha256,call_budget,models):
    """Prepare once, then hand the same case to separately built systems.

    Oracle digest identifies an independently frozen rubric. Its correctness and
    the challenger's actual evidence consumption still require external review.
    """
    from cognitive_kernel.canonical import require_sha256
    if not isinstance(case_id,str) or not case_id or not isinstance(situation,str) or not situation:
        raise ValueError("explicit case and situation required")
    if type(call_budget) is not int or call_budget<1:raise ValueError("positive call budget required")
    if set(models)!={"flora","challenger"} or any(not isinstance(v,str) or not v for v in models.values()):
        raise ValueError("freeze both independent model identities before comparison")
    if (not candidates or len({i for i,_ in candidates})!=len(candidates)
            or any(not isinstance(i,str) or not i or not isinstance(t,str) or not t for i,t in candidates)):
        raise ValueError("distinct explicitly described candidates required")
    case={"schema":"flora-equal-evidence-case-v1","case_id":case_id,
        "scope":view.scope,"valid_at":view.valid_at,"valid_until":view.valid_until,
        "generation":view.generation,"authority_epoch":view.authority_epoch,
        "situation":situation,"candidates":list(candidates),"current_heads":view.heads,
        "evidence":[semantic_record(view,r) for r in model_records(view)],
        "source_families":source_families(view),"coverage":view.coverage,
        "oracle_sha256":require_sha256(oracle_sha256,"oracle_sha256"),"call_budget":call_budget}
    case=json.loads(json_bytes(case))
    inputs=digest({k:case[k] for k in ("situation","candidates","evidence","current_heads","source_families")})
    case.update(comparison_kind="personalization",arms={arm:{"model_ref":model,"input_sha256":inputs,
        "representation":"same-registered-evidence"} for arm,model in models.items()})
    return dict(case,case_sha256=digest(case))

def backbone_case(case_id,view,port,*,oracle_sha256,call_budget):
    pair=matched_documents(view,port)
    case=comparison_case(case_id,view,situation=port.situation,candidates=port.candidates,
        oracle_sha256=oracle_sha256,call_budget=call_budget,
        models={"flora":port.model_ref,"challenger":port.model_ref})
    case.pop("case_sha256")
    case.update(comparison_kind="backbone",common_semantics_sha256=pair["common_semantics_sha256"],
        arms={arm:{"model_ref":port.model_ref,"input_sha256":pair[arm].sha256,
                  "representation":arm} for arm in ("structured","flat")})
    case["arm_inputs"]={arm:json.loads(json_bytes(pair[arm].to_mapping())) for arm in ("structured","flat")}
    return dict(case,case_sha256=digest(case))

def compare_results(cases,results):
    """Count paired independent scores, including unresolved pairs in denominator.

    Observations are trusted evaluator receipts, not model self-reported truth.
    No significance, causal benefit or hypothesis qualification is inferred.
    """
    expected={}
    for case in cases:
        sha=case.get("case_sha256")
        if sha!=digest({k:v for k,v in case.items() if k!="case_sha256"}):
            raise ValueError("case changed after freezing")
        if sha in expected or any(c["case_id"]==case["case_id"] for c in expected.values()):
            raise ValueError("duplicate case")
        expected[sha]=case
    if not expected:raise ValueError("no cases")
    kinds={c["comparison_kind"] for c in cases}
    if len(kinds)!=1:raise ValueError("do not pool different experiment claims")
    arms=("structured","flat") if kinds=={"backbone"} else ("flora","challenger")
    paired={sha:{} for sha in expected}
    for row in results:
        case=expected.get(row.get("case_sha256"))
        arm=row.get("arm")
        if case is None or arm not in arms:raise ValueError("unknown comparison case/arm")
        if arm in paired[case["case_sha256"]]:raise ValueError("duplicate result")
        score=row.get("score")
        if (row.get("oracle_sha256")!=case["oracle_sha256"] or
                type(row.get("calls")) is not int or not 1<=row["calls"]<=case["call_budget"] or
                any(row.get(key)!=case["arms"][arm][key] for key in ("model_ref","input_sha256","representation")) or
                (score is not None and (type(score) not in (float,int) or not math.isfinite(score) or not 0<=score<=1))):
            raise ValueError("mismatched oracle, budget, model, or invalid independent score")
        paired[case["case_sha256"]][arm]=row
    summary=dict(paired_cases=len(expected),resolved_pairs=0,unresolved_cases=0,
                 wins={arm:0 for arm in arms},ties=0,hypothesis_qualified=False)
    for pair in paired.values():
        if set(pair)!=set(arms):raise ValueError("missing matched arm")
        a,b=pair[arms[0]]["score"],pair[arms[1]]["score"]
        if a is None or b is None:summary["unresolved_cases"]+=1
        else:
            summary["resolved_pairs"]+=1
            if a==b:summary["ties"]+=1
            else:summary["wins"][arms[0] if a>b else arms[1]]+=1
    return summary

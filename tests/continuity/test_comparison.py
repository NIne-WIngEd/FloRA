"""Matched input and paired-result mechanics, not a behavioral success oracle."""
import copy
import unittest
import test_native_personality as pe_tests
from test_continuity_kernel import KernelFixture

class ComparisonTests(KernelFixture,unittest.TestCase):
    setUp=pe_tests.NativePersonalityTests.setUp
    port=pe_tests.NativePersonalityTests.port

    def test_structured_and_flat_have_identical_semantic_content(self):
        from flora.continuity.comparison import matched_documents
        self.store.initialize_state("hours","host","hours",4,support=[self.evidence],valid_from="2026-10-01T10:00:00+00:00")
        port=self.port()
        view=self.store.recollect("personality","judgment")
        pair=matched_documents(view,port)
        import json
        from flora.continuity.store import json_bytes
        structured=json.loads(json_bytes(pair["structured"].to_mapping()))
        flat=json.loads(json_bytes(pair["flat"].to_mapping()))
        self.assertTrue(structured["edges"])
        self.assertEqual(flat["edges"],[])
        structured["edges"]=[]
        self.assertEqual(structured,flat)
        self.assertIn("without additional inference",str(flat))
        self.assertTrue(any(e["relation_id"]=="continuity-supports" for e in pair["structured"].to_mapping()["edges"]))
        self.assertIn("does not establish truth",str(flat))
        self.assertEqual(set(pair["source_roots"]),{s.record.record_id for s in pair["flat"].sources})

    def test_model_independent_case_binds_equal_evidence_and_separate_challenger(self):
        from flora.continuity.comparison import comparison_case, compare_results
        case=comparison_case("heldout-1",self.store.recollect("personality","judgment"),
            situation="Choose schedule",candidates=(("a","Project"),("b","Research")),
            oracle_sha256="d"*64,call_budget=1,models={"flora":"pe-external","challenger":"personalized-gemma-external"})
        common={"case_sha256":case["case_sha256"],"oracle_sha256":"d"*64,"calls":1}
        rows=[dict(common,arm="flora",**case["arms"]["flora"],score=1.0),
              dict(common,arm="challenger",**case["arms"]["challenger"],score=0.0)]
        result=compare_results([case],rows)
        self.assertEqual(result["wins"]["flora"],1)
        self.assertEqual(result["paired_cases"],1)
        self.assertFalse(result["hypothesis_qualified"])
        rows[1]["score"]=None
        result=compare_results([case],rows)
        self.assertEqual(result["unresolved_cases"],1)
        self.assertEqual(result["resolved_pairs"],0)

    def test_missing_or_mismatched_comparison_never_passes_silently(self):
        from flora.continuity.comparison import comparison_case, compare_results
        case=comparison_case("one",self.store.recollect("personality","judgment"),
            situation="Choose",candidates=(("a","First"),("b","Second")),oracle_sha256="d"*64,call_budget=1,
            models={"flora":"p","challenger":"g"})
        common=dict(case_sha256=case["case_sha256"],oracle_sha256="d"*64,calls=1,score=1.0)
        rows=[dict(common,arm=arm,**case["arms"][arm]) for arm in ("flora","challenger")]
        for defect in ("missing","duplicate","oracle","case","budget","score","model","input","representation"):
            bad=copy.deepcopy(rows)
            if defect=="missing":bad.pop()
            elif defect=="duplicate":bad.append(bad[0])
            elif defect=="oracle":bad[1]["oracle_sha256"]="e"*64
            elif defect=="case":bad[1]["case_sha256"]="f"*64
            elif defect=="budget":bad[1]["calls"]=2
            elif defect=="score":bad[1]["score"]=float("nan")
            else:bad[1][{"model":"model_ref","input":"input_sha256","representation":"representation"}[defect]]="changed"
            with self.subTest(defect=defect),self.assertRaises(ValueError):
                compare_results([case],bad)

    def test_backbone_results_bind_same_model_and_actual_arm_inputs(self):
        from flora.continuity.comparison import backbone_case,compare_results
        self.store.initialize_state("hours","host","hours",4,support=[self.evidence],valid_from="2026-10-01T10:00:00+00:00")
        case=backbone_case("b-case",self.store.recollect("personality","judgment"),self.port(),
            oracle_sha256="e"*64,call_budget=1)
        self.assertNotEqual(case["arms"]["structured"]["input_sha256"],case["arms"]["flat"]["input_sha256"])
        rows=[dict(case_sha256=case["case_sha256"],oracle_sha256="e"*64,arm=arm,
            **case["arms"][arm],calls=1,score=1.0) for arm in ("structured","flat")]
        self.assertEqual(compare_results([case],rows)["ties"],1)
        rows[1]["model_ref"]="another-model"
        with self.assertRaises(ValueError):compare_results([case],rows)

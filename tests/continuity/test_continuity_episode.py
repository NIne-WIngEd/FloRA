"""Comic-derived mechanical episode. Synthetic arithmetic is NOT learned judgment.

The world changes a real file; an independent reader measures it. Paired worlds
share all pre-action evidence. No fixture supplies precomputed phase judgments.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_continuity_store import open_store, T0
from flora.continuity.kernel import ContinuityKernel
from flora.continuity.store import now


class EpisodeFormation:
    model_ref = "synthetic/episode-formation-v1"

    def __init__(self, noop=False):
        self.noop = noop

    def propose(self, view, trigger):
        record = view.record(trigger)
        if record.kind == "evidence":
            data = json.loads(view.evidence[trigger])
            hours, value = data["estimated_hours"], data["estimated_project_value"]
            valid_from = record.event_at
        else:
            data = json.loads(view.evidence[record.value["evidence"]])
            hours, value = data["elapsed_hours"], data["measured_project_value"]
            valid_from = record.event_at
        changes = []
        for subject, slot, content in (("host", "hours", hours), ("self", "project_value", value)):
            if self.noop:
                content = view.state(subject, slot).value["content"]
            changes.append({"subject": subject, "slot": slot, "value": content,
                "support": [trigger], "predecessor": view.versions.get(f"{subject}:{slot}"),
                "valid_from": valid_from, "epistemic": "synthetic_measured_estimate"})
        return {"model_ref": self.model_ref, "native_schema": "test-only/episode-v1",
                "native_output": {"measured": data, "no_op_control": self.noop}, "changes": changes}


class EpisodePersonality:
    model_ref = "synthetic/episode-personality-v1"

    def judge(self, view):
        # A declared state-consuming test double. This proves delivery, not the
        # behavioral benefit of persistent state over rereading raw outcomes.
        original = next(json.loads(b) for b in view.evidence.values() if "research_budget" in json.loads(b))
        hours = view.state("host", "hours").value["content"]
        value = view.state("self", "project_value").value["content"]
        return {"model_ref": self.model_ref, "native_schema": "test-only/episode-v1",
            "support": [r.id for r in view.records if r.kind in {"evidence", "claim", "mission", "outcome"}],
            "native_output": {"plan": "research_first" if hours > original["research_budget"] else "project_first",
                "expected_hours": hours, "project_worth_pursuing": value >= 6,
                "project_value": value, "expression_intent": "protect both commitments",
                "unknown_native_field": ["retain", {"nested": True}]}}


class SyntheticWorld:
    def __init__(self, path, hours, value):
        self.path, self.hours, self.value = path, hours, value

    def execute(self, work):
        request = work["request"]
        if request["task"] != "project":
            raise ValueError("unsupported synthetic action")
        result = {"operation_id": work["operation_id"], "elapsed_hours": self.hours,
            "measured_project_value": self.value, "project_exists": True,
            "research_submitted": self.hours <= request["research_budget"]}
        self.path.write_text(json.dumps(result))
        return {"success": True}  # Does not establish either mission's outcome.


def read_world(path):
    return json.loads(path.read_text())


class EpisodeTests(unittest.TestCase):
    def episode(self, hours=12, value=9, *, approve=True, noop=False, noise=None):
        with tempfile.TemporaryDirectory() as root:
            store = open_store(root)
            try:
                for actor, role in (("formation", "mfm"), ("personality", "pe"),
                                    ("reader", "observer"), ("executor", "executor")):
                    store.grant("grant-" + actor, actor, role)
                kernel = ContinuityKernel(store)
                original = {"estimated_hours": 4, "estimated_project_value": 3,
                            "research_budget": 8, "source_anchor": "curious and deliberate"}
                evidence = store.capture("original", "owner", "host", json.dumps(original).encode(), event_at=T0)
                anchor = store.initialize_state("source", "source_person", "anchor", original["source_anchor"],
                                                support=(evidence,), valid_from=T0)
                project = store.create_mission("project", "Produce project", "project artifact exists")
                research = store.create_mission("research", "Submit research", "submitted before deadline",
                                                 conflicts=(project,))
                proposal = kernel.form("initial-formation", "formation", EpisodeFormation(), evidence)
                kernel.activate("initial-approval", "owner", proposal)
                first = kernel.judge("first", "personality", EpisodePersonality())
                before = store.record(first).value["packet"]["native_output"]
                action = kernel.authorize_action("authorize", first, {"task": "project", "research_budget": 8},
                    missions=(project, research), executor="executor", owner_reason="host chooses project")
                work = kernel.claim_action(action, "executor")
                world = SyntheticWorld(Path(root) / "world.json", hours, value)
                kernel.acknowledge("ack", "executor", action, world.execute(work))
                self.assertEqual(kernel.mission_status(project), "unverified")
                observed = read_world(world.path)
                self.assertEqual(observed["operation_id"], action)
                raw = json.dumps(observed).encode()
                observation = store.capture("measurement", "reader", "world", raw, event_at=now(),
                                            source_root="independent-world-measurement", observes_action=action)
                assessments = {
                    project: {"status": "met" if observed["project_exists"] else "missed",
                              "criterion": store.record(project).value["criterion"]},
                    research: {"status": "met" if observed["research_submitted"] else "missed",
                               "criterion": store.record(research).value["criterion"]},
                }
                outcome = kernel.observe("outcome", "reader", action, observation, assessments)
                if noise:
                    store.capture("irrelevant", "owner", "world", json.dumps({"weather_color": noise}).encode(), event_at=now())
                revision = kernel.form("revision", "formation", EpisodeFormation(noop), outcome)
                if approve:
                    kernel.activate("revision-approval", "owner", revision)
                view = store.recollect("personality", "judgment")
                self.assertEqual(view.evidence[observation], raw)  # Also when approval is withheld.
                self.assertNotIn(revision, {r.id for r in view.records})
                self.assertEqual(view.state("source_person", "anchor").id, anchor)
                self.assertIn(("observed_after", action), store.record(outcome).links)
                statuses = [kernel.mission_status(project), kernel.mission_status(research)]
                store.close()
                # A fresh process performs the later judgment using persisted state.
                code = (
                    "import json,sys; sys.path.insert(0,sys.argv[2]); "
                    "from test_continuity_store import open_store; "
                    "from test_continuity_episode import EpisodePersonality; "
                    "from flora.continuity.kernel import ContinuityKernel; "
                    "s=open_store(sys.argv[1]); k=ContinuityKernel(s); "
                    "j=k.judge('later','personality',EpisodePersonality()); "
                    "print(json.dumps(s.record(j).value['packet']['native_output'])); s.close()"
                )
                child = subprocess.run([sys.executable, "-B", "-c", code, root,
                                        str(Path(__file__).resolve().parent)], capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stderr)
                return before, json.loads(child.stdout), statuses
            finally:
                store.close()

    def test_mixed_outcome_revises_host_and_self_after_fresh_process(self):
        before, after, statuses = self.episode()
        self.assertEqual(statuses, ["met", "missed"])
        self.assertEqual((before["plan"], before["project_value"]), ("project_first", 3))
        self.assertEqual((after["plan"], after["expected_hours"], after["project_value"]), ("research_first", 12, 9))
        self.assertTrue(after["project_worth_pursuing"])
        self.assertEqual(after["unknown_native_field"], ["retain", {"nested": True}])

    def test_coherent_alternative_world_changes_only_warranted_estimates(self):
        before, short, statuses = self.episode(hours=2)
        self.assertEqual(statuses, ["met", "met"])
        self.assertEqual(short["plan"], "project_first")
        self.assertEqual(short["expected_hours"], 2)
        self.assertEqual(short["project_value"], 9)
        self.assertEqual(before["expected_hours"], 4)

    def test_irrelevant_detail_does_not_change_declared_judgment(self):
        self.assertEqual(self.episode(noise="blue"), self.episode(noise="orange"))

    def test_withheld_approval_and_approved_noop_keep_state_but_not_hide_outcome(self):
        before, withheld, statuses = self.episode(approve=False)
        self.assertEqual(before, withheld)
        self.assertEqual(statuses, ["met", "missed"])
        _, noop, _ = self.episode(noop=True)
        self.assertEqual(before, noop)


if __name__ == "__main__":
    unittest.main()

"""Connected authority controls with explicitly synthetic, content-reading ports."""
import json
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from test_continuity_store import StoreFixture, open_store, T0


class FormationDouble:
    model_ref = "synthetic/mfm-v1"
    calls = 0

    def propose(self, view, trigger):
        self.calls += 1
        hours = json.loads(view.evidence[trigger])["hours"]
        return {"model_ref": self.model_ref, "native_schema": "test-only/1",
            "native_output": {"read_hours": hours, "extra_field": "must survive"},
            "changes": [{"subject": "host", "slot": "hours", "value": hours,
                "support": [trigger], "predecessor": view.versions.get("host:hours"),
                "valid_from": T0, "epistemic": "owner_statement"}]}


class JudgmentDouble:
    model_ref = "synthetic/pe-v1"

    def judge(self, view):
        hours = [json.loads(b)["hours"] for b in view.evidence.values() if "hours" in json.loads(b)][-1]
        state = view.state("host", "hours")
        if state:
            hours = state.value["content"]
        return {"model_ref": self.model_ref, "native_schema": "test-only/1",
            "support": [r.id for r in view.records if r.kind in {"evidence", "claim", "mission"}],
            "native_output": {"decision": "defer" if hours > 8 else "proceed",
                "assumptions": {"host_hours": hours}, "expression": "full packet retained"}}


class KernelFixture(StoreFixture):
    def make_kernel(self):
        from flora.continuity.kernel import ContinuityKernel
        self.make_store()
        self.kernel_type = ContinuityKernel
        for actor, role in (("formation", "mfm"), ("personality", "pe"),
                            ("reader", "observer"), ("executor", "executor")):
            self.store.grant("grant-" + actor, actor, role)
        self.kernel = ContinuityKernel(self.store)
        self.evidence = self.capture()
        self.mission = self.store.create_mission("mission", "Finish research", "submission exists")

    def action(self):
        decision = self.kernel.judge("judge", "personality", JudgmentDouble())
        return self.kernel.authorize_action("action", decision, {"work_hours": 12},
            missions=(self.mission,), executor="executor", owner_reason="owner chooses project")


class KernelTests(KernelFixture, unittest.TestCase):
    def setUp(self):
        self.make_kernel()

    def test_exact_independent_activation_and_full_native_packet(self):
        producer = FormationDouble()
        proposal = self.kernel.form("form", "formation", producer, self.evidence)
        self.assertEqual(self.kernel.form("form", "formation", producer, self.evidence), proposal)
        self.assertEqual(producer.calls, 1)
        self.assertIsNone(self.store.recollect("personality", "judgment").state("host", "hours"))
        with self.assertRaises(PermissionError):
            self.kernel.activate("self-approval", "formation", proposal)
        self.kernel.activate("approval", "owner", proposal)
        state = self.store.recollect("personality", "judgment").state("host", "hours")
        self.assertEqual(state.value["content"], 4)
        self.assertEqual(state.value["packet"]["native_output"]["extra_field"], "must survive")
        self.assertIn(("derived_from", proposal), state.links)

    def test_unseen_contradiction_invalidates_proposed_revision(self):
        proposal = self.kernel.form("form", "formation", FormationDouble(), self.evidence)
        self.capture("contradiction", b'{"hours":12}')
        with self.assertRaisesRegex(ValueError, "stale"):
            self.kernel.activate("approval", "owner", proposal)
        self.assertIsNone(self.store.recollect("personality", "judgment").state("host", "hours"))

    def test_inference_has_no_native_handles_and_rechecks_authority(self):
        parent = self
        class Revoked(JudgmentDouble):
            def judge(self, view):
                parent.assertEqual(parent.store._db._children, 0)
                parent.store.revoke("revoke", "personality")
                return super().judge(view)
        with self.assertRaises(PermissionError):
            self.kernel.judge("judge", "personality", Revoked())
        self.assertFalse(any(r.kind == "judgment" for r in self.store.recollect("owner", "judgment").records))

    def test_new_evidence_during_inference_prevents_publication(self):
        parent = self
        class Changed(JudgmentDouble):
            def judge(self, view):
                parent.capture("contradiction", b'{"hours":14}')
                return super().judge(view)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.kernel.judge("judge", "personality", Changed())

    def test_actor_ack_is_not_completion_and_unknown_effect_is_not_retried(self):
        action = self.action()
        work = self.kernel.claim_action(action, "executor")
        self.assertEqual(work["operation_id"], action)
        self.assertEqual(work["request"], {"work_hours": 12})
        self.store.close()
        self.store = open_store(self.tmp.name)
        self.kernel = self.kernel_type(self.store)
        self.assertIsNone(self.kernel.claim_action(action, "executor"))
        self.kernel.acknowledge("ack", "executor", action, {"success": True})
        self.assertEqual(self.kernel.mission_status(self.mission), "unverified")
        self.store.grant("changed-role", "executor", "observer")
        with self.assertRaises(PermissionError):
            self.kernel.observe("outcome", "executor", action, self.evidence,
                                {self.mission: {"status": "met"}})

    def test_revocation_before_dispatch_blocks_effect(self):
        action = self.action()
        self.store.revoke("revoke", "executor")
        with self.assertRaises(PermissionError):
            self.kernel.claim_action(action, "executor")

    def test_withdrawal_invalidates_descendants_and_rejects_old_restore(self):
        proposal = self.kernel.form("form", "formation", FormationDouble(), self.evidence)
        self.kernel.activate("approval", "owner", proposal)
        old_view = self.store.recollect("personality", "judgment")
        backup = self.store.path.parent / "old-checkpoint"
        self.store._db.checkpoint(backup)
        self.kernel.withdraw("withdraw", self.evidence)
        floor = self.store.lifecycle_epoch
        with self.assertRaisesRegex(ValueError, "stale"):
            self.store.validate_view(old_view, "personality")
        view = self.store.recollect("personality", "judgment")
        self.assertNotIn(self.evidence, view.evidence)
        self.assertIsNone(view.state("host", "hours"))
        self.assertFalse(any(r.kind in {"activation", "claim"} for r in view.records))
        from flora.continuity.store import ContinuityStore
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            ContinuityStore(backup, scope=self.store.scope, key=b"k"*32,
                            objects=self.store._objects, required_lifecycle_epoch=floor)

    def test_failed_activation_leaves_no_claim_approval_or_head(self):
        class MixedFormation(FormationDouble):
            def propose(self, view, trigger):
                packet = super().propose(view, trigger)
                packet["changes"].append(dict(packet["changes"][0], subject="self",
                                               slot="project_value", value=9))
                return packet
        proposal = self.kernel.form("form", "formation", MixedFormation(), self.evidence)
        before = self.store.recollect("personality", "judgment")
        from flora.continuity.native import Transaction
        with patch.object(Transaction, "commit", side_effect=RuntimeError("publication fault")):
            with self.assertRaisesRegex(RuntimeError, "publication fault"):
                self.kernel.activate("approval", "owner", proposal)
        after = self.store.recollect("personality", "judgment")
        self.assertEqual((after.records, after.heads, after.generation),
                         (before.records, before.heads, before.generation))
        self.kernel.activate("approval", "owner", proposal)
        fresh = self.store.recollect("personality", "judgment")
        self.assertEqual(fresh.state("host", "hours").value["content"], 4)
        self.assertEqual(fresh.state("self", "project_value").value["content"], 9)

    def test_formation_cannot_rewrite_source_person_anchor(self):
        anchor = self.store.initialize_state("anchor", "source_person", "anchor", "fixed",
                                             support=(self.evidence,), valid_from=T0)
        class MisattributedFormation(FormationDouble):
            def propose(self, view, trigger):
                packet = super().propose(view, trigger)
                packet["changes"][0].update(subject="source_person", slot="anchor",
                                              predecessor=anchor, value="host trait")
                return packet
        before = self.store.recollect("owner", "judgment")
        with self.assertRaisesRegex(ValueError, "source-person"):
            self.kernel.form("form", "formation", MisattributedFormation(), self.evidence)
        after = self.store.recollect("owner", "judgment")
        self.assertEqual(after.records, before.records)
        self.assertEqual(after.state("source_person", "anchor").value["content"], "fixed")

    def test_withdrawal_covers_offered_content_omitted_from_model_citations(self):
        unaffected = self.kernel.judge("unexposed", "personality", JudgmentDouble())
        other = self.capture("other", b'{"hours":7,"private":"withdraw this phrase"}')
        parent = self
        class UnderreportedFormation(FormationDouble):
            def propose(self, view, trigger):
                packet = super().propose(view, trigger)
                packet["native_output"]["copied"] = view.evidence[other].decode()
                return packet
        proposal = self.kernel.form("form", "formation", UnderreportedFormation(), self.evidence)
        claims = self.kernel.activate("approve", "owner", proposal)
        class UnderreportedJudgment(JudgmentDouble):
            def judge(self, view):
                packet = super().judge(view)
                packet["support"] = [parent.evidence]
                packet["native_output"]["copied"] = view.evidence[other].decode()
                return packet
        judgment = self.kernel.judge("judge", "personality", UnderreportedJudgment())
        self.kernel.withdraw("withdraw", other)
        for identity in (proposal, *claims, judgment):
            self.assertEqual(self.store.record(identity).status, "withdrawn")
        self.assertNotIn("withdraw this phrase", repr(self.store.recollect("owner", "judgment")))
        self.assertEqual(self.store.record(unaffected).status, "active")

    def future_change(self):
        start = datetime.now(timezone.utc) + timedelta(seconds=30)
        boundary = start + timedelta(seconds=1)
        self.store.initialize_state("initial", "host", "hours", 4,
                                    support=(self.evidence,), valid_from=T0)
        self.store.initialize_state("future", "host", "hours", 12,
                                    support=(self.evidence,), valid_from=boundary.isoformat())
        return start.isoformat(), (boundary + timedelta(seconds=1)).isoformat()

    def test_valid_time_boundary_during_inference_invalidates_read_basis(self):
        start, end = self.future_change()
        with patch("flora.continuity.store.now", return_value=start) as clock:
            class CrossesBoundary(JudgmentDouble):
                def judge(self, view):
                    packet = super().judge(view)
                    clock.return_value = end
                    return packet
            with self.assertRaisesRegex(ValueError, "stale|time"):
                self.kernel.judge("judge", "personality", CrossesBoundary())

    def test_time_boundary_blocks_approval_and_dispatch_without_any_write(self):
        start, end = self.future_change()
        with patch("flora.continuity.store.now", return_value=start) as clock:
            proposal = self.kernel.form("form", "formation", FormationDouble(), self.evidence)
            clock.return_value = end
            with self.assertRaisesRegex(ValueError, "stale|time"):
                self.kernel.activate("approve", "owner", proposal)
        with patch("flora.continuity.store.now", return_value=start) as clock:
            action = self.action()
            clock.return_value = end
            with self.assertRaisesRegex(ValueError, "stale|time"):
                self.kernel.claim_action(action, "executor")

    def test_expiration_rejects_crossing_but_time_within_interval_is_valid(self):
        start = datetime.now(timezone.utc) + timedelta(seconds=30)
        boundary = start + timedelta(seconds=10)
        self.store.initialize_state("expires", "host", "hours", 4, support=(self.evidence,),
                                    valid_from=T0, valid_to=boundary.isoformat())
        with patch("flora.continuity.store.now", return_value=start.isoformat()) as clock:
            class WithinInterval(JudgmentDouble):
                def judge(self, view):
                    packet = super().judge(view)
                    clock.return_value = (start + timedelta(seconds=1)).isoformat()
                    return packet
            self.kernel.judge("within", "personality", WithinInterval())
            class Expires(JudgmentDouble):
                def judge(self, view):
                    packet = super().judge(view)
                    clock.return_value = (boundary + timedelta(seconds=1)).isoformat()
                    return packet
            with self.assertRaisesRegex(ValueError, "stale|time"):
                self.kernel.judge("expired", "personality", Expires())

    def test_old_sample_with_future_event_time_cannot_certify_later_action(self):
        old = self.store.capture("old-sample", "reader", "world", b'{"project_exists":false}',
                                 event_at="2099-01-01T00:00:00Z")
        action = self.action()
        self.kernel.claim_action(action, "executor")
        self.assertLess(self.store.record(old).recorded_at, self.store.record(action).recorded_at)
        with self.assertRaisesRegex(ValueError, "observation|bound|dispatch"):
            self.kernel.observe("outcome", "reader", action, old,
                {self.mission: {"status": "met", "criterion": "submission exists"}})
        self.assertEqual(self.kernel.mission_status(self.mission), "unverified")

    def test_observation_is_bound_to_exact_action_and_goal_criterion(self):
        from flora.continuity.store import now
        first = self.action()
        self.kernel.claim_action(first, "executor")
        second_judgment = self.kernel.judge("second-judge", "personality", JudgmentDouble())
        second = self.kernel.authorize_action("second", second_judgment, {"work_hours": 2},
            missions=(self.mission,), executor="executor", owner_reason="another attempt")
        self.kernel.claim_action(second, "executor")
        sample = self.store.capture("sample-first", "reader", "world", b'{"submitted":true}',
                                    event_at=now(), observes_action=first)
        assessment = {self.mission: {"status": "met", "criterion": "submission exists"}}
        with self.assertRaisesRegex(ValueError, "observation|bound"):
            self.kernel.observe("wrong-action", "reader", second, sample, assessment)
        current = self.store.capture("sample-second", "reader", "world", b'{"submitted":true}',
                                     event_at=now(), observes_action=second)
        with self.assertRaisesRegex(ValueError, "criterion"):
            self.kernel.observe("wrong-criterion", "reader", second, current,
                                {self.mission: {"status": "met", "criterion": "unrelated criterion"}})
        self.kernel.observe("right", "reader", second, current, assessment)
        self.assertEqual(self.kernel.mission_status(self.mission), "met")


if __name__ == "__main__":
    unittest.main()

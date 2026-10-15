"""Actual encrypted authority on the pinned engine, scoped to one local owner."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cognitive_kernel.contracts import ProductHostScope
from flora.selected.object_store import EncryptedObjectPlane, LocalObjectBackend

T0 = "2026-10-01T10:00:00+00:00"
T1 = "2026-10-02T10:00:00+00:00"


def open_store(root, key=b"k" * 32, host="ari", **kwargs):
    from flora.continuity.store import ContinuityStore
    scope = ProductHostScope.create(product_id="friday", host_instance_id=host,
        schema_version="1.0.0", encryption_domain="continuity-test")
    plane = EncryptedObjectPlane(scope=scope, key=key,
        backend=LocalObjectBackend(Path(root) / "objects"))
    return ContinuityStore(Path(root) / "authority", scope=scope,
                           key=key, objects=plane, **kwargs)


class StoreFixture:
    def make_store(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = open_store(self.tmp.name)
        self.addCleanup(lambda: self.store.close())

    def capture(self, op="original", content=b'{"hours":4}'):
        return self.store.capture(op, "owner", "host", content, event_at=T0)


class StoreTests(StoreFixture, unittest.TestCase):
    def setUp(self):
        self.make_store()

    def test_exact_bytes_encrypted_retry_and_pending_formation_reopen(self):
        secret = b"Ari estimates four hours for the project."
        identity = self.capture(content=secret)
        view = self.store.recollect("owner", "judgment")
        self.assertEqual(view.evidence[identity], secret)
        self.assertEqual(self.capture(content=secret), identity)
        self.assertEqual(self.store.recollect("owner", "judgment").generation, view.generation)
        pending = self.store.pending("owner")
        self.assertEqual([(p["kind"], p["source"]) for p in pending], [("formation", identity)])
        with self.assertRaisesRegex(ValueError, "idempotency"):
            self.capture(content=b"different request")
        self.store.close()
        for path in Path(self.tmp.name).rglob("*"):
            if path.is_file():
                self.assertNotIn(secret, path.read_bytes())
        self.store = open_store(self.tmp.name)
        self.assertEqual(self.store.recollect("owner", "judgment").evidence[identity], secret)
        self.assertEqual(self.store.pending("owner"), pending)

    def test_scope_and_key_are_bound_on_reopen(self):
        self.store.close()
        for args in ({"key": b"z" * 32}, {"host": "other"}):
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, "key|scope"):
                open_store(self.tmp.name, **args)

    def test_failed_commit_publishes_neither_capture_nor_pending_work(self):
        from flora.continuity.native import Transaction
        before = self.store.recollect("owner", "judgment")
        with patch.object(Transaction, "commit", side_effect=RuntimeError("injected commit fault")):
            with self.assertRaisesRegex(RuntimeError, "injected commit fault"):
                self.capture()
        after = self.store.recollect("owner", "judgment")
        self.assertEqual((after.records, after.generation), (before.records, before.generation))
        self.assertEqual(self.store.pending("owner"), [])
        self.capture()  # The failed operation did not consume its retry identity.

    def test_new_evidence_and_mutated_view_are_rejected(self):
        view = self.store.recollect("owner", "judgment")
        self.capture()
        with self.assertRaisesRegex(ValueError, "stale"):
            self.store.validate_view(view, "owner")
        view = self.store.recollect("owner", "judgment")
        view.evidence.clear()
        with self.assertRaisesRegex(ValueError, "seal"):
            self.store.validate_view(view, "owner")

    def test_revocation_blocks_old_and_new_context(self):
        self.store.grant("grant", "reader", "pe")
        view = self.store.recollect("reader", "judgment")
        self.store.revoke("revoke", "reader")
        with self.assertRaises(PermissionError):
            self.store.validate_view(view, "reader")
        with self.assertRaises(PermissionError):
            self.store.recollect("reader", "judgment")

    def test_two_time_axes_preserve_what_was_known_and_when_it_applied(self):
        evidence = self.capture()
        initial = self.store.initialize_state("state1", "host", "hours", 4,
                                             support=(evidence,), valid_from=T0)
        known_before = self.store.record(initial).recorded_at
        corrected = self.store.initialize_state("state2", "host", "hours", 12,
                                               support=(evidence,), valid_from=T1)
        self.assertEqual(self.store.state_at("owner", "host", "hours", valid_at=T0).id, initial)
        self.assertEqual(self.store.state_at("owner", "host", "hours", valid_at=T1,
                                            known_at=known_before).id, initial)
        self.assertEqual(self.store.state_at("owner", "host", "hours", valid_at=T1).id, corrected)
        self.assertEqual(self.store.record(initial).value["content"], 4)

    def test_missing_original_fails_closed(self):
        self.capture()
        objects = [p for p in (Path(self.tmp.name) / "objects").rglob("*") if p.is_file()]
        objects[0].write_bytes(b"broken")
        with self.assertRaises(ValueError):
            self.store.recollect("owner", "judgment")


if __name__ == "__main__":
    unittest.main()

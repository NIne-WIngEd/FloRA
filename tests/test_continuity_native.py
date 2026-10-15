"""Real native transaction behavior; no in-memory or alternate-engine fallback."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class ConfigurationTests(unittest.TestCase):
    def test_invalid_timeout_is_rejected_before_loading_native_library(self):
        from flora.continuity.native import RocksDB
        # This is a numeric boundary, not an experiment's response-time target.
        maximum = (1 << 31) - 1
        for value in (-1, True, 1.5, maximum + 1, 1 << 80):
            with self.subTest(value=value), patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError):
                    RocksDB("unused", lock_timeout_ms=value)


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("flora.continuity"),
                             "shared RocksDB foundation not implemented")
        from flora.continuity.native import RocksDB
        self.engine = RocksDB
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "db"
        self.db = RocksDB(self.path, lock_timeout_ms=25)
        self.addCleanup(self.db.close)

    def test_atomic_binary_records_rollback_and_reopen(self):
        with self.db.transaction() as tx:
            tx.put(b"event/1", b"source\0bytes")
            tx.put(b"head/host", b"event/1")
            tx.commit()
        with self.db.transaction() as tx:
            tx.put(b"event/2", b"not committed")
            tx.delete(b"head/host")
        self.db.close()
        with self.engine(self.path) as db:
            with db.snapshot() as snap:
                self.assertEqual(snap.get(b"head/host"), b"event/1")
                self.assertEqual(snap.scan(b"event/"), [(b"event/1", b"source\0bytes")])
                self.assertIsNone(snap.get(b"event/2"))

    def test_snapshot_is_stable_while_writer_commits(self):
        with self.db.transaction() as tx:
            tx.put(b"generation", b"1")
            tx.commit()
        with self.db.snapshot() as snap:
            with self.db.transaction() as tx:
                tx.put(b"contradiction/new", b"new relevant evidence")
                tx.put(b"generation", b"2")
                tx.commit()
            self.assertEqual(snap.get(b"generation"), b"1")
            self.assertEqual(snap.scan(b"contradiction/"), [])
        with self.db.transaction() as tx:
            self.assertEqual(tx.get(b"generation"), b"2")
            self.assertEqual(tx.scan(b"contradiction/"), [(b"contradiction/new", b"new relevant evidence")])

    def test_tracked_missing_key_prevents_conflicting_write(self):
        with self.db.transaction() as first:
            self.assertIsNone(first.get(b"head/missing"))
            with self.db.transaction() as conflicting:
                with self.assertRaisesRegex(RuntimeError, "[Tt]imeout|[Tt]imed out|[Bb]usy"):
                    conflicting.put(b"head/missing", b"unauthorized successor")
            first.put(b"head/missing", b"authorized successor")
            first.commit()
        with self.db.snapshot() as snap:
            self.assertEqual(snap.get(b"head/missing"), b"authorized successor")

    def test_stale_generation_rejects_newly_inserted_contradiction(self):
        with self.db.transaction() as tx:
            tx.put(b"generation", b"1")
            tx.commit()
        with self.db.transaction() as stale:
            self.assertEqual(stale.get(b"generation", tracked=False), b"1")
            self.assertEqual(stale.scan(b"contradiction/"), [])
            with self.db.transaction() as writer:
                writer.put(b"contradiction/new", b"new evidence")
                writer.put(b"generation", b"2")
                writer.commit()
            self.assertEqual(stale.scan(b"contradiction/"), [])
            with self.assertRaisesRegex(RuntimeError, "[Bb]usy|[Cc]onflict"):
                stale.get(b"generation")
        with self.db.transaction() as fresh:
            self.assertEqual(fresh.get(b"generation"), b"2")
            self.assertEqual(fresh.scan(b"contradiction/"),
                             [(b"contradiction/new", b"new evidence")])
            fresh.put(b"decision", b"includes contradiction")
            fresh.commit()

    def test_failed_construction_releases_acquired_native_resources(self):
        actual = self.db.lib
        for stage, expected in (
            ("rocksdb_transaction_options_set_lock_timeout", (0, 0)),
            ("rocksdb_transaction_get_snapshot", (1, 0)),
            ("rocksdb_readoptions_set_snapshot", (1, 1)),
        ):
            released = []

            class InjectFailure:
                def __getattr__(self, name):
                    function = getattr(actual, name)

                    def call(*args):
                        if name == stage:
                            raise RuntimeError("injected construction failure")
                        if name.endswith("_destroy") or name == "rocksdb_free":
                            released.append(name)
                        return function(*args)
                    return call

            with self.subTest(stage=stage):
                self.db.lib = InjectFailure()
                try:
                    with self.assertRaisesRegex(RuntimeError, "injected construction"):
                        self.db.transaction()
                finally:
                    self.db.lib = actual
                self.assertEqual(released.count("rocksdb_readoptions_destroy"), 1)
                self.assertEqual(released.count("rocksdb_transaction_options_destroy"), 1)
                self.assertEqual(released.count("rocksdb_writeoptions_destroy"), 1)
                self.assertEqual(released.count("rocksdb_transaction_destroy"), expected[0])
                self.assertEqual(released.count("rocksdb_free"), expected[1])
                self.assertEqual(self.db._children, 0)
                with self.db.transaction() as tx:
                    tx.put(b"after-construction-failure", stage.encode())
                    tx.commit()

    def test_live_handles_prevent_unsafe_database_close(self):
        with self.db.snapshot():
            with self.assertRaisesRegex(RuntimeError, "active"):
                self.db.close()
        with self.db.transaction() as tx:
            with self.assertRaisesRegex(RuntimeError, "active"):
                self.db.close()
        with self.assertRaisesRegex(RuntimeError, "closed"):
            tx.get(b"any")

    def test_checkpoint_reopens_committed_state(self):
        with self.db.transaction() as tx:
            tx.put(b"record", b"approved")
            tx.commit()
        target = Path(self.tmp.name) / "checkpoint"
        self.db.checkpoint(target)
        with self.engine(target) as restored:
            with restored.snapshot() as snap:
                self.assertEqual(snap.get(b"record"), b"approved")

    def test_real_process_death_before_and_after_commit(self):
        self.db.close()
        src = str(Path(__file__).resolve().parents[1] / "src")
        for commit in (False, True):
            code = (
                "import os,sys; sys.path.insert(0,sys.argv[1]); "
                "from flora.continuity.native import RocksDB; "
                "db=RocksDB(sys.argv[2]); tx=db.transaction(); "
                "tx.put(b'event/crash',b'actual'); tx.put(b'head/crash',b'event/crash'); "
                + ("tx.commit(); " if commit else "") + "os._exit(71)"
            )
            child = subprocess.run([sys.executable, "-c", code, src, str(self.path)],
                                   capture_output=True, text=True)
            self.assertEqual(child.returncode, 71, child.stderr)
            with self.engine(self.path) as restored:
                with restored.snapshot() as snap:
                    self.assertEqual(snap.get(b"event/crash"), b"actual" if commit else None)
                    self.assertEqual(snap.get(b"head/crash"), b"event/crash" if commit else None)


if __name__ == "__main__":
    unittest.main()

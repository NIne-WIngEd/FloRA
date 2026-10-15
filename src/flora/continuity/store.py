"""One local authority process; typed, encrypted history on actual TransactionDB.

Caller identities are supplied by the trusted local application, not accepted
from a network request. Worker models receive views, never this authority API.
Full scans deliberately bound the first experiment; no scalable search claim.
"""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import threading
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flora.selected.object_store import RawObjectReference
from .contracts import Record, ReadView, SUBJECTS, KINDS
from .native import RocksDB


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def require_time(value):
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return stamp.astimezone(timezone.utc).isoformat(timespec="microseconds")


def json_bytes(value):
    def encode(item):
        if isinstance(item, bytes):
            return {"$bytes": base64.b64encode(item).decode("ascii")}
        raise TypeError("unsupported continuity value")
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, default=encode).encode()


class Mutation:
    def __init__(self, store, native):
        self.store, self.native = store, native
        self.meta = self.get("meta")  # Tracked global fence covers absence too.
        stamp = max(datetime.fromisoformat(now()),
                    datetime.fromisoformat(self.meta["recorded_at"]) + timedelta(microseconds=1))
        self.recorded_at = stamp.isoformat(timespec="microseconds")
        self.changed = False
        self.time_basis = None

    def get(self, key):
        return self.store._get(self.native, key)

    def put(self, key, value):
        self.native.put(key.encode(), self.store._seal(key, value))
        self.changed = True

    def record(self, identity, *, candidate=False):
        record = self.store._record(self.native, identity)
        if record.status == "withdrawn" or (record.status == "candidate" and not candidate):
            raise ValueError("record is not currently eligible")
        return record

    def append(self, kind, subject, value, *, links=(), parents=(), event_at=None, status="active"):
        if kind not in KINDS or subject not in SUBJECTS or status not in {"active", "candidate", "historical"}:
            raise ValueError("unknown record kind, subject or status")
        if not isinstance(value, dict):
            raise TypeError("record value must be an object")
        parents = tuple(dict.fromkeys((*parents, *(target for _, target in links))))
        for parent in parents:
            self.record(parent, candidate=True)
        identity = uuid.uuid4().hex
        self.meta["sequence"] += 1
        record = Record(identity, kind, subject, value, parents, tuple(links),
                        require_time(event_at or self.recorded_at), self.recorded_at,
                        self.meta["sequence"], status)
        self.put("record/" + identity, asdict(record))
        self.put(f"order/{record.sequence:020d}", identity)
        for parent in parents:
            self.put(f"dependent/{parent}/{identity}", identity)
        return identity

    def head(self, subject, slot):
        head = self.get(self.store._key_for("head", f"{subject}:{slot}"))
        return head["record"] if head else None

    def set_head(self, subject, slot, identity):
        self.put(self.store._key_for("head", f"{subject}:{slot}"),
                 {"subject": subject, "slot": slot, "record": identity})

    def pending(self, identity, kind, source, **data):
        self.put("pending/" + identity, dict(id=identity, kind=kind, source=source,
                                             status="pending", **data))


class ContinuityStore:
    def __init__(self, path, *, scope, key, objects, required_lifecycle_epoch=0):
        scope.validate()
        if not isinstance(key, bytes) or len(key) != 32 or objects.scope != scope:
            raise ValueError("invalid key/scope binding")
        self.path, self.scope, self._key, self._objects = Path(path), scope, key, objects
        self._writer = threading.RLock()
        self._db = RocksDB(path)
        try:
            with self._db.transaction() as tx:
                blob = tx.get(b"meta")
                if blob is None:
                    if required_lifecycle_epoch:
                        raise ValueError("restore is missing lifecycle state")
                    meta = dict(schema=1, scope=scope.storage_scope(), generation=0,
                                authority_epoch=0, lifecycle_epoch=0, sequence=0, recorded_at=now())
                    tx.put(b"meta", self._seal("meta", meta))
                    grant_key = self._key_for("grant", "owner")
                    tx.put(grant_key.encode(), self._seal(grant_key, {"role": "owner", "enabled": True}))
                else:
                    try:
                        meta = self._open("meta", blob)
                    except Exception as exc:
                        raise ValueError("wrong key or scope") from exc
                    if meta["schema"] != 1 or meta["scope"] != scope.storage_scope():
                        raise ValueError("unsupported schema/scope")
                    if meta["lifecycle_epoch"] < required_lifecycle_epoch:
                        raise ValueError("restore predates required lifecycle epoch")
                tx.commit()
        except BaseException:
            self._db.close()
            raise

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _seal(self, identity, value):
        nonce = os.urandom(12)
        aad = ("continuity-v1:" + self.scope.storage_scope() + ":" + identity).encode()
        return nonce + AESGCM(self._key).encrypt(nonce, json_bytes(value), aad)

    def _open(self, identity, blob):
        aad = ("continuity-v1:" + self.scope.storage_scope() + ":" + identity).encode()
        return json.loads(AESGCM(self._key).decrypt(blob[:12], blob[12:], aad))

    def _fingerprint(self, value):
        return hmac.new(self._key, b"continuity-seal-v1:" + json_bytes(value), hashlib.sha256).hexdigest()

    def _key_for(self, kind, name):
        return kind + "/" + self._fingerprint([kind, name])

    def _get(self, reader, key):
        value = reader.get(key.encode())
        return self._open(key, value) if value is not None else None

    def _scan(self, reader, prefix):
        return [(key.decode(), self._open(key.decode(), value)) for key, value in reader.scan(prefix.encode())]

    def _authorize(self, reader, actor, roles=None):
        grant = self._get(reader, self._key_for("grant", actor))
        if not grant or not grant["enabled"] or (roles and grant["role"] not in roles):
            raise PermissionError("current actor permission denied")
        return grant["role"]

    def _record(self, reader, identity):
        value = self._get(reader, "record/" + identity)
        if value is None:
            raise ValueError("unknown record")
        status = self._get(reader, "status/" + identity)
        value["parents"] = tuple(value["parents"])
        value["links"] = tuple(tuple(link) for link in value["links"])
        if status:
            value["status"] = status
        return Record(**value)

    def record(self, identity):
        """Owner audit route, including inactive history; never a model input route."""
        with self._db.snapshot() as reader:
            return self._record(reader, identity)

    def _records(self, reader):
        return [self._record(reader, identity) for _, identity in self._scan(reader, "order/")]

    def _view_signature(self, view):
        return self._fingerprint(asdict(replace(view, seal="")))

    @staticmethod
    def _check_time(basis):
        stamp = require_time(now())
        if stamp < basis["valid_at"] or (basis["valid_until"] and stamp >= basis["valid_until"]):
            raise ValueError("stale valid-time basis; recollect before use")

    def _check_view(self, reader, view, actor):
        self._authorize(reader, actor)
        if view.actor != actor or view.scope != self.scope.storage_scope():
            raise PermissionError("view actor/scope mismatch")
        if not hmac.compare_digest(view.seal, self._view_signature(view)):
            raise ValueError("read view seal mismatch")
        meta = self._get(reader, "meta")
        if (view.generation, view.authority_epoch) != (meta["generation"], meta["authority_epoch"]):
            raise ValueError("stale read view; recollect before publication")
        self._check_time({"valid_at": view.valid_at, "valid_until": view.valid_until})

    def validate_view(self, view, actor):
        with self._db.snapshot() as reader:
            self._check_view(reader, view, actor)

    def replay(self, operation_id, actor, roles, request):
        with self._db.snapshot() as reader:
            self._authorize(reader, actor, roles)
            old = self._get(reader, self._key_for("operation", operation_id))
            if old:
                if old["request"] != self._fingerprint([actor, request]):
                    raise ValueError("idempotency identity reused with different request")
                return True, old["result"]
            return False, None

    def _write(self, operation_id, actor, roles, request, apply, *, view=None):
        if not isinstance(operation_id, str) or not operation_id:
            raise ValueError("stable operation identity required")
        with self._writer, self._db.transaction() as native:
            tx = Mutation(self, native)
            self._authorize(native, actor, roles)
            key = self._key_for("operation", operation_id)
            old = tx.get(key)
            fingerprint = self._fingerprint([actor, request])
            if old:
                if old["request"] != fingerprint:
                    raise ValueError("idempotency identity reused with different request")
                return old["result"]
            if view is not None:
                self._check_view(native, view, actor)
                tx.time_basis = {"valid_at": view.valid_at, "valid_until": view.valid_until}
            result = apply(tx)
            if not tx.changed:
                return result
            tx.append("commit", "world", {"operation": operation_id, "actor": actor,
                "request_digest": fingerprint, "generation": tx.meta["generation"] + 1}, status="historical")
            tx.meta["generation"] += 1
            tx.meta["recorded_at"] = tx.recorded_at
            tx.put("meta", tx.meta)
            tx.put(key, {"request": fingerprint, "result": result})
            if tx.time_basis:
                self._check_time(tx.time_basis)
            native.commit()
            return result

    def grant(self, operation_id, actor, role):
        if role not in {"mfm", "pe", "observer", "executor", "approver"} or actor == "owner":
            raise ValueError("invalid actor/role")
        def apply(tx):
            tx.put(self._key_for("grant", actor), {"role": role, "enabled": True})
            tx.meta["authority_epoch"] += 1
        return self._write(operation_id, "owner", {"owner"}, ["grant", actor, role], apply)

    def revoke(self, operation_id, actor):
        if actor == "owner":
            raise ValueError("cannot revoke local owner through worker grant")
        def apply(tx):
            tx.put(self._key_for("grant", actor), {"role": "revoked", "enabled": False})
            tx.meta["authority_epoch"] += 1
        return self._write(operation_id, "owner", {"owner"}, ["revoke", actor], apply)

    def capture(self, operation_id, actor, subject, content, *, event_at, source_root=None,
                observes_action=None):
        event_at = require_time(event_at)
        request = ["capture", subject, content, event_at, source_root, observes_action]
        found, result = self.replay(operation_id, actor, {"owner", "observer"}, request)
        if found:
            return result
        # Stage durable authenticated bytes before opening the publication transaction.
        reference = self._objects.put(content)
        def apply(tx):
            links = ()
            if observes_action is not None:
                self._authorize(tx.native, actor, {"observer"})
                action = tx.record(observes_action)
                effect = tx.get("effect/" + observes_action)
                if (action.kind != "action" or not effect or actor == action.value["executor"]
                        or effect["status"] not in {"uncertain", "acknowledged"}
                        or not effect["dispatched_at"] <= event_at <= tx.recorded_at):
                    raise ValueError("observation must be bound to an independent dispatched action and valid time")
                links = (("observed_after", observes_action),)
            identity = tx.append("evidence", subject, {"object_id": reference.object_id,
                "sha256": reference.plaintext_sha256, "size": reference.size,
                "source_actor": actor, "source_root": source_root or reference.object_id,
                "observes_action": observes_action}, event_at=event_at, links=links)
            tx.pending(identity, "formation", identity)
            return identity
        return self._write(operation_id, actor, {"owner", "observer"}, request, apply)

    def pending(self, actor):
        with self._db.snapshot() as reader:
            self._authorize(reader, actor, {"owner", "mfm"})
            return [value for _, value in self._scan(reader, "pending/") if value["status"] == "pending"]

    def create_mission(self, operation_id, goal, criterion, *, dependencies=(), conflicts=()):
        if not isinstance(goal, str) or not goal or not isinstance(criterion, str) or not criterion:
            raise ValueError("goal and independent acceptance criterion required")
        def apply(tx):
            for identity in (*dependencies, *conflicts):
                if tx.record(identity).kind != "mission":
                    raise ValueError("mission relation must name a mission")
            return tx.append("mission", "mission", {"goal": goal, "criterion": criterion},
                links=tuple(("depends_on", x) for x in dependencies) + tuple(("conflicts_with", x) for x in conflicts))
        return self._write(operation_id, "owner", {"owner"}, ["mission", goal, criterion, dependencies, conflicts], apply)

    def initialize_state(self, operation_id, subject, slot, value, *, support, valid_from, valid_to=None):
        valid_from = require_time(valid_from)
        valid_to = require_time(valid_to) if valid_to else None
        if not slot or not support or (valid_to and valid_to <= valid_from):
            raise ValueError("state needs slot, support and valid interval")
        def apply(tx):
            predecessor = tx.head(subject, slot)
            if subject == "source_person" and predecessor:
                raise ValueError("source-person anchor is immutable in this prototype")
            for identity in support:
                tx.record(identity)
            links = [("supports", x) for x in support]
            if predecessor:
                links.append(("supersedes", predecessor))
            identity = tx.append("claim", subject, {"slot": slot, "content": value,
                "valid_from": valid_from, "valid_to": valid_to, "predecessor": predecessor,
                "epistemic": "owner_statement"}, links=links)
            tx.set_head(subject, slot, identity)
            return identity
        return self._write(operation_id, "owner", {"owner"},
            ["initialize_state", subject, slot, value, support, valid_from, valid_to], apply)

    @staticmethod
    def _state(records, subject, slot, valid_at, known_at):
        matches = [r for r in records if r.kind == "claim" and r.status != "withdrawn"
            and r.subject == subject and r.value["slot"] == slot and r.recorded_at <= known_at
            and r.value["valid_from"] <= valid_at
            and (r.value.get("valid_to") is None or valid_at < r.value["valid_to"])]
        return max(matches, key=lambda r: r.sequence, default=None)

    def state_at(self, actor, subject, slot, *, valid_at, known_at=None):
        valid_at, known_at = require_time(valid_at), require_time(known_at or now())
        with self._db.snapshot() as reader:
            self._authorize(reader, actor)
            return self._state(self._records(reader), subject, slot, valid_at, known_at)

    def recollect(self, actor, purpose):
        roles = {"formation": {"mfm", "owner"}, "revision": {"mfm", "owner"},
                 "judgment": {"pe", "owner"}}
        if purpose not in roles:
            raise ValueError("unknown recollection purpose")
        with self._db.snapshot() as reader:
            self._authorize(reader, actor, roles[purpose])
            meta = self._get(reader, "meta")
            records = tuple(r for r in self._records(reader)
                            if r.status in {"active", "historical"} and r.kind != "commit")
            evidence = {}
            for record in records:
                if record.kind == "evidence":
                    value = record.value
                    evidence[record.id] = self._objects.get(RawObjectReference(self.scope,
                        value["object_id"], value["sha256"], value["size"]))
            versions, heads = {}, {}
            stamp = now()
            for _, head in self._scan(reader, "head/"):
                if head["record"] is None:
                    continue
                name = f'{head["subject"]}:{head["slot"]}'
                versions[name] = head["record"]
                current = self._state(records, head["subject"], head["slot"], stamp, stamp)
                if current:
                    heads[name] = current.id
            view = ReadView(self.scope.storage_scope(), actor, purpose, meta["generation"],
                            meta["authority_epoch"], records, evidence, heads, versions, "")
            boundaries = [time for r in records if r.kind == "claim"
                          for time in (r.value["valid_from"], r.value.get("valid_to"))
                          if time is not None and time > stamp]
            view = replace(view, valid_at=stamp, valid_until=min(boundaries, default=None))
            return replace(view, seal=self._view_signature(view))

    @property
    def lifecycle_epoch(self):
        with self._db.snapshot() as reader:
            return self._get(reader, "meta")["lifecycle_epoch"]

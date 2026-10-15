"""Governed decision episodes, not model implementation or a provider controller."""
import json
import uuid

from .contracts import SUBJECTS
from .store import json_bytes, require_time


class ContinuityKernel:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _packet(packet, model_ref):
        # Retain the complete native payload, including fields we do not interpret.
        if (not isinstance(packet, dict) or packet.get("model_ref") != model_ref
                or not isinstance(packet.get("native_schema"), str)
                or not packet["native_schema"] or "native_output" not in packet):
            raise ValueError("complete versioned native model packet required")
        return json.loads(json_bytes(packet))

    @staticmethod
    def _basis(view):
        return {"generation": view.generation, "authority_epoch": view.authority_epoch,
                "seal": view.seal, "offered": [r.id for r in view.records], "coverage": view.coverage,
                "valid_at": view.valid_at, "valid_until": view.valid_until}

    @staticmethod
    def _support(view, identities):
        if not isinstance(identities, list) or not identities:
            raise ValueError("explicit eligible support required")
        offered = {r.id for r in view.records}
        if len(set(identities)) != len(identities) or not set(identities) <= offered:
            raise ValueError("support must name distinct offered records")

    def form(self, operation_id, actor, port, trigger):
        request = ["form", port.model_ref, trigger]
        found, result = self.store.replay(operation_id, actor, {"mfm"}, request)
        if found:
            return result
        view = self.store.recollect(actor, "formation")
        source = view.record(trigger)
        if source.kind not in {"evidence", "outcome"}:
            raise ValueError("formation trigger must be evidence or independently observed outcome")
        packet = self._packet(port.propose(view, trigger), port.model_ref)
        changes = packet.get("changes")
        if not isinstance(changes, list) or not changes:
            raise ValueError("formation must propose explicit changes")
        slots = set()
        for change in changes:
            subject, slot = change["subject"], change["slot"]
            if subject not in SUBJECTS - {"source_person"} or not isinstance(slot, str) or not slot:
                raise ValueError("invalid revision subject/slot; source-person anchor is protected")
            if (subject, slot) in slots:
                raise ValueError("duplicate proposed state slot")
            slots.add((subject, slot))
            if change["predecessor"] != view.versions.get(f"{subject}:{slot}"):
                raise ValueError("proposal predecessor differs from consumed view")
            self._support(view, change["support"])
            if trigger not in change["support"]:
                raise ValueError("each revision must identify its triggering evidence/outcome")
            start = require_time(change["valid_from"])
            end = require_time(change["valid_to"]) if change.get("valid_to") else None
            if end and end <= start:
                raise ValueError("invalid revision time interval")
            if not change.get("epistemic"):
                raise ValueError("explicit epistemic status required")
        def apply(tx):
            parents = tuple(dict.fromkeys(x for c in changes for x in c["support"]))
            for parent in parents:
                tx.record(parent)
            identity = tx.append("proposal", "world", {"packet": packet, "actor": actor,
                "trigger": trigger, "basis": self._basis(view),
                "publication_generation": tx.meta["generation"] + 1},
                links=tuple(("derived_from", p) for p in parents)
                      + tuple(("context_from", r.id) for r in view.records), status="candidate")
            pending = tx.get("pending/" + trigger)
            if pending:
                tx.put("pending/" + trigger, dict(pending, status="proposed", proposal=identity))
            return identity
        return self.store._write(operation_id, actor, {"mfm"}, request, apply, view=view)

    def activate(self, operation_id, actor, proposal):
        def apply(tx):
            candidate = tx.record(proposal, candidate=True)
            if candidate.kind != "proposal":
                raise ValueError("activation requires an exact proposal")
            if actor == candidate.value["actor"]:
                raise PermissionError("proposal cannot approve itself")
            if candidate.value["publication_generation"] != tx.meta["generation"]:
                raise ValueError("stale proposal; recollect before approval")
            tx.time_basis = candidate.value["basis"]
            self.store._check_time(tx.time_basis)
            packet = candidate.value["packet"]
            for change in packet["changes"]:
                if tx.head(change["subject"], change["slot"]) != change["predecessor"]:
                    raise ValueError("stale state predecessor")
                for identity in change["support"]:
                    tx.record(identity)
            approval = tx.append("approval", "world", {"actor": actor, "proposal": proposal},
                                 links=(("approves", proposal),))
            claims = []
            for change in packet["changes"]:
                links = [("supports", p) for p in change["support"]]
                links += [("derived_from", proposal), ("authorized_by", approval)]
                if change["predecessor"]:
                    links.append(("supersedes", change["predecessor"]))
                identity = tx.append("claim", change["subject"], {"slot": change["slot"],
                    "content": change["value"], "valid_from": require_time(change["valid_from"]),
                    "valid_to": require_time(change["valid_to"]) if change.get("valid_to") else None,
                    "epistemic": change["epistemic"], "predecessor": change["predecessor"],
                    "packet": packet}, links=links)
                tx.set_head(change["subject"], change["slot"], identity)
                claims.append(identity)
            activation = tx.append("activation", "world", {"claims": claims, "proposal": proposal},
                                   parents=(approval, *claims))
            tx.pending(activation, "projection_refresh", activation)
            return claims
        return self.store._write(operation_id, actor, {"owner", "approver"},
                                 ["activate", proposal], apply)

    def judge(self, operation_id, actor, port):
        request = ["judge", port.model_ref]
        found, result = self.store.replay(operation_id, actor, {"pe"}, request)
        if found:
            return result
        view = self.store.recollect(actor, "judgment")
        packet = self._packet(port.judge(view), port.model_ref)
        self._support(view, packet.get("support"))
        def apply(tx):
            for identity in packet["support"]:
                tx.record(identity)
            return tx.append("judgment", "self", {"packet": packet, "basis": self._basis(view),
                "publication_generation": tx.meta["generation"] + 1},
                links=tuple(("uses", p) for p in packet["support"])
                      + tuple(("context_from", r.id) for r in view.records))
        return self.store._write(operation_id, actor, {"pe"}, request, apply, view=view)

    def authorize_action(self, operation_id, judgment, request, *, missions, executor, owner_reason):
        if not isinstance(request, dict) or not missions or not owner_reason:
            raise ValueError("explicit request, goals and owner authorization required")
        def apply(tx):
            decision = tx.record(judgment)
            if decision.kind != "judgment" or decision.value["publication_generation"] != tx.meta["generation"]:
                raise ValueError("stale judgment; obtain a current judgment before authorizing action")
            tx.time_basis = decision.value["basis"]
            self.store._check_time(tx.time_basis)
            self.store._authorize(tx.native, executor, {"executor"})
            for mission in missions:
                if tx.record(mission).kind != "mission":
                    raise ValueError("action must pursue actual missions")
            identity = tx.append("action", "mission", {"request": request, "missions": list(missions),
                "executor": executor, "owner_reason": owner_reason,
                "time_basis": tx.time_basis,
                "publication_generation": tx.meta["generation"] + 1},
                links=(("judged_by", judgment), *(("pursues", m) for m in missions)))
            tx.put("effect/" + identity, {"status": "ready", "executor": executor})
            return identity
        return self.store._write(operation_id, "owner", {"owner"},
            ["authorize", judgment, request, missions, executor, owner_reason], apply)

    def claim_action(self, action, actor):
        def apply(tx):
            intent = tx.record(action)
            effect = tx.get("effect/" + action)
            if intent.kind != "action" or not effect or effect["executor"] != actor:
                raise PermissionError("action belongs to another executor")
            if effect["status"] != "ready":
                return None  # Unknown/acknowledged effects require reconciliation, not another call.
            if intent.value["publication_generation"] != tx.meta["generation"]:
                raise ValueError("stale action authorization")
            tx.time_basis = intent.value["time_basis"]
            self.store._check_time(tx.time_basis)
            tx.put("effect/" + action, dict(effect, status="uncertain", dispatched_at=tx.recorded_at))
            return {"operation_id": action, "request": intent.value["request"]}
        return self.store._write(uuid.uuid4().hex, actor, {"executor"}, ["dispatch", action], apply)

    def acknowledge(self, operation_id, actor, action, receipt):
        def apply(tx):
            intent = tx.record(action)
            effect = tx.get("effect/" + action)
            if intent.kind != "action" or not effect or effect["executor"] != actor:
                raise PermissionError("receipt actor differs from executor")
            if effect["status"] != "uncertain":
                raise ValueError("no unresolved dispatched action")
            identity = tx.append("ack", "world", {"receipt": receipt, "actor": actor},
                                 links=(("reports_on", action),))
            tx.put("effect/" + action, dict(effect, status="acknowledged", receipt=identity))
            return identity
        return self.store._write(operation_id, actor, {"executor"}, ["ack", action, receipt], apply)

    def observe(self, operation_id, actor, action, evidence, assessments):
        def apply(tx):
            intent = tx.record(action)
            effect = tx.get("effect/" + action)
            if intent.kind != "action" or not effect:
                raise ValueError("observation requires an action")
            if actor == intent.value["executor"]:
                raise PermissionError("executor cannot independently certify its own outcome")
            source = tx.record(evidence)
            if (source.kind != "evidence" or source.value["source_actor"] != actor
                    or source.value.get("observes_action") != action
                    or effect["status"] not in {"uncertain", "acknowledged"}
                    or source.recorded_at < effect["dispatched_at"]
                    or not effect["dispatched_at"] <= source.event_at <= source.recorded_at):
                raise ValueError("outcome needs independent observation bound to this dispatch")
            if set(assessments) != set(intent.value["missions"]):
                raise ValueError("assess every pursued goal separately, including unknown outcomes")
            for mission, assessment in assessments.items():
                if assessment.get("status") not in {"met", "missed", "unknown"}:
                    raise ValueError("invalid outcome status")
                goal = tx.record(mission)
                if assessment.get("criterion") != goal.value["criterion"]:
                    raise ValueError("observation must bind the exact mission criterion")
            identity = tx.append("outcome", "world", {"assessments": assessments,
                "observer": actor, "action": action, "evidence": evidence}, event_at=source.event_at,
                links=(("observed_after", action), ("supports", evidence),
                       *(("evaluates", m) for m in assessments)))
            tx.put("effect/" + action, dict(effect, status="observed", outcome=identity))
            tx.pending(identity, "revision", identity)
            return identity
        return self.store._write(operation_id, actor, {"observer"},
                                 ["observe", action, evidence, assessments], apply)

    def mission_status(self, mission):
        with self.store._db.snapshot() as reader:
            record = self.store._record(reader, mission)
            if record.kind != "mission" or record.status == "withdrawn":
                raise ValueError("mission is unavailable")
            outcomes = [r for r in self.store._records(reader) if r.kind == "outcome"
                        and r.status != "withdrawn" and mission in r.value["assessments"]]
            if not outcomes:
                return "unverified"
            latest = max(outcomes, key=lambda r: r.sequence)
            return latest.value["assessments"][mission]["status"]

    def withdraw(self, operation_id, source):
        """Revocation of use, not physical erasure or model unlearning."""
        def apply(tx):
            tx.record(source, candidate=True)
            affected, queue = set(), [source]
            while queue:
                identity = queue.pop()
                if identity in affected:
                    continue
                affected.add(identity)
                queue.extend(value for _, value in self.store._scan(tx.native, "dependent/" + identity + "/"))
            for identity in sorted(affected):
                tx.put("status/" + identity, "withdrawn")
                pending = tx.get("pending/" + identity)
                if pending:
                    tx.put("pending/" + identity, dict(pending, status="cancelled"))
                effect = tx.get("effect/" + identity)
                if effect:
                    tx.put("effect/" + identity, dict(effect, status="withdrawn"))
            for key, head in self.store._scan(tx.native, "head/"):
                if head["record"] in affected:
                    tx.put(key, dict(head, record=None))  # Never implicitly reactivate an old state.
            tx.meta["authority_epoch"] += 1
            tx.meta["lifecycle_epoch"] += 1
            event = tx.append("withdrawal", "world", {"source": source, "affected": sorted(affected)})
            tx.pending(event, "projection_cleanup", event, affected=sorted(affected))
            return sorted(affected)
        return self.store._write(operation_id, "owner", {"owner"}, ["withdraw", source], apply)

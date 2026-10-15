"""Narrow continuity envelopes; these are not substitutes for PE/MFM schemas."""
from dataclasses import dataclass, field
from typing import Any, Protocol

SUBJECTS = frozenset({"source_person", "host", "relationship", "self", "mission", "world"})
KINDS = frozenset({"evidence", "mission", "proposal", "claim", "judgment", "action",
                   "outcome", "approval", "activation", "withdrawal", "commit", "ack",
                   "memory", "formation_decision", "target"})


@dataclass(frozen=True)
class Record:
    id: str
    kind: str
    subject: str
    value: dict[str, Any]
    parents: tuple[str, ...]
    links: tuple[tuple[str, str], ...]
    event_at: str
    recorded_at: str
    sequence: int
    status: str


@dataclass(frozen=True)
class ReadView:
    scope: str
    actor: str
    purpose: str
    generation: int
    authority_epoch: int
    records: tuple[Record, ...]
    evidence: dict[str, bytes]
    heads: dict[str, str]
    versions: dict[str, str]
    seal: str
    coverage: str = "complete-authoritative-scan"
    valid_at: str = ""
    valid_until: str | None = None
    source_roots: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def state(self, subject: str, slot: str) -> Record | None:
        identity = self.heads.get(f"{subject}:{slot}")
        return next((r for r in self.records if r.id == identity), None)

    def record(self, identity: str) -> Record:
        return next(r for r in self.records if r.id == identity)


class FormationPort(Protocol):
    model_ref: str
    def propose(self, view: ReadView, trigger: str) -> dict: ...


class JudgmentPort(Protocol):
    model_ref: str
    def judge(self, view: ReadView) -> dict: ...

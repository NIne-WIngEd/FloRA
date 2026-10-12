"""Signed selected H permissions on the existing fictional phase data plane."""
import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cognitive_kernel.contracts import ProvenanceReference
from cognitive_kernel.experience import ExperienceEvent
from flora.selected.formation_policy import FormationPermissionAction, XTDBFormationPermissionPolicy, formation_permission_payload
from flora.selected.owner_authorization import Ed25519OwnerActionVerifier, OwnerActionProof, owner_action_message
from metadata_batch_fixture import install_current_metadata_batch


class PhaseHistoryPermissions:
    def __init__(self, fixture):
        self.f = fixture
        install_current_metadata_batch(fixture.connection)
        self.policy = XTDBFormationPermissionPolicy(scope=fixture.scope,
            authority_namespace_id=fixture.namespace, connection=fixture.connection, registry=fixture.registry)
        self.key, self.proofs, self.count = Ed25519PrivateKey.generate(), {}, 0
        self.verifier = Ed25519OwnerActionVerifier(scope=fixture.scope,
            owner_public_key=self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw), proofs=self.proofs)

    def grant(self, event_id, purpose, decision="allow"):
        f, policy = self.f, self.policy
        source = f.registry.lookup(event_id)
        previous = policy.current_action(event_id, purpose)
        self.count += 1
        action = FormationPermissionAction.create(scope=f.scope, authority_namespace_id=f.namespace,
            action_id="phase-history-grant-" + str(self.count), source_ref_id=event_id,
            source_registration_sha256=source.registration_sha256, purpose=purpose, decision=decision,
            generation=1 if previous is None else previous.generation + 1,
            previous_action_sha256=None if previous is None else previous.action_sha256,
            authorization_ref="fictional-enrolled-history-owner", authorized_at=f._clock())
        parents = (event_id,)
        if previous is not None:
            parents += (policy._stored_action(previous.action_id)["request_event_id"],)
        raw = f.objects.put(formation_permission_payload(action))
        event = ExperienceEvent.create(event_type="formation_permission_action", scope=f.scope,
            occurred_at=action.authorized_at, content_digest=raw.plaintext_sha256,
            provenance=ProvenanceReference.create(provenance_type="derived_inference",
                source_reference_ids=(raw.object_id,), derivation_activity_id="phase-history-permission",
                responsible_component="fictional-owner"), retention_class="ordinary_experience",
            storage_tier="raw_buffer", payload_reference=raw.object_id, parent_event_ids=parents)
        f.log.append(event, expected_revision=len(f.log.replay()) - 1)
        signature = self.key.sign(owner_action_message(event, "formation_permission"))
        self.proofs[event.event_id] = OwnerActionProof("formation_permission", event.event_id,
            event.event_sha256, base64.b64encode(signature).decode())
        policy.apply(action, request_event_id=event.event_id, log=f.log, objects=f.objects,
            references={raw.object_id: raw}, verifier=self.verifier)
        return action

    def grant_closure(self, event_id, purpose):
        """Exact registered parents only, each receiving its own signed action."""
        pending, seen = [event_id], set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            source = self.f.registry.lookup(current)
            if source is None:
                raise AssertionError("fixture grant has an unregistered parent")
            pending.extend(source.evidence.parent_refs)
            action = self.policy.current_action(current, purpose)
            if action is None or action.decision != "allow":
                self.grant(current, purpose)

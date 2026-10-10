"""Real owner-map connection over native fields; no factory/capture execution.

These controls qualify named ownership and current callback execution only.
They do not authenticate supplied field representations or prove a full capture.
"""
from types import MethodType
import unittest

from flora.selected import _phase_preparation as prep
from flora.selected.experiment_preregistration import (
    RegisteredExperimentPreregistration, XTDBExperimentPreregistrationCustody,
)
from flora.selected.phase_snapshots import PreregisteredPhaseCaptureLineageVerifier


class RegisteredPhaseHistoryOwnerConnectionTest(unittest.TestCase):
    def setUp(self):
        self.effects = []
        self.allowed = True
        self.history = object()
        self.store = object.__new__(XTDBExperimentPreregistrationCustody)
        self.store.histories = {('case', 'before'): self.history}

        def current():
            self.effects.append('current')
            if not self.allowed:
                raise PermissionError('controlled current authority withdrawn')

        # Opaque, live control port: admission may seal it, never execute it.
        self.store._current = current
        self.anchor = object.__new__(RegisteredExperimentPreregistration)
        self.anchor.store = self.store
        self.store.anchor = self.anchor
        self.consumer = object.__new__(PreregisteredPhaseCaptureLineageVerifier)
        self.consumer.preregistration = self.anchor
        self.consumer.history_for = self.anchor.history_for

    def owner_map(self):
        return prep._owner_map(None, 'capture', None, self.consumer, None)

    def test_actual_bound_history_owner_connects_without_executing_current(self):
        callback = self.anchor.history_for
        role = prep._bound_callback_role(callback)
        self.assertIsInstance(role, tuple, 'The actual native history owner is missing its named callback edge')
        self.assertEqual(role[:2], ('anchor', 'history_for'))
        self.assertIs(role[2][0], RegisteredExperimentPreregistration)
        self.assertIs(role[2][1], RegisteredExperimentPreregistration.history_for)
        self.assertIs(role[2][2], RegisteredExperimentPreregistration.history_for.__code__)
        mapped = self.owner_map()
        self.assertIsNotNone(mapped, 'A declared native history connection still falls back')
        self.assertIn(self.anchor, mapped[0])
        self.assertIn(self.store, mapped[0])
        self.assertEqual(self.effects, [], 'Admission executed a live authority callback')

    def test_execution_keeps_original_current_authority_callback_live(self):
        self.assertIs(self.anchor.history_for('case', 'before'), self.history)
        self.assertEqual(self.effects, ['current'])
        self.allowed = False
        with self.assertRaisesRegex(PermissionError, 'controlled current authority withdrawn'):
            self.anchor.history_for('case', 'before')
        self.assertEqual(self.effects, ['current', 'current'])

    def test_other_native_anchor_method_is_conservative_fallback(self):
        self.consumer.history_for = self.anchor.history_authority
        self.assertIsNone(self.owner_map())
        self.assertEqual(self.effects, [])

    def test_replaced_function_and_same_identity_changed_code_fall_back(self):
        original = RegisteredExperimentPreregistration.history_for
        original_code = original.__code__
        def replacement(self, case_id, phase):
            raise AssertionError('Admission invoked a replacement')
        try:
            RegisteredExperimentPreregistration.history_for = replacement
            self.consumer.history_for = self.anchor.history_for
            self.assertIsNone(self.owner_map())
        finally:
            RegisteredExperimentPreregistration.history_for = original
        try:
            original.__code__ = replacement.__code__
            self.consumer.history_for = self.anchor.history_for
            self.assertIsNone(self.owner_map())
        finally:
            original.__code__ = original_code
        self.assertEqual(self.effects, [])

    def test_subclass_anchor_does_not_inherit_native_callback_admission(self):
        class CustomAnchor(RegisteredExperimentPreregistration):
            pass
        custom = object.__new__(CustomAnchor)
        custom.store = self.store
        self.consumer.preregistration = custom
        self.consumer.history_for = custom.history_for
        self.assertIsNone(self.owner_map())
        self.assertEqual(self.effects, [])

    def test_proxy_bound_to_native_function_falls_back_without_getter(self):
        effects = self.effects
        class Proxy:
            def __getattribute__(self, name):
                effects.append('proxy getter')
                raise AssertionError('Admission invoked a proxy getter')
        proxy = object.__new__(Proxy)
        self.consumer.history_for = MethodType(RegisteredExperimentPreregistration.history_for, proxy)
        self.assertIsNone(self.owner_map())
        self.assertEqual(self.effects, [])

    def test_custom_control_getter_shape_falls_back_without_effects(self):
        effects = self.effects
        class CustomControl(XTDBExperimentPreregistrationCustody):
            def __getattribute__(self, name):
                effects.append('control getter')
                raise AssertionError('Admission invoked a control getter')
        self.anchor.store = object.__new__(CustomControl)
        self.assertIsNone(self.owner_map())
        self.assertEqual(self.effects, [])


if __name__ == '__main__':
    unittest.main()

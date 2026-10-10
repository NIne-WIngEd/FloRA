"""One fresh walk of real captured functions and reader bindings."""
import sys
import unittest
from unittest.mock import patch

from flora.selected import selected_authority_frame as frames
from flora.selected import selected_phase_authority as phase


_BOUND_GLOBAL = object()


class _Owner:
    def read(self):
        raise AssertionError("pure verification executed a reader")


class SharedContextBindingTest(unittest.TestCase):
    def setUp(self):
        self.owner = _Owner()
        self.reader = phase._ReaderBinding.capture(self.owner, "read")
        readers = (self.reader,)
        def leaf():
            return readers, _BOUND_GLOBAL
        def middle():
            return leaf()
        def root():
            return middle()
        self.binding = phase._FunctionBinding.capture(root)
        frames._register_binding(self.binding)
        self.middle = self.binding.nested[0]
        self.leaf = self.middle.nested[0]

    def verify(self):
        frames._require_frame_contracts()
        frames._verify_binding(self.binding)

    def _diamond_binding(self):
        readers = (self.reader,)
        def leaf():
            return readers, _BOUND_GLOBAL
        def branch(callback):
            def invoke():
                return callback()
            return invoke
        left, right = branch(leaf), branch(leaf)
        def root():
            return left(), right()
        binding = phase._FunctionBinding.capture(root)
        frames._register_binding(binding)
        left_capture, right_capture = binding.nested
        left_leaf, right_leaf = left_capture.nested[0], right_capture.nested[0]
        # capture() records the same leaf independently through each branch.
        self.assertIsNot(left_leaf, right_leaf)
        self.assertIs(left_leaf.function, right_leaf.function)
        self.assertIs(dict(zip(left_leaf.function.__code__.co_freevars,
            (value for _, value in left_leaf.closure)))["readers"], readers)
        self.assertIs(dict(zip(right_leaf.function.__code__.co_freevars,
            (value for _, value in right_leaf.closure)))["readers"], readers)
        return binding, left_capture, left_leaf, right_capture, right_leaf

    def test_diamond_checks_independent_captures_and_shared_reader_once_each_fresh_walk(self):
        binding, left, left_leaf, right, right_leaf = self._diamond_binding()
        own_check = getattr(phase._FunctionBinding, "_verify_shallow", phase._FunctionBinding.verify)
        checks, reader_checks, effects = [], [], []
        function_codes = {item.function.__code__ for item in (binding, left, left_leaf, right, right_leaf)}
        def observe(frame, event, argument):
            if event == "call":
                if frame.f_code is own_check.__code__:
                    checks.append(id(frame.f_locals["self"]))
                elif frame.f_code is phase._ReaderBinding.verify.__code__:
                    reader_checks.append(id(frame.f_locals["self"]))
                elif frame.f_code in function_codes or frame.f_code is _Owner.read.__code__:
                    effects.append("captured callback or reader")
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            frames._require_frame_contracts()
            frames._verify_binding(binding)
            first_checks, first_readers = tuple(checks), tuple(reader_checks)
            checks.clear()
            reader_checks.clear()
            frames._require_frame_contracts()
            frames._verify_binding(binding)
        finally:
            sys.setprofile(previous)
        self.assertEqual(effects, [])
        # Check reader multiplicity first: the published tree reaches this
        # assertion with two visits, rather than failing on fixture setup.
        self.assertEqual(first_readers, (id(self.reader),),
            "shared exact reader must be checked once in the first fresh walk")
        self.assertEqual(reader_checks, [id(self.reader)],
            "shared exact reader must be checked again in the next fresh walk")
        expected = (id(left_leaf), id(left), id(right_leaf), id(right), id(binding))
        self.assertEqual(first_checks, expected)
        self.assertEqual(checks, list(expected))

    def test_diamond_later_walk_rejects_shared_reader_and_later_branch_mutations(self):
        binding, left, left_leaf, right, right_leaf = self._diamond_binding()
        effects = []
        function_codes = {item.function.__code__ for item in (binding, left, left_leaf, right, right_leaf)}
        def replacement_reader(self):
            raise AssertionError("changed reader executed")
        function_codes.update((_Owner.read.__code__, replacement_reader.__code__))
        def observe(frame, event, argument):
            if event == "call" and frame.f_code in function_codes:
                effects.append("captured callback or reader")
        def verify():
            frames._require_frame_contracts()
            frames._verify_binding(binding)
        class EffectfulOwner:
            def __getattribute__(self, name):
                effects.append(name)
                raise AssertionError("changed reader owner dereferenced")
            def __eq__(self, other):
                effects.append("equality")
                raise AssertionError("changed reader owner compared")
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            verify()
            original_owner = self.reader.owner
            try:
                object.__setattr__(self.reader, "owner", EffectfulOwner())
                with self.assertRaisesRegex(PermissionError, "captured owner fields changed"):
                    verify()
            finally:
                object.__setattr__(self.reader, "owner", original_owner)
            verify()
            original_code = _Owner.read.__code__
            try:
                _Owner.read.__code__ = replacement_reader.__code__
                with self.assertRaisesRegex(PermissionError, "actual reader binding changed"):
                    verify()
            finally:
                _Owner.read.__code__ = original_code
            verify()
            original_capture_code = right_leaf.code
            try:
                object.__setattr__(right_leaf, "code", object())
                with self.assertRaisesRegex(PermissionError, "captured owner fields changed"):
                    verify()
            finally:
                object.__setattr__(right_leaf, "code", original_capture_code)
            verify()
            # Each branch has its own callback cell. Mutating only the right
            # branch must still be noticed after the left leaf was checked.
            cell, original_callback = right.closure[0]
            self.assertIsNot(cell, left.closure[0][0])
            def replacement_callback():
                raise AssertionError("changed callback executed")
            function_codes.add(replacement_callback.__code__)
            try:
                cell.cell_contents = replacement_callback
                with self.assertRaisesRegex(PermissionError, "actual callback binding changed"):
                    verify()
            finally:
                cell.cell_contents = original_callback
            verify()
        finally:
            sys.setprofile(previous)
        self.assertEqual(effects, [])

    def test_each_function_and_reader_is_checked_once_per_fresh_walk(self):
        # The pre-repair own checks live in verify(); after extraction they
        # live in _verify_shallow(). Observe actual code, never replace it.
        own_check = getattr(phase._FunctionBinding, "_verify_shallow", phase._FunctionBinding.verify)
        checks, reader_checks, effects = [], [], []
        function_codes = {item.function.__code__ for item in (self.binding, self.middle, self.leaf)}
        def observe(frame, event, argument):
            if event == "call":
                if frame.f_code is own_check.__code__:
                    checks.append(id(frame.f_locals["self"]))
                elif frame.f_code is phase._ReaderBinding.verify.__code__:
                    reader_checks.append(id(frame.f_locals["self"]))
                elif frame.f_code in function_codes:
                    effects.append("captured function")
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            self.verify()
            self.verify()
        finally:
            sys.setprofile(previous)
        expected = [id(self.leaf), id(self.middle), id(self.binding)]
        self.assertEqual(checks, expected * 2)
        self.assertEqual(reader_checks, [id(self.reader)] * 2)
        self.assertEqual(effects, [])

    def test_later_walk_rejects_leaf_code_closure_and_global_mutation(self):
        self.verify()
        original_code = self.leaf.function.__code__
        readers = ()
        def replacement():
            return readers, None
        try:
            self.leaf.function.__code__ = replacement.__code__
            with self.assertRaisesRegex(PermissionError, "actual callback binding changed"):
                self.verify()
        finally:
            self.leaf.function.__code__ = original_code
        cell, original = self.leaf.closure[0]
        try:
            cell.cell_contents = ()
            with self.assertRaisesRegex(PermissionError, "actual callback binding changed"):
                self.verify()
        finally:
            cell.cell_contents = original
        with patch.dict(globals(), {"_BOUND_GLOBAL": object()}):
            with self.assertRaisesRegex(PermissionError, "actual callback binding changed"):
                self.verify()
        self.verify()

    def test_replaced_capture_and_reader_fields_reject_before_effects(self):
        self.verify()
        effects = []
        class Effectful:
            def __getattribute__(self, name):
                effects.append(name)
                raise AssertionError("replacement dereferenced")
            def __eq__(self, other):
                effects.append("equality")
                raise AssertionError("replacement compared")
        for owner, field, value in ((self.middle, "nested", (Effectful(),)),
                (self.leaf, "function", Effectful()), (self.reader, "owner", Effectful())):
            original = object.__getattribute__(owner, field)
            try:
                object.__setattr__(owner, field, value)
                with self.subTest(field=field), self.assertRaisesRegex(PermissionError, "captured owner fields changed"):
                    self.verify()
                self.assertEqual(effects, [])
            finally:
                object.__setattr__(owner, field, original)
        self.verify()

    def test_full_phase_binding_verification_still_rejects_leaf_mutation(self):
        self.binding.verify()
        cell, original = self.leaf.closure[0]
        try:
            cell.cell_contents = ()
            with self.assertRaisesRegex(PermissionError, "actual callback binding changed"):
                self.binding.verify()
        finally:
            cell.cell_contents = original
        self.binding.verify()

    def test_own_check_identity_and_code_are_pinned_before_execution(self):
        name = "_verify_shallow" if hasattr(phase._FunctionBinding, "_verify_shallow") else "verify"
        original = getattr(phase._FunctionBinding, name)
        effects = []
        def replacement(self, observed=effects):
            observed.append("changed own check")
        with patch.object(phase._FunctionBinding, name, new=replacement):
            with self.assertRaisesRegex(PermissionError, "verifier class changed"):
                self.verify()
        code = original.__code__
        try:
            original.__code__ = replacement.__code__
            with self.assertRaisesRegex(PermissionError, "verifier code changed"):
                self.verify()
        finally:
            original.__code__ = code
        self.assertEqual(effects, [])

    def test_custom_metaclass_reader_is_refused_before_class_lookup_effects(self):
        effects, armed = [], [False]
        class Lookup(type):
            def __getattribute__(cls, name):
                if armed[0]:
                    effects.append(name)
                return type.__getattribute__(cls, name)
        class Owner(metaclass=Lookup):
            def read(self):
                raise AssertionError("pure verifier executed a reader")
        reader = phase._ReaderBinding.capture(Owner(), "read")
        frames._register_binding(reader)
        armed[0] = True
        with self.assertRaises(PermissionError):
            frames._require_frame_contracts()
            frames._verify_binding(reader)
        self.assertEqual(effects, [])

    def test_changed_reader_ancestor_is_refused_before_metaclass_effects(self):
        effects, armed = [], [False]
        class Plain:
            pass
        class Lookup(type):
            def __getattribute__(cls, name):
                if armed[0]:
                    effects.append(name)
                return type.__getattribute__(cls, name)
        class Foreign(metaclass=Lookup):
            pass
        class Owner(Plain):
            def read(self):
                raise AssertionError("pure verifier executed a reader")
        reader = phase._ReaderBinding.capture(Owner(), "read")
        frames._register_binding(reader)
        original_bases = Owner.__bases__
        try:
            Owner.__bases__ = (Foreign,)
            self.assertIs(type(Owner), type)
            armed[0] = True
            with self.assertRaises(PermissionError):
                frames._require_frame_contracts()
                frames._verify_binding(reader)
            self.assertEqual(effects, [])
        finally:
            armed[0] = False
            Owner.__bases__ = original_bases


if __name__ == "__main__":
    unittest.main()

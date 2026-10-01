import unittest
from fishing.collection import CollectionTracker
from fishing.scene import manual_target


class CollectionTests(unittest.TestCase):
    def test_receipt_finishes_holding_immediately(self):
        self.assertEqual(CollectionTracker(0).update(True, False, .1), 'received')

    def test_idle_prompt_retries_key_without_recasting(self):
        tracker = CollectionTracker(0)
        self.assertIsNone(tracker.update(False, True, 1))
        self.assertEqual(tracker.update(False, True, 1.5), 'retry')
        self.assertIsNone(tracker.update(False, True, 2))
        self.assertEqual(tracker.update(False, True, 3), 'retry')

    def test_loading_bar_keeps_t_down(self):
        tracker = CollectionTracker(0)
        for t in range(1, 61):
            self.assertIsNone(tracker.update(False, True, t, loading=True))
        self.assertEqual(tracker.update(True, False, 61), 'received')

    def test_missing_prompt_never_confirms_receipt(self):
        tracker = CollectionTracker(0)
        for t in (1, 6, 30, 60):
            self.assertIsNone(tracker.update(False, False, t))

    def test_manual_point_scales_and_rejects_overlay(self):
        self.assertEqual(manual_target(1920, 1080, (.5, .4)), (960, 432))
        self.assertEqual(manual_target(960, 540, (.5, .4)), (480, 216))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, (.5, .4), (900, 400, 1000, 500))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, None)

import unittest
from fishing.scene import manual_target
from fishing.collection import Collection


class CollectionTests(unittest.TestCase):
    def test_failed_press_is_held_two_seconds_before_retry(self):
        c = Collection(0)
        self.assertEqual(c.update(0, True, False, False), 'holding')
        self.assertEqual(c.update(1.99, True, False, False), 'holding')
        self.assertTrue(c.held)
        self.assertEqual(c.update(2, True, False, False), 'retry')
        self.assertFalse(c.held)
        c.update(2.05, True, False, False)
        self.assertFalse(c.held)
        c.update(2.11, True, False, False)
        self.assertTrue(c.held)
        self.assertEqual(c.update(2.9, True, True, False), 'holding')
        self.assertEqual(c.update(3.2, True, True, False), 'holding')

    def test_three_failed_t_attempts_and_missing_prompt_mean_empty_cast(self):
        c = Collection(0)
        self.assertEqual(c.update(0, True, False, False), 'holding')
        self.assertEqual(c.update(2, True, False, False), 'retry')
        self.assertEqual(c.attempts, 1)
        c.update(2.11, True, False, False)
        self.assertEqual(c.update(4.11, True, False, False), 'retry')
        self.assertEqual(c.attempts, 2)
        c.update(4.22, True, False, False)
        self.assertEqual(c.update(6.22, False, False, False), 'empty')
        self.assertEqual(c.attempts, 3)

    def test_three_t_attempts_do_not_classify_still_visible_prompt_as_empty(self):
        c = Collection(0)
        c.update(0, True, False, False)
        c.update(2, True, False, False)
        c.update(2.11, True, False, False)
        c.update(4.11, True, False, False)
        c.update(4.22, True, False, False)
        self.assertEqual(c.update(6.22, True, False, False), 'retry')

    def test_loading_and_disappearing_prompt_do_not_interrupt_hold(self):
        c = Collection(0)
        c.update(0, True, False, False)
        c.update(.2, True, True, False)
        for t in (1, 2, 6, 10):
            self.assertEqual(c.update(t, False, False, False), 'holding')
            self.assertTrue(c.held)
        self.assertEqual(c.update(11, False, False, True), 'received')
        self.assertFalse(c.held)

    def test_return_to_idle_diamond_requires_two_seconds_before_retry(self):
        c = Collection(0)
        c.update(0, True, False, False)
        c.update(.2, True, True, False)
        c.update(.4, False, False, False)
        c.update(.8, True, False, False)
        self.assertEqual(c.update(2.79, True, False, False), 'holding')
        self.assertEqual(c.update(2.81, True, False, False), 'retry')

    def test_empty_cast_restarts_only_if_no_catch_was_seen(self):
        c = Collection(0)
        self.assertEqual(c.update(5.9, False, False, False), 'waiting')
        self.assertEqual(c.update(6, False, False, False), 'empty')
        c = Collection(0)
        c.update(1, True, False, False)
        c.update(2, False, False, False)
        self.assertNotEqual(c.update(20, False, False, False), 'empty')

    def test_pause_does_not_count_as_empty_return_time(self):
        c = Collection(0)
        c.pause(20)
        self.assertEqual(c.update(25, False, False, False), 'waiting')
        self.assertEqual(c.update(26, False, False, False), 'empty')

    def test_manual_point_scales_and_rejects_overlay(self):
        self.assertEqual(manual_target(1920, 1080, (.5, .4)), (960, 432))
        self.assertEqual(manual_target(960, 540, (.5, .4)), (480, 216))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, (.5, .4), (900, 400, 1000, 500))
        with self.assertRaises(ValueError):
            manual_target(1920, 1080, None)

class ImmediateLoadingTests(unittest.TestCase):
    def test_loading_seen_on_initial_press_is_latched(self):
        c = Collection(0)
        self.assertEqual(c.update(0, True, True, False), 'holding')
        self.assertTrue(c.loading)
        self.assertEqual(c.update(10, True, False, False), 'holding')

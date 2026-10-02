import unittest
from fishing.stats import SessionStats, duration


class StatsTests(unittest.TestCase):
    def test_background_name_resolution_preserves_confirmed_total(self):
        stats = SessionStats()
        stats.record('Sin identificar')
        stats.record('Sin identificar')
        stats.rename_unknown('Chatarra')
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.snapshot()[1], {'Sin identificar': 1, 'Chatarra': 1})
        stats.rename_unknown('Pez azul')
        self.assertEqual(stats.total, 2)
        self.assertNotIn('Sin identificar', stats.snapshot()[1])

    def test_pauses_and_reactivation_keep_totals_without_idle_time(self):
        stats = SessionStats()
        stats.tick(0, True)
        stats.record('Pez dorado')
        stats.tick(10, False)
        stats.tick(100, True)
        stats.record('Sin identificar')
        stats.tick(105, False)
        seconds, items = stats.snapshot()
        self.assertEqual(seconds, 15)
        self.assertEqual(items, {'Pez dorado': 1, 'Sin identificar': 1})
        self.assertEqual(duration(3661), '01:01:01')

    def test_snapshot_does_not_change_when_next_catch_is_recorded(self):
        stats = SessionStats()
        snapshot = stats.snapshot()
        stats.record('Hilo de seda')
        self.assertEqual(snapshot, (0, {}))

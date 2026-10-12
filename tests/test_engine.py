import unittest
from engine import simulate, analyze


class EngineTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(simulate(), simulate())
        self.assertNotEqual(simulate(1), simulate(2))

    def test_no_future_leakage(self):
        events = simulate()
        self.assertEqual(analyze(events, 1000), analyze([e for e in events if e['second'] <= 1000], 1000))

    def test_evidence_is_visible(self):
        events = simulate()
        for second in range(0, 5401, 60):
            state = analyze(events, second)
            ids = {e['id'] for e in state['events']}
            for insight in state['insights']:
                self.assertTrue(set(insight['evidence']) <= ids)

    def test_insufficient_data(self):
        self.assertEqual(analyze([], 0)['insights'], [])

    def test_designed_pattern_detected(self):
        insights = analyze(simulate(), 3900)['insights']
        self.assertTrue(any(i['key'] == 'right_route' for i in insights))
        self.assertTrue(all(i['confidence'] in ('medium', 'high') for i in insights))

    def test_every_insight_is_explainable(self):
        for second in (1860, 3900, 4800):
            for insight in analyze(simulate(), second)['insights']:
                self.assertTrue(insight['explanation'])
                self.assertTrue(insight['limitation'])
                self.assertTrue(insight['metric'])

    def test_coordinates_are_normalized(self):
        for event in simulate():
            for field in ('x', 'y', 'end_x', 'end_y'):
                self.assertGreaterEqual(event[field], 0)
                self.assertLessEqual(event[field], 100)


if __name__ == '__main__':
    unittest.main()

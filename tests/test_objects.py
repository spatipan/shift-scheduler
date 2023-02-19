import unittest
from datetime import datetime
from ..src.objects.timeinterval import TimeInterval, TimeIntervals
import plotly.express as px


class TestTimeInterval(unittest.TestCase):

    def test_constructor(self):
        ti = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        self.assertEqual(ti.start_time, datetime(2022, 1, 1, 0))
        self.assertEqual(ti.end_time, datetime(2022, 1, 1, 1))

    def test_duration(self):
        ti = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        self.assertEqual(ti.duration().total_seconds(), 3600)
        # ti2 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 2, 0))
        # self.assertEqual(ti2.duration(), 86400)

    def test_overlap(self):
        ti1 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        ti2 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        self.assertTrue(ti1.overlap(ti2))
        ti3 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 0, 30))
        self.assertTrue(ti1.overlap(ti3))
        ti4 = TimeInterval(datetime(2022, 1, 1, 1), datetime(2022, 1, 1, 2))
        self.assertFalse(ti1.overlap(ti4))
    
    def test_contains(self):
        ti1 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        ti2 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))
        self.assertTrue(ti1.contains(ti2))
        ti3 = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 0, 30))
        self.assertTrue(ti1.contains(ti3))
        ti4 = TimeInterval(datetime(2022, 1, 1, 0, 30), datetime(2022, 1, 1, 2))
        self.assertFalse(ti1.contains(ti4))


class TestTimeIntervals(unittest.TestCase):
    
        def test_constructor(self):
            intervals = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1)),
                                    TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            self.assertEqual(len(intervals.intervals), 2)
            self.assertEqual(intervals.intervals[0].start_time, datetime(2022, 1, 1, 0))
            self.assertEqual(intervals.intervals[0].end_time, datetime(2022, 1, 1, 1))
            self.assertEqual(intervals.intervals[1].start_time, datetime(2022, 1, 1, 2))
            self.assertEqual(intervals.intervals[1].end_time, datetime(2022, 1, 1, 3))
    
        def test_duration(self):
            intervals = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1)),
                                    TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            self.assertEqual(intervals.duration(), 7200)
    
        def test_overlap(self):
            intervals1 = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1)),
                                        TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            intervals2 = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 1, 30), datetime(2022, 1, 1, 2, 30)),
                                        TimeInterval(datetime(2022, 1, 1, 3), datetime(2022, 1, 1, 4))])
            self.assertTrue(intervals1.overlap(intervals2))
            intervals3 = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 1), datetime(2022, 1, 1, 2)),
                                        TimeInterval(datetime(2022, 1, 1, 3), datetime(2022, 1, 1, 4))])
            self.assertFalse(intervals1.overlap(intervals3))

        def test_contains(self, interval = TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1))):
            intervals1 = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1)),
                                        TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            self.assertTrue(intervals1.contains(interval))
            intervals2 = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0, 30), datetime(2022, 1, 1, 1, 30)),
                                        TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            self.assertFalse(intervals2.contains(interval))

        def test_visualize_gantt(self):
            intervals = TimeIntervals([TimeInterval(datetime(2022, 1, 1, 0), datetime(2022, 1, 1, 1)),
                                    TimeInterval(datetime(2022, 1, 1, 2), datetime(2022, 1, 1, 3))])
            intervals.visualize_gantt()


# Run the unit tests
unittest.main(argv=[''], verbosity=2, exit=False)


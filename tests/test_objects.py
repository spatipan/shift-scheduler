import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime
from src.objects.timeinterval import *
from src.objects.employee import *
from src.objects.shift import *
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

class TestShift(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime(2023, 2, 19, 8, 0)
        self.end_time = datetime(2023, 2, 19, 16, 0)
        self.interval = TimeInterval(self.start_time, self.end_time)
        self.shift = Shift(self.interval, min_employees=1, max_employees=2, shift_name='Day Shift', shift_type='Normal', workload_coefficient=1)
        self.employee1 = Employee('John', 'Doe')
        self.employee2 = Employee('Jane', 'Doe')

    def test_add_assigned_employee(self):
        self.shift.add_assigned_employee(self.employee1)
        self.assertEqual(self.shift.num_assigned_employees, 1)

    def test_add_assigned_employee_full_shift(self):
        self.shift.add_assigned_employee(self.employee1)
        self.shift.add_assigned_employee(self.employee2)
        with self.assertRaises(Exception):
            self.shift.add_assigned_employee(Employee('Foo', 'Bar'))

    def test_add_assigned_employee_duplicate(self):
        self.shift.add_assigned_employee(self.employee1)
        with self.assertRaises(Exception):
            self.shift.add_assigned_employee(self.employee1)

    def test_add_assigned_employees(self):
        self.shift.add_assigned_employees([self.employee1, self.employee2])
        self.assertEqual(self.shift.num_assigned_employees, 2)

    def test_add_assigned_employees_full_shift(self):
        self.shift.add_assigned_employee(self.employee1)
        with self.assertRaises(Exception):
            self.shift.add_assigned_employees([self.employee2, Employee('Foo', 'Bar')])

    def test_remove_assigned_employee(self):
        self.shift.add_assigned_employee(self.employee1)
        self.shift.remove_assigned_employee(self.employee1)
        self.assertEqual(self.shift.num_assigned_employees, 0)

    def test_remove_assigned_employee_not_assigned(self):
        with self.assertRaises(Exception):
            self.shift.remove_assigned_employee(self.employee1)

    def test_reset_employees(self):
        self.shift.add_assigned_employee(self.employee1)
        self.shift.add_assigned_employee(self.employee2)
        self.shift.reset_employees()
        self.assertEqual(self.shift.num_assigned_employees, 0)

    def test_change_shift_type(self):
        self.shift.change_shift_type('Night')
        self.assertEqual(self.shift.shift_type, 'Night')
    
    def test_change_workload_coefficient(self):
        self.shift.change_workload_coefficient(2)
        self.assertEqual(self.shift.workload_coefficient, 2)

    def test_change_min_employees(self):
        self.shift.change_min_employees(2)
        self.assertEqual(self.shift.min_employees, 2)

    def test_change_max_employees(self):
        self.shift.change_max_employees(3)
        self.assertEqual(self.shift.max_employees, 3)

    def test_change_shift_name(self):
        self.shift.change_shift_name('Night Shift')
        self.assertEqual(self.shift.shift_name, 'Night Shift')

    def test_change_interval(self):
        start_time = datetime(2023, 2, 19, 16, 0)
        end_time = datetime(2023, 2, 19, 23, 0)
        interval = TimeInterval(start_time, end_time)
        self.shift.change_interval(interval)
        self.assertEqual(self.shift.interval, interval)



# Run the unit tests

def run_tests():
    print("Running unit tests")
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()